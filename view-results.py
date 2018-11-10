#!/usr/bin/env python3

import argparse
import json
import statistics

def graph_table(data, hostname=None):
    """Generates a display with table

    Args:
        TODO
    """
    # TODO
    pass

def graph_bar_chart(data, hostname=None):
    """TODO
    """
    # TODO
    pass

def graph_map(data, hostname=None):
    """TODO
    """
    # TODO
    pass

def graph_cool_visualisation(data, hostname=None):
    """TODO
    """
    # TODO
    pass

def show_stats(data, hostname=None):
    """Prints the stats related to data

    Args:
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    if hostname is None:
        num_hops = 0
        hops = []
        entries = 0
        for host in data:
            entries += len(data[host])
            for entry in data[host]:
                num_hops += len(entry["data"])
                if type(entry["data"]) is list:
                    for reading in entry["data"]:
                        hops += reading["results"]

        print("Number of hostnames:", len(data), end=", ")
        print("Total number of entries:", entries)

        print("Total number of hops:", num_hops, end=", ")
        print("Average number of hops per entry:", num_hops / entries)

        to_print = [
                    ("Average time per hop", sum(hops) / len(hops)),
                    ("Best time", min(hops)),
                    ("Worst time", max(hops)),
                    ("Standard deviation", statistics.stdev(hops))
                ]

        max_length = max(map(lambda x: len(x[0]), to_print))
        if hops:
            for line in to_print:
                print("{} {}ms".format((line[0] + ":").ljust(max_length),
                        line[1]))

def parse_args():
    """Sets and parses command line arguments

    Returns:
        Namespace object
    """
    parser = argparse.ArgumentParser(description="Visualises traceroute data")

    parser.add_argument("data_file", type=str,
            help="File with traceroute data")
    parser.add_argument("action", type=str, default="list",
            choices=["info", "hostnames", "stats", "chart", "table", "map"],
            help="Action to carry out on data")
    parser.add_argument("hostnames", type=str, help="Hostnames to visualise",
            nargs="*")

    return parser.parse_args()

def main(args):
    with open(args.data_file, "r") as f:
        data = json.load(f)

    function_mappings = {
                "stats": show_stats,
                "chart": graph_bar_chart,
                "table": graph_table,
                "map": graph_map
            }

    if args.action == "info":
        hostname_count = len(data)
        entries = 0
        empty_entries = 0
        for host in data:
            entries += len(data[host])
            for entry in data[host]:
                if type(entry["data"]) is not list:
                    empty_entries += 1
        print("Hostnames:", hostname_count)
        print(f"Total entries: {entries} (empty entries: {empty_entries})")

    elif args.action == "hostnames":
        hostnames = list(data.keys())
        hostnames.sort()
        max_length = max(map(len, hostnames))
        for host in hostnames:
            empty_entries = 0
            for entry in data[host]:
                if type(entry["data"]) is not list:
                    empty_entries += 1
            print(f"{host.ljust(max_length)}", end=" ")
            print(f"({len(data[host])} entries, {empty_entries} empty)")

    else:
        if not args.hostnames:
            function_mappings[args.action](data)
        for hostname in args.hostnames:
            function_mappings[args.action](data, hostname)

if __name__ == "__main__":
    main(parse_args())
