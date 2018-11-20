#!/usr/bin/env python3

import argparse
import datetime
import enum
import json
import subprocess
import time


class TracerouteVersion(enum.Enum):
    """Enum of supported traceroute versions, taken from `traceroute --version`
    """
    MODERN = "Modern traceroute for Linux, version 2.1.0"
    INETUTILS = "traceroute (GNU inetutils) 1.9.4"

def parse_line(version, line, expected_tries):
    """Parses a line printed by the traceroute program

    Args:
        version (TracerouteVersion)
        line (str): line printed by traceroute
        expected_tries (int): number of probes expected to be returned

    Returns:
        dict

    Raises:
        ValueError: invalid TracerouteVersion
        RuntimeError: unexpected input
    """
    words = [word.strip() for word in line.split(" ") if word.strip()]

    result = {
                "index": int(words[0]),
                "results": []
            }

    def is_ipv4_format(word):
        if word.count(".") != 3:
            return False
        try:
            for num in word.split("."):
                if int(num) < 0 or int(num) >= 256:
                    return False
        except ValueError:
            return False
        return True

    wrapped_by_brackets = lambda word: word[0] == "(" and word[-1] == ")"

    def is_float(word):
        try:
            float(word)
        except ValueError:
            return False
        return True

    if version == TracerouteVersion.INETUTILS:
        is_ipv4 = is_ipv4_format
        is_hostname = wrapped_by_brackets
        is_time = lambda x: is_float(x[:-2]) if x[-2:] == "ms" else False
    elif version == TracerouteVersion.MODERN:
        is_ipv4 = lambda x: wrapped_by_brackets(x) and is_ipv4_format(x[1:-1])
        is_time = is_float
        is_hostname = lambda word: word != "ms"
    else:
        raise ValueError("Invalid TracerouteVersion enum")

    for word in words[1:]:
        if word == "*":
            expected_tries -= 1
        elif is_ipv4(word):
            if "ip_address" not in result:
                result["ip_address"] = []
            if word not in result["ip_address"]:
                result["ip_address"].append(word.strip("()"))
        elif is_time(word):
            result["results"].append(float(word.replace("ms", "")))
            expected_tries -= 1
        elif is_hostname(word):
            result["hostname"] = word.strip("()")

    if "ip_address" in result and "hostname" in result:
        if len(result["ip_address"]) > 1:
            # Removing hostname information - unfortunately, a change in the
            # stored json format and a refactor of view-results is required to
            # maintain all information
            result.pop("hostname")
        elif result["hostname"] in result["ip_address"]:
            result.pop("hostname")

    if expected_tries != 0:
        raise RuntimeError("Unexpected behaviour - invalid input")

    return result

