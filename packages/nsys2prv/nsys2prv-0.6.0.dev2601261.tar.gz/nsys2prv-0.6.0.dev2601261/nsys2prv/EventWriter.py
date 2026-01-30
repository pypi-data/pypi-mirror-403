import os
import tqdm
import math
from .semantics.nsys_event import ESD

DEFAULT_BLOCK_WRITE_SIZE = 4096

class ListBuffer():
    """Use lists as a storage"""
    def __init__(self):
        self.__io = []

    def clear(self):
        old_val = self.value()
        self.__init__()
        return old_val

    def value(self):
        return "".join(self.__io)

    def write(self, symbol):
        self.__io.append(symbol)

def event_writer(prv_file, df, name, serialization_f):
    if "NSYS2PRV_BLOCK_WRITE_SIZE" is os.environ:
        BLOCK_WRITE_SIZE = int(os.getenv("NSYS2PRV_BLOCK_WRITE_SIZE"))
    else:
        BLOCK_WRITE_SIZE = DEFAULT_BLOCK_WRITE_SIZE
    num_rows = df.shape[0]
    lbuffer = ListBuffer()
    for b in tqdm.tqdm(range(math.floor(num_rows / BLOCK_WRITE_SIZE)+1), desc="{} ({:.2E} events)".format(name, num_rows*2), unit="blocks"):
        limit = min(BLOCK_WRITE_SIZE, num_rows - b*BLOCK_WRITE_SIZE)
        for index in range(limit):
            row = df.iloc[index + b*BLOCK_WRITE_SIZE]
            lbuffer.write(serialization_f(row))
        prv_file.write(lbuffer.value())
        lbuffer.clear()

def serialize_esdd(d: list[ESD], f):
    for i, v in enumerate(d):
        f.write("EVENT_TYPE\n")
        f.write("0 {} {}\n".format(v["type"], v["name"]))
        if v["names"] is not None:
            f.write("VALUES\n")
            f.write("0 End\n")
            for index, row in v["names"].iterrows():
                f.write("{} {}\n".format(row["event_value"], row["Name"]))
        f.write("\n")