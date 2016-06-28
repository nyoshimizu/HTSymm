"""
Load verilog code and return its contents as a verilog db class, defined below.
"""

import mmap
from db.gate_db import GateDB
from db.gates import Gates
import sqlalchemy


class VerilogDB:

    def __init__(self):
        self.input_pins = set()
        self.output_pins = set()
        self.node_pins = set()
        self.gates = GateDB()

    def input_pins_sorted(self):
        return sorted(self.input_pins, key=lambda number:
                      int(''.join(k for k in number if k.isdigit())))

    def output_pins_sorted(self):
        return sorted(self.output_pins, key=lambda number:
                      int(''.join(k for k in number if k.isdigit())))

    def node_pins_sorted(self):
        return sorted(self.node_pins, key=lambda number:
                      int(''.join(k for k in number if k.isdigit())))


def load_verilog(circuit):
    """
    Load verilog file and return as VerilogDB object.

    circuit is name of circuit to load

    Returns VerilogDB object
    """

    filename = "../verilog/" + circuit + ".v"

    return_db = VerilogDB()

    with open(filename, "r") as file_data:
        file_verilog = mmap.mmap(file_data.fileno(), 0,
                                 access=mmap.ACCESS_READ)

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
            verilog_line_2 += verilog_line[verilog_line.find('N'):
                                           verilog_line.find(';')]
        else:
            verilog_line_2 += verilog_line[verilog_line.find('N'):
                                           verilog_line.rfind(',')+1]

        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')

    return_db.node_pins = set(verilog_line_2.split(','))

    # Read gate
    while True:
        verilog_line = file_verilog.readline()
        verilog_line = verilog_line.decode('ascii')
        if verilog_line[0:verilog_line.find(" ")] in Gates().names:
            gate = verilog_line[0:verilog_line.find(" ")]
            verilog_line = verilog_line[verilog_line.find('(')+1:
                                        verilog_line.find(')')]
            verilog_line = verilog_line.split(', ')
            outpin = verilog_line[0]
            inpin = verilog_line[1:]

            return_db.gates.db[outpin] =
            GateDB.GateElement(gate, outpin, inpin)

        elif verilog_line == "":
            break

    file_verilog.close()

    return return_db


class VerilogSQL:
    """
    Class to access and query verilog SQL database.
    """

    def __init__(self):
        self.loaded = False
        self.circuit = None
        self.conn = None
        self.db = VerilogDB()

    def loadfile(self):
        engine = create_engine('sqlite:///verilog.sqlite3', echo=False)
        self.conn = engine.connect()
        self.loaded = True

    def closefile(self):
        self.conn.close()
        self.loaded = False

    def loadinputpins(self, circuit):
        self.circuit = circuit

        metadata = MetaData()

        input_pins_table = Table('input_pins', metadata,
                                 Column('id', INTEGER, primary_key=True),
                                 Column('circuit', TEXT),
                                 Column('input_pin', TEXT)
                                 )

        sel = select([input_pins_table]).where(input_pins_table.c.circuit ==
                                               self.circuit)

        query = self.conn.execute(sel)

        self.db.input_pins = set()
        for _, _, pin in query:
            self.db.input_pins.add(pin)

        query.close()

    def loadoutputpins(self, circuit):
        self.circuit = circuit

        metadata = MetaData()

        output_pins_table = Table('output_pins', metadata,
                                  Column('id', INTEGER, primary_key=True),
                                  Column('circuit', TEXT),
                                  Column('output_pin', TEXT)
                                  )

        sel = select([output_pins_table]).where(output_pins_table.c.circuit ==
                                                self.circuit)

        query = self.conn.execute(sel)

        self.db.output_pins = set()
        for _, _, pin in query:
            self.db.output_pins.add(pin)

        query.close()

    def loadnodepins(self, circuit):

        self.circuit = circuit

        metadata = MetaData()

        node_pins_table = Table('node_pins', metadata,
                                Column('id', INTEGER, primary_key=True),
                                Column('circuit', TEXT),
                                Column('node_pin', TEXT)
                                )

        sel = select([node_pins_table]).where(node_pins_table.c.circuit ==
                                              self.circuit)

        query = self.conn.execute(sel)

        self.db.node_pins = set()
        for _, _, pin in query:
            self.db.node_pins.add(pin)

        query.close()

    def loadgates(self, circuit):

        self.circuit = circuit

        metadata = MetaData()

        gates_table = Table('gates', metadata,
                            Column('id', INTEGER, primary_key=True),
                            Column('circuit', TEXT),
                            Column('gate', TEXT),
                            Column('output_pin', TEXT),
                            Column('input_pin', TEXT)
                            )

        sel = select([gates_table]).where(gates_table.c.circuit ==
                                          self.circuit)

        query = self.conn.execute(sel)

        self.db.gates.db = {}
        for _, _, gate, out_pin, in_pin in query:
            if out_pin in self.db.gates.db:
                in_pin_other = self.db.gates.db[out_pin].input_pin
                self.db.gates.db[out_pin] =
                GateDB.GateElement(gate, out_pin, [in_pin]+[in_pin_other])
            else:
                self.db.gates.db[out_pin] =
                GateDB.GateElement(gate, out_pin, in_pin)

        query.close()
