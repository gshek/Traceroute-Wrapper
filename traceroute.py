#!/usr/bin/env python3

import argparse
import datetime
import json
import subprocess
import time


class TracerouteResult:
    """Object stores the result of the traceroute program
    """

    def __init__(self, host, first_hop=None, gateways=None, icmp=False,
            max_hop=64, connection_type="udp", port=33434, tries=3,
            resolve_hostnames=False, type_of_service=None, wait=3,
            output_file=None):
        """Initialises the object to call the traceroute program

        Args:
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

        self._cmd.append("-M")
        self._cmd.append(connection_type)

        self._cmd.append("-p")
        self._cmd.append(str(port))

        self._cmd.append("-q")
        self._cmd.append(str(tries))

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
            ValueError: When there are incorrect arguments
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
        """
        words = [word.strip() for word in line.split(" ") if word.strip()]
        expected_tries = self._number_of_tries

        # Though about using regexes, but though this would be more readable

        def is_ipv4(word):
            allowed = {str(i) for i in range(10)}
            allowed.add(".")
            for c in word:
                if c not in allowed:
                    return False
            if word.count(".") != 3:
                return False
            for num in word.split("."):
                if int(num) >= 256:
                    return False
            return True

        def is_hostname(word):
            return word[0] == "(" and word[-1] == ")"

        def is_time(word):
            if word[-2:] != "ms":
                return False
            try:
                float(word[:-2])
            except ValueError:
                return False
            return True

        result = {
                    "index": int(words[0]),
                    "results": []
                }

        for word in words[1:]:
            if word == "*":
                expected_tries -= 1
            elif is_ipv4(word):
                if "ip_address" not in result:
                    result["ip_address"] = []
                if word not in result["ip_address"]:
                    result["ip_address"].append(word)
            elif is_hostname(word):
                result["hostname"] = word.strip("()")
            elif is_time(word):
                result["results"].append(float(word.replace("ms", "")))
                expected_tries -= 1

        if "ip_address" in result:
            if len(result["ip_address"]) > 1:
                # Unknown behaviour, so removing hostname information
                if "hostname" in result:
                    result.pop("hostname")
            elif result["hostname"] in result["ip_address"]:
                result.pop("hostname")

        if expected_tries != 0:
            raise "Unexpected behaviour - invalid input"

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

def parse_args():
    """Sets and parses the command line arguments

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

def main(args):
    tr_result = TracerouteResult(**vars(args))
    tr_result.run_traceroute_program()
    tr_result.save_to_file()

if __name__ == "__main__":
    main(parse_args())