class TracerouteResult:
    """Object stores the result of the traceroute program
    """

    def __init__(self, tr_ver, host, first_hop=None, gateways=None, icmp=False,
            max_hop=64, connection_type="udp", port=33434, tries=3,
            resolve_hostnames=False, type_of_service=None, wait=3,
            output_file=None):
        """Initialises the object to call the traceroute program

        Note, if traceroute version is 2.1.0, resolve_hostnames is not used
        since it is default behaviour that hostnames are resolved.

        Args:
            tr_ver (TracerouteVersion): traceroute version enum
            host (str): hostname to send traceroute to
            first_hop (int): initial hop distance, that is the time-to-live
            gateways (str): list of gateways separated by spaces for loose
                    source routing
            icmp (bool): use ICMP ECHO as probe
            max_hop (int): maximal hop count
            connection_type (str): (icmp or udp) for traceroute operations
            port (int): destination port
            tries (int): number probe packets per hop
            resolve_hostnames (bool): resolve hostnames
            type_of_service (int): set type of service (TOS)
            wait (int): number of seconds to wait for response
            output_file (str): Name of file to store output
        """
        self._tr_ver = tr_ver
        self._cmd = ["traceroute"]

        if first_hop:
            self._cmd.append("-f")
            self._cmd.append(str(first_hop))

        if gateways:
            self._cmd.append("-g")
            self._cmd.append(" ".join(gateways))

        if icmp:
            self._cmd.append("-I")

        self._cmd.append("-m")
        self._cmd.append(str(max_hop))

        if tr_ver == TracerouteVersion.INETUTILS:
            self._cmd.append("-M")
            self._cmd.append(connection_type)
        elif tr_ver == TracerouteVersion.MODERN:
            self._cmd.append("--" + connection_type)

        self._cmd.append("-p")
        self._cmd.append(str(port))

        self._cmd.append("-q")
        self._cmd.append(str(tries))

        if tr_ver == TracerouteVersion.INETUTILS:
            if resolve_hostnames:
                self._cmd.append("--resolve-hostnames")

        if type_of_service:
            self._cmd.append("-t")
            self._cmd.append(str(type_of_service))

        self._cmd.append("-w")
        self._cmd.append(str(wait))

        self._cmd.append(host)

        self._host = host.strip()
        if output_file:
            self._output_file = output_file
        else:
            self._output_file = host + "-output.json"

        self._description = ""
        self._result = []
        self._result_timestamp = ""
        self._seconds_taken = 0

        self._number_of_tries = tries

    def run_traceroute_program(self):
        """Runs the traceroute program and stores the result

        Raises:
            ValueError: when there are incorrect arguments
            RuntimeError: when host cannot be found
        """
        print("'{}'".format(" ".join(self._cmd)))
        proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)

        def read_traceroute_line():
            return proc.stdout.readline().decode().strip()

        self._result_timestamp = str(datetime.datetime.now())
        start = time.time()

        self._description = read_traceroute_line()
        print(self._description)

        if "name or service not known" in self._description.lower():
            raise RuntimeError("Name or Service is not known")

        while True:
            line = read_traceroute_line()

            if "invalid argument" in line.lower():
                raise ValueError("Invalid Argument")


            if not line:
                break

            print(line)
            self._parse_traceroute_line(line)

        self._seconds_taken = time.time() - start

    def _parse_traceroute_line(self, line):
        """Parses traceroute line and appends to result

        Args:
            line (str): line from traceroute program

        Raises:
            RuntimeError: on unexpected behaviour
        """
        result = parse_line(self._tr_ver, line, self._number_of_tries)
        self._result.append(result)

    def to_json(self):
        """Converts the class to json along with all data

        Returns:
            dictionary
        """
        result = {"cmd": " ".join(self._cmd)}
        if not self._result:
            result["data"] = "No data"
            result["timestamp"] = str(datetime.datetime.now())
        else:
            result["description"] = self._description,
            result["timestamp"] = self._result_timestamp,
            result["time_taken_in_secs"] = self._seconds_taken,
            result["data"] = self._result
        return result

    def save_to_file(self):
        """Saves the result in a file
        """
        try:
            with open(self._output_file, "r") as f:
                prev_data = json.load(f)
        except FileNotFoundError:
            prev_data = {}

        if self._host not in prev_data:
            prev_data[self._host] = []
        prev_data[self._host].append(self.to_json())
        with open(self._output_file, "w") as f:
            json.dump(prev_data, f, sort_keys=True, indent=4)

def parse_args(traceroute_version):
    """Sets and parses the command line arguments

    Args:
        traceroute_version (TracerouteVersion): used to determine cli

    Returns:
        Namespace object
    """
    parser = argparse.ArgumentParser(description="Wrapper for traceroute")

    parser.add_argument("--first-hop", type=int,
            help="Set initial hop distance, that is the time-to-live")
    parser.add_argument("--gateways", type=str,
            help="List of gateways for loose source routing")
    parser.add_argument("--icmp", default=False, action="store_true",
             help="Use ICMP ECHO as probe")
    parser.add_argument("--max-hop", type=int, default=64,
            help="Set maximal hop count")
    parser.add_argument("--connection-type", type=str, choices=["icmp", "udp"],
            default="udp",  help="Method to use for traceroute operations")
    parser.add_argument("--port", type=int, default=33434, help="Port to use")
    parser.add_argument("--tries", type=int, default=3,
            help="Number of probe packets per hop")
    if traceroute_version == TracerouteVersion.INETUTILS:
        parser.add_argument("--resolve-hostnames", default=False,
                action="store_true", help="Resolve hostnames")
    parser.add_argument("--type-of-service", type=str,
            help="Set type of service (TOS)")
    parser.add_argument("--wait", type=int, default=3,
            help="Number of seconds to wait for response")

    parser.add_argument("host", type=str, help="Host to trace route to")
    
    parser.add_argument("output_file", type=str, default="",
            help="File to store resuilts in")
    return parser.parse_args()

def get_traceroute_version():
    """Returns the installed traceroute version

    Returns:
        TracerouteVersion or None

    Raises:
        ImportError
    """
    cmd = ["traceroute", "--version"]
    
    try: 
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
        return TracerouteVersion(proc.stdout.readline().decode().strip())
    except (ValueError, FileNotFoundError) as ex:
        raise ImportError("Cannot find supported traceroute program") from ex

def main(args, tr_ver):
    tr_result = TracerouteResult(tr_ver, **vars(args))
    tr_result.run_traceroute_program()
    tr_result.save_to_file()

if __name__ == "__main__":
    traceroute_version = get_traceroute_version()
    main(parse_args(traceroute_version), traceroute_version)
