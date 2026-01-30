import sys
from struct import unpack, calcsize

import cdm_bindings

if len(sys.argv) != 2:
    print("Expected file path as an argument")
    sys.exit(-1)

with open(sys.argv[1], "rb") as f:
    s = f.read()

decoder = cdm_bindings.FileDecoder(s)
ebis = decoder.get_baffle_settings()
header = decoder.get_header()
print(hex(header.magic_byte))
print(header.type)
frame = decoder.read_full_frame();
print(frame.timestamp)
print(frame.count, len(frame.data))
print(frame.data[0].sum)

