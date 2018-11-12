#!/usr/bin/env python3

import argparse
import itertools
import json
import statistics

import graphviz
import matplotlib.pyplot as plt
import numpy as np
import prettytable

class TracerouteData:
    """Encapsulates traceroute data
    """

    def __init__(self, data):
        """Initialises the object

        Args:
            data (dict): the traceroute data
        """
        self._data = data
        self._hostnames = list(self._data)
        self._hostnames.sort()

    def get_hostnames(self):
        """Returns a list of hostnames

        Returns:
            list[str]
        """
        return self._hostnames

    def get_number_empty_entries(self, hostname):
        """Count the number of empty entries given a hostname

        Args:
            hostname (str)

        Returrns:
            int
        """
        empty_entries = 0
        for entry in self._data[hostname]:
            if type(entry["data"]) is not list:
                empty_entries += 1
        return empty_entries

    def get_number_all_empty_entries(self):
        """Counts the number of empty entries in all the data

        Returns:
            int
        """
        total = 0
        for hostname in self.get_hostnames():
            total += self.get_number_empty_entries(hostname)
        return total

    def get_number_entries(self, hostname):
        """Counts the number of non-empty entries for a hostname

        Args:
            hostname (str)

        Returns:
            int
        """
        return len(self._data[hostname]) -\
                self.get_number_empty_entries(hostname)

    def get_number_all_entries(self):
        """Counts the number of non-empty entries in all the data

        Returns:
            int
        """
        total = 0
        for hostname in self.get_hostnames():
            total += self.get_number_entries(hostname)
        return total

    def get_hostnames_info(self):
        """Returns information about hostnames

        Yield:
            tuple: 3-tuple of format
            (hostname, number of non-empty entries, number of empty entries)
        """
        for host in self.get_hostnames():
            yield (
                        host,
                        self.get_number_entries(host),
                        self.get_number_empty_entries(host)
                    )

    def get_entries(self, hostname):
        """Generator of non-empty entries given a hostname

        Args:
            hostname (str)

        Yields:
            dict
        """
        for entry in self._data[hostname]:
            if type(entry["data"]) is list:
                yield entry

    def get_hostname_entry_delays(self, hostname):
        """Returns the delay times given a hostname

        Args:
            hostname (str)

        Returns:
            list[list[float]]: list of list of delay times in ms, grouped by
                    the router
        """
        result = []
        for entry in self.get_entries(hostname):
            for i in range(len(entry["data"])):
                if i == len(result):
                    result.append([])
                result[i] += entry["data"][i]["results"]
        return result

    def get_hostname_entry_hosts(self, hostname, with_hostnames=True):
        """Returns the hostnames visited by traceroute program

        Args:
            hostname (str)
            with_hostnames (bool): True if you wish to return both ip_address
                    and hostname, False if only ip_address is wanted

        Returns:
            list[list[str]]: list of list of hostnames, grouped by the router
        """
        result = []
        hostname_map = {}
        for entry in self.get_entries(hostname):
            for i in range(len(entry["data"])):
                if i == len(result):
                    result.append(set())
                if "ip_address" in entry["data"][i]:
                    for ip in entry["data"][i]["ip_address"]:
                        result[i].add(ip)
                        if with_hostnames and "hostname" in entry["data"][i]:
                            hostname_map[ip] = entry["data"][i]["hostname"]

        for i in range(len(result)):
            ip_matches = set(hostname_map) & result[i]
            for ip in ip_matches:
                result[i].remove(ip)
                result[i].add("{} ({})".format(ip, hostname_map[ip]))
            if len(result[i]) == 0:
                result[i].add("???")

        return result

