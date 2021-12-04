#!/usr/bin/env python3
import sys
import struct

inp = (open(sys.argv[1], "rb") if len(sys.argv) >= 2 else sys.stdin.buffer).read()
out = open(sys.argv[2], "wb") if len(sys.argv) >= 3 else sys.stdout.buffer

out.write(struct.pack(
    "<HH H H I HBBBBBB 18s18s II IIII", 
    1, 0, # file format
    0, # zlib?
    1, # icon
    len(inp), # file len
    0, 0, 0, 0, 0, 0, 0, # last modified
    b"txt2ptc", # first author
    b"txt2ptc", # last author
    0, 0, # first/last author id (?)
    0, 0, 0, 0,
))
out.write(inp)
out.write(b"\0" * 20)