#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Total bytes read/written

import getopt, sys

diskstats = "/proc/diskstats"

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:m:")
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-d":
        device = a
    elif o == "-m":
        direction = 0 if a == "r" else 1

ds = open(diskstats, "r")
stats_lines = ds.readlines()
ds.close
sectors = 0

for line in stats_lines:
    stats = line.split()
    if device in stats:
        if direction:
            sectors = stats[9]
        else:
            sectors = stats[5]

bytes = int(sectors)*512

if bytes < 1024:
    print ("%fB" % bytes)
elif bytes < 1024*1024:
    kb = bytes/1024
    print ("%.2fKiB" % kb)
elif bytes < 1024*1024*1024:
    mb = bytes/1024/1024
    print ("%.2fMiB" % mb)
else:
    gb = bytes/1024/1024/1024
    print ("%.2fGiB" % gb)