def graph_table(data, hostname=None):
    """Generates a display with table

    Args:
        data (TracerouteData object)
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    def get_stats_from_list(nums):
        average = str(round(sum(nums) / len(nums), 2))
        best = str(round(min(nums), 2))
        worst = str(round(max(nums), 2))
        stdev = str(round(statistics.stdev(nums), 2))
        return [average, best, worst, stdev]

    if hostname is None:
        table = prettytable.PrettyTable(["Hostname Targets", "Rcvd",
                "Average (ms)", "Best (ms)", "Worst (ms)", "StDev (ms)"])
        table.align["Hostname Targets"] = "l"

        for hostname in data.get_hostnames():
            delays = data.get_hostname_entry_delays(hostname)
            delays = list(itertools.chain.from_iterable(delays))
            stats = get_stats_from_list(delays) if delays else ["-"] * 4
            table.add_row([hostname, len(delays)] + stats)
    else:
        table = prettytable.PrettyTable(["", "Host", "Rcvd",
                "Average (ms)", "Best (ms)", "Worst (ms)", "StDev (ms)"],
                hrules=prettytable.ALL)
        table.align[""] = "l"
        table.align["Host"] = "l"

        delays = data.get_hostname_entry_delays(hostname)

        if len(delays) == 0:
            print("No data")
            return

        v_hosts = data.get_hostname_entry_hosts(hostname)

        for i in range(len(delays)):
            stats = get_stats_from_list(delays[i]) if delays[i] else ["-"] * 4
            table.add_row([i+1, "\n".join(v_hosts[i]), len(delays[i])] + stats)
    print(table)

def graph_bar_chart(data, hostname=None):
    """Displays a bar chart of the data

    Args:
        data (TracerouteData object)
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    if hostname is None:
        hostnames = data.get_hostnames()
        max_hops = 0
        max_average = 0
        min_average = 0

        averages = []
        for hostname in hostnames:
            data.get_hostname_entry_delays(hostname)
            averages.append([])
            for delays in data.get_hostname_entry_delays(hostname):
                if delays:
                    averages[-1].append(round(sum(delays) / len(delays), 1))
                    min_average = min(min_average, averages[-1][-1])
                else:
                    averages[-1].append(-5)
                max_average = max(max_average, averages[-1][-1])
                max_hops = max(max_hops, len(averages[-1]))

        for i in range(len(averages)):
            while len(averages[i]) < max_hops:
                averages[i].append(-10)
        averages = np.array(averages)
        if min_average + 1 < max_average:
            min_average += 1

        fig, ax = plt.subplots()

        # Colourmap
        cmap = plt.get_cmap("inferno_r")
        cmap.set_bad(color="lightblue")

        # Heatmap
        change_miss_f = lambda x: int(max_average) + 6 if x == -5 else x
        change_miss_v = np.vectorize(change_miss_f)
        averages = change_miss_v(averages)

        val_f = lambda x: min(x, plt.Locator.MAXTICKS - 5)
        val_v = np.vectorize(val_f)
        im = ax.imshow(np.ma.masked_equal(val_v(averages), val_f(-10)),
                cmap=cmap)

        # Colourbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_ticks([int(max_average) + 6, val_f(max_average),
                val_f(min_average)])
        cbar.set_ticklabels(["No Data", ">=" + str(val_f(max_average)),
                min_average])

        cbar.ax.set_ylabel("Average Delay (ms)", rotation=-90, va="bottom")
        ax.set_title("Traceroute Information")

    else:
        delays = data.get_hostname_entry_delays(hostname)

        if len(delays) == 0:
            print("No data")
            return

        averages = [round(sum(d) / len(d), 2) if d else 0 for d in delays]

        hostnames = []
        for host in data.get_hostname_entry_hosts(hostname, False):
            host = ", ".join(host)
            if len(host) > len("Multiple Entries") and "," in host:
                host = "Multiple Entries"
            hostnames.append(host)

        fig, ax = plt.subplots()
        ax.barh(np.arange(len(hostnames)), np.array(averages), align="center")

        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel("Average Delay (ms)")
        ax.set_title("Traceroute Information to {}".format(hostname))

    ax.set_yticks(np.arange(len(hostnames)))
    ax.set_yticklabels(hostnames)

    fig.tight_layout()
    plt.show()

