# TracerouteWrapper

## Traceroute Version
```
traceroute (GNU inetutils) 1.9.4
Copyright (C) 2015 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by Elian Gidoni.
```

## Usage

### traceroute.py
```
usage: traceroute.py [-h] [--first-hop FIRST_HOP] [--gateways GATEWAYS]
                     [--icmp] [--max-hop MAX_HOP]
                     [--connection-type {icmp,udp}] [--port PORT]
                     [--tries TRIES] [--resolve-hostnames]
                     [--type-of-service TYPE_OF_SERVICE] [--wait WAIT]
                     host output_file

Wrapper for traceroute

positional arguments:
  host                  Host to trace route to
  output_file           File to store resuilts in

optional arguments:
  -h, --help            show this help message and exit
  --first-hop FIRST_HOP
                        Set initial hop distance, that is the time-to-live
  --gateways GATEWAYS   List of gateways for loose source routing
  --icmp                Use ICMP ECHO as probe
  --max-hop MAX_HOP     Set maximal hop count
  --connection-type {icmp,udp}
                        Method to use for traceroute operations
  --port PORT           Port to use
  --tries TRIES         Number of probe packets per hop
  --resolve-hostnames   Resolve hostnames
  --type-of-service TYPE_OF_SERVICE
                        Set type of service (TOS)
  --wait WAIT           Number of seconds to wait for response
```

### view-results.py
```
usage: view-results.py [-h]
                       data_file {info,hostnames,stats,chart,table,map}
                       [hostnames [hostnames ...]]

Visualises traceroute data

positional arguments:
  data_file             File with traceroute data
  {info,hostnames,stats,chart,table,map}
                        Action to carry out on data
  hostnames             Hostnames to visualise

optional arguments:
  -h, --help            show this help message and exit
```

## Assignment

*Quarkslab IRMA Detection Coverage & Performance Internship 2018 - 2019 Assignment*

You may know the traceroute command on unix. Given a host, it shows the intermediate hosts with their latency. Eg.

```sh
$  traceroute fr.wikipedia.org
traceroute to rr.knams.wikimedia.org (145.97.39.155), 30 hops max, 38 byte packets
1  80.67.162.30 (80.67.162.30)  0.341 ms  0.300 ms  0.299 ms
2  telehouse2-gw.netaktiv.com (80.67.170.1)  5.686 ms  1.656 ms  0.428 ms
3  giga.gitoyen.net (80.67.168.16)  1.169 ms  0.704 ms  0.563 ms
4  62.4.73.27 (62.4.73.27)  2.382 ms  1.623 ms  1.297 ms
5  ge5-2.mpr2.cdg2.fr.above.net (64.125.23.86)  1.196 ms ge9-4.mpr2.cdg2.fr.above.net (64.125.23.102)  1.290 ms ge5-1.mpr2.cdg2.fr.above.net (64.125.23.82)  30.297 ms
6  so-5-0-0.cr1.lhr3.uk.above.net (64.125.23.13)  41.900 ms  9.658 ms  9.118 ms
7  so-7-0-0.mpr1.ams5.nl.above.net (64.125.27.178)  23.403 ms  23.209 ms  23.703 ms
8  64.125.27.221.available.above.net (64.125.27.221)  19.149 ms so-0-0-0.mpr3.ams1.nl.above.net (64.125.27.181)  19.378 ms 64.125.27.221.available.above.net (64.125.27.221)  20.017 ms
9  PNI.Surfnet.ams1.above.net (82.98.247.2)  16.834 ms  16.384 ms  16.129 ms
10  af-500.xsr01.amsterdam1a.surf.net (145.145.80.9)  21.525 ms 20.645 ms  24.101 ms
11  kncsw001-router.customer.surf.net (145.145.18.158)  20.233 ms 16.868 ms  19.568 ms
12  gi0-24.csw2-knams.wikimedia.org (145.97.32.29)  23.614 ms  23.270 ms  23.574 ms
13  rr.knams.wikimedia.org (145.97.39.155)  23.992 ms  23.050 ms 23.657 ms
```

We want you to play a bit with python and the traceroute command. First, write a small program in python3 able to call traceroute, to parse its information and to put it in a database (feel free to use the storage you find the most suited, just a file might be enough).

Then, write a second program that read this database and display useful information about it (ex. a graph, some statistics, a path from an host to another, etc.)

With this assignment, we want you to show your ability to parse unformatted data, to use it efficiently, and to display it nicely. Make a clever use of traceroute options, store your data in a structure that is easy to understand and process, show relevant information.
