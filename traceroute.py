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
        """
        print("'{}'".format(" ".join(self._cmd)))
        proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE)

        def read_traceroute_line():
            return proc.stdout.readline().decode().strip()

        self._result_timestamp = str(datetime.datetime.now())
        start = time.time()

        self._description = read_traceroute_line()
        print(self._description)

        while True:
            line = read_traceroute_line()

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

        result = {"number": int(words[0])}

        ip_index = 1
        while ip_index < len(words) and words[ip_index] == "*":
            expected_tries -= 1
            ip_index += 1

        if ip_index != len(words):
            result["ip_address"] = words[ip_index]

        if ip_index + expected_tries < len(words) - 1:
            result["hostname"] = words[ip_index+1].strip("()")

        tries = []
        for i in range(len(words)-expected_tries, len(words)):
            if words[i] != "*":
                tries.append(float(words[i].replace("ms", "")))

        result["results"] = tries

        print("DEBUG", result)
        self._result.append(result)

    def to_json(self):
        """Converts the class to json along with all data

        Returns:
            dictionary
        """
        if not self._result:
            return {
                        "cmd": " ".join(self._cmd),
                        "data": "No data"
                    }

        return {
                    "cmd": " ".join(self._cmd),
                    "description": self._description,
                    "timestamp": self._result_timestamp,
                    "time_taken_in_secs": self._seconds_taken,
                    "data":self._result
                }

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