def graph_map(data, hostname=None):
    """Displays a grpah visualisation of data

    Args:
        data (TracerouteData object)
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    hostnames = data.get_hostnames() if hostname is None else [hostname]

    graph = graphviz.Digraph(comment="Traceroute Information",
            filename="map-drawing.gv")
    graph.node_attr.update(color="lightblue2", style="filled")

    edges = {}
    ip_to_hosts = {}
    temp_count = 1
    for host in hostnames:
        for entry in data.get_entries(host):
            if "ip_address" not in entry["data"][0]:
                entry["data"][0]["ip_address"] = {f"??? ({temp_count})"}
                temp_count += 1

            for i in range(1, len(entry["data"])):
                if "hostname" in entry["data"][i-1]:
                    for ip in entry["data"][i-1]["ip_address"]:
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
                        if "hostname" in entry["data"][i]:
                            name = entry["data"][i]["hostname"]
                            for ip in currents:
                                ip_to_hosts[ip] = name

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


def print_stats(data, hostname=None):
    """Prints the stats related to data

    Args:
        data (TracerouteData object)
        hostname (str): hostname to output data on, if None, summary of all
                data is printed
    """
    to_print = []
    if hostname is None:
        delays = []
        for hostname in data.get_hostnames():
            delays += data.get_hostname_entry_delays(hostname)

        to_print.append(("Number of hostnames", len(data.get_hostnames())))
        to_print.append(("Total number of entries",
                data.get_number_all_entries()))

        to_print.append(("Average number of hops per hostname",
                round(len(delays) / len(data.get_hostnames()), 2)))
    else:
        delays = data.get_hostname_entry_delays(hostname)

        to_print.append(("Number of entries",
                data.get_number_entries(hostname)))
        to_print.append(("Maximum number of hops", len(delays)))

    if not delays:
        print("No data")
        return

    delays = list(itertools.chain.from_iterable(delays))
    to_print.append(("Average delay", round(sum(delays) / len(delays), 2),
            "ms"))
    to_print.append(("Best time", round(min(delays), 2), "ms"))
    to_print.append(("Worst time", round(max(delays), 2), "ms"))
    to_print.append(("Standard deviation", round(statistics.stdev(delays), 2),
            "ms"))

    max_length = max(map(lambda x: len(x[0]), to_print)) + 1

    for line in to_print:
        print("{} {}{}".format((line[0] + ":").ljust(max_length),
                line[1], line[2] if len(line) > 2 else ""))

def print_general_info(data):
    """Prints general information about data

    Args:
        data (TracerouteData object)
    """
    print(" Information ".center(60, "="))
    print("Number of hostnames:", len(data.get_hostnames()))
    print("Number of entries:", data.get_number_all_entries())
    num_empty = data.get_number_all_empty_entries()
    if num_empty > 0:
        print("Number of empty entries:", num_empty)

def print_hostname_info(data):
    """Prints list of hostnames

    Args:
        data (TracerouteData object)
    """
    print(" Hostnames ".center(60, "="))
    max_length = max(map(len, data.get_hostnames()))
    for info in data.get_hostnames_info():
        print(info[0].ljust(max_length), "(", end="")
        print(info[1], "entries", end="")
        if info[2] > 0:
            print(",", info[2], "empty entries", end="")
        print(")")


def parse_args():
    """Sets and parses command line arguments

    Returns:
        Namespace object
    """
    parser = argparse.ArgumentParser(description="Visualises traceroute data")

    parser.add_argument("data_file", type=str,
            help="File with traceroute data")
    parser.add_argument("action", type=str, default="list",
            choices=["info", "hostnames", "stats", "table", "chart", "map"],
            help="Action to carry out on data")
    parser.add_argument("hostnames", type=str, help="Hostnames to visualise",
            nargs="*")

    return parser.parse_args()

def main(args):
    with open(args.data_file, "r") as f:
        data = TracerouteData(json.load(f))

    function_mappings = {
                "stats": print_stats,
                "chart": graph_bar_chart,
                "table": graph_table,
                "map": graph_map
            }

    if args.action == "info":
        print_general_info(data)
    elif args.action == "hostnames":
        print_hostname_info(data)
    else:
        if not args.hostnames:
            print(" Information Based On All Data ".center(60, "="))
            function_mappings[args.action](data)
        for hostname in args.hostnames:
            if hostname in data.get_hostnames():
                print(f" {hostname} ".center(60, "="))
                function_mappings[args.action](data, hostname)
            else:
                print("Error:", hostname, "not in data")

if __name__ == "__main__":
    main(parse_args())
