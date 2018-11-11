#!/usr/bin/env python3

import argparse
import json
import statistics

import graphviz
import matplotlib.pyplot as plt
import numpy as np
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
                table.add_row([host, len(hops), average, best, worst, stdev])
            else:
                table.add_row([host, len(hops)] + ["-"] * 4)

    else:
        table = prettytable.PrettyTable(["", "Host", "Rcvd",
                "Average (ms)", "Best (ms)", "Worst (ms)", "StDev (ms)"],
                hrules=prettytable.ALL)
        table.align[""] = "l"
        table.align["Host"] = "l"

        max_hops = 0
        for entry in data[hostname]:
            if type(entry["data"]) is list:
                max_hops = max(max_hops, len(entry["data"]))

        hops_hosts = [set() for i in range(max_hops)]
        hops_ips = [set() for i in range(max_hops)]
        hops = [[] for i in range(max_hops)]
        for entry in data[hostname]:
            if type(entry["data"]) is list:
                for i, hop in enumerate(entry["data"]):
                    if "ip_address" in hop:
                        for ip in hop["ip_address"]:
                            name = ip
                            if "hostname" in hop:
                                name += " (" + hop["hostname"] + ")"
                                if ip in hops_hosts[i]:
                                    hops_hosts[i].remove(ip)
                            if ip not in hops_ips[i]:
                                hops_hosts[i].add(name)
                            hops_ips[i].add(ip)
                    hops[i] += hop["results"]

        if max_hops == 0:
            print("No data")
            return

        for i in range(len(hops)):
            if len(hops_hosts[i]) == 0:
                hops_hosts[i].add("???")
            if hops[i]:
                table.add_row([i+1, "\n".join(hops_hosts[i]), len(hops[i]),
                        round(sum(hops[i]) / len(hops[i]), 2),
                        round(min(hops[i]), 2), round(max(hops[i]), 2),
                        round(statistics.stdev(hops[i]), 2)])
            else:
                table.add_row([i+1, "\n".join(hops_hosts[i])] + ["-"] * 5)
    print(table)

