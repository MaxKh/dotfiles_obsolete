#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Scrolling output of paconky by MaxKh

import os


size = 42
buf = []

home = os.path.expanduser("~")
packets_path = os.path.join(home, ".cache/packets")
step_path = os.path.join(home, ".cache/step")

try:
    f_pack = open(packets_path, "r")
    packets = f_pack.readlines()
    f_pack.close()
except:
    if os.path.isfile(step_path):
        os.remove(step_path)
    packets = []

try:
    f_step = open(step_path, "r")
    step = int(f_step.readline())
    f_step.close()
except:
    step = 0

num_packets = len(packets)

if num_packets <= size:
    step = 0

buf += packets[step:step+size]


if step+size > num_packets and size < num_packets:
    buf += packets[0:step+size-num_packets]

step = 0 if (step == num_packets or size >= num_packets)  else step+1

f_step = open(step_path, "w+")
f_step.write(str(step))
f_step.close()

if len(buf) < size:
    buf += ["\n"]*(size-len(buf))

for p in buf:
    print(p, end = '')
