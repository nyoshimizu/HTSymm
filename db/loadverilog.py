"""
Load verilog code and return its contents as a verilog db class, defined below.
"""

import mmap
from db.gate_db import GateDB
from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    MetaData,
    create_engine,
    select,
    text,
)


class VerilogDB:
    """
    Class that stores Verilog database of pins, gates, and pin values.
    """

    def __init__(self):
        self.input_pins = set()
        self.input_pin_values = {}
        self.output_pins = set()
        self.output_pin_values = {}
        self.node_pins = set()
        self.node_pin_values = {}
        self.gatedb = GateDB()

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

    filename = "./verilog/" + circuit + ".v"

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
        if verilog_line[0:verilog_line.find(" ")] in GateDB.names:
            gate = verilog_line[0:verilog_line.find(" ")]
            verilog_line = verilog_line[verilog_line.find('(')+1:
                                        verilog_line.find(')')]
            verilog_line = verilog_line.split(', ')
            outpin = verilog_line[0]
            inpin = verilog_line[1:]

            return_db.gatedb.db[outpin] = GateDB.GateElement(
                                         gate, outpin, inpin)

        elif verilog_line == "":
            break

    file_verilog.close()

    return return_db


class VerilogSQL:
    """
    Class to access and query Verilog SQL database.
    """

    metadata = MetaData()

    # Define SQL table objects.
    input_pins_table = Table('input_pins', metadata,
                             Column('id', Integer, primary_key=True),
                             Column('circuit', String),
                             Column('input_pin', String)
                             )

    output_pins_table = Table('output_pins', metadata,
                              Column('id', Integer, primary_key=True),
                              Column('circuit', String),
                              Column('output_pin', String)
                              )

    node_pins_table = Table('node_pins', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('circuit', String),
                            Column('node_pin', String)
                            )
    gates_table = Table('gates', metadata,
                        Column('id', Integer, primary_key=True),
                        Column('circuit', String),
                        Column('gate', String),
                        Column('output_pin', String),
                        Column('input_pin0', String),
                        Column('input_pin1', String),
                        Column('input_pin2', String),
                        Column('input_pin3', String),
                        Column('input_pin4', String),
                        Column('input_pin5', String),
                        Column('input_pin6', String),
                        Column('input_pin7', String),
                        Column('input_pin8', String),
                        Column('input_pin9', String),
                        )

    def __init__(self):
        self.loaded = False
        self.circuit = None
        self.conn = None
        self.VerilogDB = VerilogDB()

    def loadfile(self):
        engine = create_engine('sqlite:///db/verilog.sqlite3', echo=False)
        self.conn = engine.connect()
        self.loaded = True

    def closefile(self):
        self.conn.close()
        self.loaded = False

    def loadinputpins(self):

        sel = select([self.input_pins_table]).where(
                     self.input_pins_table.c.circuit == self.circuit)

        query = self.conn.execute(sel)

        self.VerilogDB.input_pins = set()
        for _, _, pin in query:
            self.VerilogDB.input_pins.add(pin)

        query.close()

    def loadoutputpins(self):

        sel = select([self.output_pins_table]).where(
                     self.output_pins_table.c.circuit == self.circuit)

        query = self.conn.execute(sel)

        self.VerilogDB.output_pins = set()
        for _, _, pin in query:
            self.VerilogDB.output_pins.add(pin)

        query.close()

    def loadnodepins(self):

        sel = select([self.node_pins_table]).where(
                     self.node_pins_table.c.circuit == self.circuit)

        query = self.conn.execute(sel)

        self.VerilogDB.node_pins = set()
        for _, _, pin in query:
            self.VerilogDB.node_pins.add(pin)

        query.close()

    def loadgates(self):

        sel = select([self.gates_table]).where(
                      self.gates_table.c.circuit == self.circuit)

        query = self.conn.execute(sel)

        self.VerilogDB.gatedb.db = {}
        for (_, _, gate, out_pin, in_pin0, in_pin1, in_pin2, in_pin3, in_pin4,
             in_pin5, in_pin6, in_pin7, in_pin8, in_pin9) in query:

            in_pins = [in_pin0, in_pin1, in_pin2, in_pin3, in_pin4,
                       in_pin5, in_pin6, in_pin7, in_pin8, in_pin9]
            self.VerilogDB.gatedb.add(gate,
                               out_pin,
                               [pin for pin in in_pins if pin is not None]
                               )

        query.close()

    def readgateswithinputs(self, input_pins):
        """
        Reads from the VerilogSQL file the data from the gates table the
        gates that have input pins that are all in the input_pins passed to
        the method.

        circuit = string of circuit name
        input_pins: set of input pins

        Returns a GateDB.db object of gate elements which adhere to the
        criterion.
        """
        returngatedb = GateDB()

        s_circuit = self.circuit

        if len(input_pins) > 10:
            raise ValueError("readgateswithinputs received more than 10 " +
                             "input pins.")
        else:
            s_textpins = list(input_pins)+['none']*(10-len(input_pins))

        # SQL code to find gates that have all its input pins in a given
        # set of pins.
        #
        # select gate, ouput_pin, input_pin0, input_pin1, input_pin2,
        #         input_pin3, input_pin4, input_pin5, input_pin6,
        #         input_pin7, input_pin8, input_pin9
        # from gates
        # where circuit = 'c17'
        # and (input_pin0 in ('N1', 'N3', 'N2', 'N11') or input_pin0 is null)
        # and (input_pin1 in ('N1', 'N3', 'N2', 'N11') or input_pin1 is null)
        # ;

        # SQLAlchemy does not seem to be able to bind multiple items per param?

        SQL_text = text(
                   "SELECT gate, output_pin, input_pin0, input_pin1, "
                   "input_pin2, input_pin3, input_pin4, input_pin5, "
                   "input_pin6, input_pin7, input_pin8, input_pin9 "
                   "FROM gates "
                   "WHERE circuit = :textcircuit "
                   "AND (input_pin0 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin0 IS null) "
                   "AND (input_pin1 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin1 IS null) "
                   "AND (input_pin2 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin2 IS null) "
                   "AND (input_pin3 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin3 IS null) "
                   "AND (input_pin4 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin4 IS null) "
                   "AND (input_pin5 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin5 IS null) "
                   "AND (input_pin6 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin6 IS null) "
                   "AND (input_pin7 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin7 IS null) "
                   "AND (input_pin8 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin8 IS null) "
                   "AND (input_pin9 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9) OR input_pin9 IS null) "
                   ";"
        )

        if self.loaded is True:
            SQL_text = SQL_text.bindparams(textcircuit=s_circuit,
                                           t0=s_textpins[0],
                                           t1=s_textpins[1],
                                           t2=s_textpins[2],
                                           t3=s_textpins[3],
                                           t4=s_textpins[4],
                                           t5=s_textpins[5],
                                           t6=s_textpins[6],
                                           t7=s_textpins[7],
                                           t8=s_textpins[8],
                                           t9=s_textpins[9]
                                           )

            query = self.conn.execute(SQL_text)

        else:
            raise IOError("SQL file not opened before executing \
                          readgateswithinputs")

        results = [str(r) for r in query]
        for k in range(len(results)):
            # Remove parantheses
            results[k] = results[k][1:-1]
            # Remove single quotes from results
            results[k] = results[k].replace("'", "")
            # Split into lists
            results[k] = results[k].split(', ')

        for result in results:
            gate = result[0]
            output_pin = result[1]
            input_pins = set([pin for pin in result[2:] if pin != 'None'])
            returngatedb.add(gate, output_pin, input_pins)

        return returngatedb

    def update_pin_values(self):
        """
        Starting with circuit input pins, update pin values. Perform
        iteratively by getting all values that can be calculated from input
        pins, then calculate new values based on newly calculated pins, etc.

        Requires self.gatedb to have been loaded from the SQL database using
        self.loadfile() and all gate list and pin lists to have been loaded
        by running self.load self.loadinputpins(), self.loadnodepins(),
        and self.loadoutputpins() so that results can be distributed at the
        end.

        Requires self.VerilogDB.input_pin_values to be complete.

        Updates self.gatedb rather than return data.
        """
        if any([pin for pin in self.VerilogDB.input_pins
                if pin not in self.VerilogDB.input_pin_values.keys()]):
            raise ValueError("Error in update_pin_values: not all input pins \
                have values")

        node_values = dict()
        for pin in self.VerilogDB.input_pin_values:
            node_values[pin] = self.VerilogDB.input_pin_values[pin]

        new_inputs = self.VerilogDB.input_pins
        used_inputs = set()
        new_outputs = set()

        while any(new_inputs):
            for new_input in new_inputs:
                newgatedb = self.readgateswithinputs(new_inputs)
                used_inputs |= new_inputs
                new_outputs = set(newgatedb.db.keys())
                for new_output in new_outputs:
                    print('New output: ', new_output)
                    gate_input_pins = newgatedb.db[new_output].input_pins
                    print('inputs :', gate_input_pins)
                    gate_type = newgatedb.db[new_output].gate
                    print('gate type: ', gate_type)
                    gate_input_values = [node_values[pin]
                                         for pin in gate_input_pins]
                    print('values: ', gate_input_values)
                    node_values[new_output] = newgatedb.gateoutput(
                                               gate_type, gate_input_values)

            # Only add to new_inputs if they are not output pins.
            new_inputs |= new_outputs - self.VerilogDB.output_pins

        for pin in node_values:
            if pin in self.VerilogDB.node_pins:
                self.VerilogDB.node_pin_values[pin] = node_values[pin]
            elif pin in self.VerilogDB.input_pins:
                self.VerilogDB.input_pin_values[pin] = node_values[pin]
            elif pin in self.VerilogDB.output_pins:
                self.VerilogDB.output_pin_values[pin] = node_values[pin]
        # INFINITE LOOP