def graph_bar_chart(data, hostname=None):
    """Displays a bar chart of the data

    Args:
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    if hostname is None:
        hostnames = list(data.keys())
        hostnames.sort()

        max_hops = 0
        max_average = 0
        min_average = 0
        hop_averages = []
        for host in hostnames:
            hops = []
            for entry in data[host]:
                if type(entry["data"]) is list:
                    for i in range(len(entry["data"])):
                        if len(hops) == i:
                            hops.append([])
                        hops[i] += entry["data"][i]["results"]
            hop_averages.append([])
            for hop in hops:
                if hop:
                    hop_averages[-1].append(round(sum(hop) / len(hop), 1))
                else:
                    hop_averages[-1].append(-5.0)
                max_average = max(max_average, hop_averages[-1][-1])
                if hop_averages[-1][-1] != -5:
                    min_average = min(min_average, hop_averages[-1][-1])
            max_hops = max(max_hops, len(hops))

        for i in range(len(hop_averages)):
            while len(hop_averages[i]) < max_hops:
                hop_averages[i].append(-10.0)

        fig, ax = plt.subplots()

        # Colourmap
        cmap = plt.get_cmap("inferno_r")
        cmap.set_bad(color="lightblue")

        # Heatmap
        data = np.array(hop_averages)

        change_miss_f = lambda x: int(max_average) + 6 if x == -5 else x
        change_miss_v = np.vectorize(change_miss_f)
        data = change_miss_v(data)

        val_f = lambda x: min(x, plt.Locator.MAXTICKS - 5)
        val_v = np.vectorize(val_f)
        im = ax.imshow(np.ma.masked_equal(val_v(data), val_f(-10)), cmap=cmap)

        if min_average + 1 < max_average:
            min_average += 1

        # Colourbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_ticks([int(max_average) + 6, val_f(max_average),
                val_f(min_average)])
        cbar.set_ticklabels(["No data", ">=" + str(val_f(max_average)),
                min_average])

        cbar.ax.set_ylabel("Average hop time (ms)", rotation=-90,
                va="bottom")

        ax.set_xticks(np.arange(max_hops))
        ax.set_yticks(np.arange(len(hostnames)))

        ax.set_xticklabels(list(range(1, max_hops+1)))
        ax.set_yticklabels(hostnames)

        ax.set_title("Traceroute Information")

    else:
        hops_hosts = []
        hops = []
        for entry in data[hostname]:
            if type(entry["data"]) is list:
                for i in range(len(entry["data"])):
                    if len(hops) == i:
                       hops.append([])
                       hops_hosts.append(set())

                    if "ip_address" in entry["data"][i]:
                        for name in entry["data"][i]["ip_address"]:
                            hops_hosts[i].add(name)
                    hops[i] += entry["data"][i]["results"]
        if not hops:
            print("No data")
            return
        hops_averages = [round(sum(hs) / len(hs), 2)\
                if hs else 0 for hs in hops]
        hosts = [", ".join(host) if host else "???" for host in hops_hosts]
        msg = "Multiple Entries"
        hosts = [msg if len(h) > len(msg) and "," in h else h for h in hosts]

        fig, ax = plt.subplots()

        num_hops = len(hops)

        ax.barh(np.arange(num_hops), np.array(hops_averages), align="center")
        ax.set_yticks(np.arange(num_hops))
        ax.set_yticklabels(hosts)

        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel("Average Time (ms)")
        ax.set_title("Traceroute Information to {}".format(hostname))

    fig.tight_layout()
    plt.show()

def graph_map(data, hostname=None):
    """Displays a grpah visualisation of data

    Args:
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    if hostname is None:
        hostnames = list(data.keys())
        hostnames.sort()
    else:
        hostnames = [hostname]

    graph = graphviz.Digraph(comment="Traceroute Information",
            filename="map-drawing.gv")
    graph.node_attr.update(color="lightblue2", style="filled")

    edges = {}
    ip_to_hosts = {}
    temp_count = 1
    for host in hostnames:
        for entry in data[host]:
            if type(entry["data"]) is list:
                if "ip_address" not in entry["data"][0]:
                    entry["data"][0]["ip_address"] = {f"??? ({temp_count})"}
                    temp_count += 1

                for i in range(1, len(entry["data"])):
                    if "hostname" in entry["data"][i-1]:
                        if len(entry["data"][i-1]["ip_address"]) == 1:
                            ip = next(iter(entry["data"][i-1]["ip_address"]))
                            ip_to_hosts[ip] = entry["data"][i-1]["hostname"]

                    for previous in entry["data"][i-1]["ip_address"]:
                        if previous not in edges:
                            edges[previous] = (set(), None)

                        if "ip_address" not in entry["data"][i]:
                            if edges[previous][1] is None:
                                new_node = f"??? ({temp_count})"
                                edges[previous] = (edges[previous][0], new_node)
                                temp_count += 1
                            else:
                                new_node = edges[previous][1]
                            entry["data"][i]["ip_address"] = {new_node}

                        currents = entry["data"][i]["ip_address"]

                        if i == len(entry["data"]) - 1:
                            if len(currents) == 1:
                                if "hostname" in entry["data"][i]:
                                    ip = next(iter(currents))
                                    host_name = entry["data"][i]["hostname"]
                                    ip_to_hosts[ip] = host_name

                            temp_currents = set()
                            for current in currents:
                                if f"<{host}>" not in current:
                                    temp_currents.add(current + f"\n<{host}>")
                            currents = temp_currents

                        for current in currents:
                            if current not in edges[previous][0]:
                                edges[previous][0].add(current)
                                graph.edge(previous, current)


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

    for i, node in enumerate(graph.body):
        found_ips = set()
        for word in node.split("\""):
            if is_ipv4(word):
                if word in ip_to_hosts:
                    found_ips.add(word)
        for ip in found_ips:
            graph.body[i] = graph.body[i].replace(f"\"{ip}\"",
                    f"\"{ip}\n{ip_to_hosts[ip]}\"")

    graph.view(cleanup=True)


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
