#!/usr/bin/env python3

import argparse
import json
import statistics

import prettytable

def graph_table(data, hostname=None):
    """Generates a display with table

    Args:
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """

    if hostname is None:
        hosts = list(data.keys())
        hosts.sort()

        table = prettytable.PrettyTable(["Hostname Targets", "Rcvd",
                "Average (ms)", "Best (ms)", "Worst (ms)", "StDev (ms)"])
        table.align["Hostname Targets"] = "l"
        for host in hosts:
            hops = []
            for entry in data[host]:
                if type(entry["data"]) is list:
                    for hop in entry["data"]:
                        hops += hop["results"]
            
            if hops:
                average = str(round(sum(hops) / len(hops), 2))
                best = str(round(min(hops), 2))
                worst = str(round(max(hops), 2))
                stdev = str(round(statistics.stdev(hops), 2))
            else:
                average = "-"
                best = "-"
                worst = "-"
                stdev = "-"

            table.add_row([host, len(hops), average, best, worst, stdev])

    else:
        table = prettytable.PrettyTable(["", "Hostname", "Rcvd",
                "Average (ms)", "Best (ms)", "Worst (ms)", "StDev (ms)"],
                hrules=prettytable.ALL)
        table.align[""] = "l"
        table.align["Hostname"] = "l"

        max_hops = 0
        for entry in data[hostname]:
            if type(entry["data"]) is list:
                max_hops = max(max_hops, len(entry["data"]))

        hops_hosts = [set() for i in range(max_hops)]
        hops = [[] for i in range(max_hops)]
        for entry in data[hostname]:
            if type(entry["data"]) is list:
                for i, hop in enumerate(entry["data"]):
                    name = ""
                    if "ip_address" in hop:
                        name = hop["ip_address"]
                    if "hostname" in hop:
                        name += " (" + hop["hostname"] + ")"
                    
                    if name != "":
                        hops_hosts[i].add(name)
                    hops[i] += hop["results"]

        if max_hops == 0:
            print("No data")
            return

        for i in range(len(hops)):
            if len(hops_hosts[i]) == 0:
                hops_hosts[i].add("?")
            if hops[i]:
                table.add_row([i+1, "\n".join(hops_hosts[i]), len(hops[i]),
                        round(sum(hops[i]) / len(hops[i]), 2),
                        round(min(hops[i]), 2), round(max(hops[i]), 2),
                        round(statistics.stdev(hops[i]), 2)])
            else:
                table.add_row([i+1, "\n".join(hops_hosts[i])] + ["-"] * 5)
    print(table)

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
    def get_host_entry_info(host):
        num_hops = 0
        hops = []
        for entry in data[host]:
            if type(entry["data"]) is list:
                num_hops += len(entry["data"])
                for reading in entry["data"]:
                    hops += reading["results"]
        return (num_hops, hops)

    if hostname is None:
        num_hops = 0
        hops = []
        entries = 0
        for host in data:
            entries += len(data[host])
            entry_info = get_host_entry_info(host)
            num_hops += entry_info[0]
            hops += entry_info[1]

        print("Number of hostnames:", len(data), end=", ")
        print("Total number of entries:", entries)
    else:
        num_hops, hops = get_host_entry_info(hostname)
        entries = len(data[hostname])
        print("Number of entries:", entries)

    print("Total number of hops:", num_hops, end=", ")
    print("Average number of hops per entry:", round(num_hops / entries, 2))

    if not hops:
        print("No hops data")
        return

    to_print = [
                ("Average time per hop", round(sum(hops) / len(hops), 2)),
                ("Best time", round(min(hops), 2)),
                ("Worst time", round(max(hops), 2)),
                ("Standard deviation", round(statistics.stdev(hops), 2))
            ]

    max_length = max(map(lambda x: len(x[0]), to_print)) + 1

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
        print(" Information ".center(60, "="))
        print("Hostnames:", hostname_count)
        print(f"Total entries: {entries} (empty entries: {empty_entries})")

    elif args.action == "hostnames":
        hostnames = list(data.keys())
        hostnames.sort()
        max_length = max(map(len, hostnames))
        print(" Hostnames ".center(60, "="))
        for host in hostnames:
            empty_entries = 0
            for entry in data[host]:
                if type(entry["data"]) is not list:
                    empty_entries += 1
            print(f"{host.ljust(max_length)}", end=" ")
            print(f"({len(data[host])} entries, {empty_entries} empty)")

    else:
        if not args.hostnames:
            print(" Information Based On All Data ".center(60, "="))
            function_mappings[args.action](data)
        for hostname in args.hostnames:
            if hostname in data:
                print(f" {hostname} ".center(60, "="))
                function_mappings[args.action](data, hostname)
            else:
                print("Error:", hostname, "not in data")

if __name__ == "__main__":
    main(parse_args())
