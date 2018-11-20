# TracerouteWrapper

## Requirements
* Traceroute *(see version below)*
* Python3
* Python packages in **requirements.txt**
* Graphviz

## Supported Traceroute Version
```
traceroute (GNU inetutils) 1.9.4
Copyright (C) 2015 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by Elian Gidoni.
```

```
Modern traceroute for Linux, version 2.1.0
Copyright (c) 2016  Dmitry Butskoy,   License: GPL v2 or any later
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

## Example Usage

### To run traceroute on `yahoo.com` and store output in **output.json**
```sh
# To run with default options
./traceroute.py yahoo.com output.json

# Resolve hostnames
./traceroute.py --resolve-hostnames yahoo.com output.json

# Use 10 tries
./traceroute.py --tries 10 yahoo.com output.json
```

### To visualise data in **output.json**
```sh
# General information
./view-results.py output.json info

# List of hostnames
./view-results.py output.json hostnames

# General statistics
./view-results.py output.json stats

# Statistics on yahoo.com only
./view-results.py output.json stats yahoo.com

# Table summarising all data
./view-results.py output.json table

# More detailed table on yahoo.com only
./view-results.py output.json table yahoo.com

# Colourplot summarising all data
./view-results.py output.json chart

# More detailed bar chart on yahoo.com only
./view-results.py output.json chart yahoo.com

# Full map
./view-results.py output.json map

# Map of yahoo.com only
./view-results.py output.json map yahoo.com
```
