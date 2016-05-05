"""
Load verilog code and return its contents as a verilog db class, defined below.
"""

import mmap
from db.gate_db import GateDB
from db.gates import Gates


class VerilogDB:

    def __init__(self):
        self.input_pins = {}
        self.output_pins = {}
        self.node_pins = {}
        self.gates = GateDB()

    def input_pins_sorted(self):
        return sorted(self.input_pins, key=lambda number: int(''.join(k for k in number if k.isdigit())))

    def output_pins_sorted(self):
        return sorted(self.output_pins, key=lambda number: int(''.join(k for k in number if k.isdigit())))

    def node_pins_sorted(self):
        return sorted(self.node_pins, key=lambda number: int(''.join(k for k in number if k.isdigit())))


def load_verilog(circuit):

    filename = "../verilog/" + circuit + ".v"

    return_db = VerilogDB()

    with open(filename, "r") as file_data:
        file_verilog = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

    # Read input pins
    while True:
        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')
        if verilog_line[0:5] == 'input':
            break

    verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
    return_db.input_pins = set(verilog_line.split(','))

    # Read output pins
    while True:
        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')
        if verilog_line[0:6] == 'output':
            break

    verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
    return_db.output_pins = set(verilog_line.split(','))

    # Read node pins
    while True:
        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')
        if verilog_line[0:4] == 'wire':
            break

    verilog_line = verilog_line[5:]
    verilog_line_2 = ''
    while True:
        if 'N' not in verilog_line:
            break

        if ';' in verilog_line:
            verilog_line_2 += verilog_line[verilog_line.find('N'):verilog_line.find(';')]
        else:
            verilog_line_2 += verilog_line[verilog_line.find('N'):verilog_line.rfind(',')+1]

        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')

    return_db.node_pins = set(verilog_line_2.split(','))

    # Read gate
    while True:
        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')
        if verilog_line[0:verilog_line.find(" ")] in Gates().names:
            gate = verilog_line[0:verilog_line.find(" ")]
            verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
            verilog_line = verilog_line.split(', ')
            outpin = verilog_line[0]
            inpin = verilog_line[1:]

            return_db.gates.db[outpin] = GateDB.GateElement(gate, outpin, inpin)

        elif verilog_line == "":
            break

    file_verilog.close()

    return return_db
