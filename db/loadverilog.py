"""
Load verilog code and return its contents as a verilog db class, defined below.
"""

import mmap
import re
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

    # Define Verilog SQL table objects.

    metadataVerilog = MetaData()

    input_pins_table = Table('input_pins', metadataVerilog,
                             Column('id', Integer, primary_key=True),
                             Column('circuit', String),
                             Column('input_pin', String)
                             )

    output_pins_table = Table('output_pins', metadataVerilog,
                              Column('id', Integer, primary_key=True),
                              Column('circuit', String),
                              Column('output_pin', String)
                              )

    node_pins_table = Table('node_pins', metadataVerilog,
                            Column('id', Integer, primary_key=True),
                            Column('circuit', String),
                            Column('node_pin', String)
                            )
    gates_table = Table('gates', metadataVerilog,
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

    # Define symmpath count SQL table objects.

    metadatasymmpathcount = MetaData()

    symmpath_count_table = Table('symmpath_counts', metadatasymmpathcount,
                                 Column('id', Integer, primary_key=True),
                                 Column('circuit', String),
                                 Column('pin', String),
                                 Column('path_delay', Integer),
                                 Column('num_paths', Integer),
                                 )

    def __init__(self):
        self.loaded = False
        self.circuit = None
        self.conn = None
        self.VerilogDB = VerilogDB()

    def loadfile(self):
        self.engineVerilog = create_engine(
                              'sqlite:///db/verilog.sqlite3', echo=False)
        self.metadataVerilog.bind = self.engineVerilog
        self.metadataVerilog.create_all(checkfirst=True)
        self.conn = self.engineVerilog.connect()
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

    def readgateswithinputs(self, input_pins, req_input_pins):
        """
        Reads from the VerilogSQL file the data from the gates table the
        gates that have input pins that are all in the input_pins passed to
        the method, and which must have input pins in the req_input_pins
        list.

        input_pins: set of input pins
        req_input_pins: set of input pins which must be inputs to gate.

        Returns a GateDB.db object of gate elements which adhere to the
        criterion.
        """

        returngatedb = GateDB()

        s_circuit = self.circuit

        if len(input_pins) > 10 or len(req_input_pins) > 10:
            raise ValueError("readgateswithinputs received more than 10 " +
                             "input or required input pins.")
        elif any(input_pins & req_input_pins):
            raise ValueError("readgateswithinputs received pins that were " +
                             "in both input_pins and req_input_pins: " +
                             str(input_pins & req_input_pins))
        else:
            s_textinputpins = (list(input_pins) +
                               ['none']*(10-len(input_pins)))
            s_textreqinputpins = (list(req_input_pins) +
                                  ['none']*(10-len(req_input_pins)))

        # SQL code to find gates that have all its input pins in a given
        # set of pins. Assume we have values for N1, N2, N11 and we have new
        # values for N3 and N4 which must be in the gates we find.
        #
        # select gate, ouput_pin, input_pin0, input_pin1, input_pin2,
        #         input_pin3, input_pin4, input_pin5, input_pin6,
        #         input_pin7, input_pin8, input_pin9
        # from gates
        # where circuit = 'c17'
        # and (input_pin0 in ('N1', 'N2', 'N11', 'N3', 'N4')
        #                             or input_pin0 is null)
        # and (input_pin1 in ('N1', 'N2', 'N11', 'N3', 'N4')
        #                             or input_pin1 is null)
        # and ('N3' in (input_pin0, input_pin1)
        # or 'N4' in (input_pin0, input_pin1))
        # ;

        # SQLAlchemy does not seem to be able to bind multiple items per param?

        SQL_text = text(
                   "SELECT gate, output_pin, input_pin0, input_pin1, "
                   "input_pin2, input_pin3, input_pin4, input_pin5, "
                   "input_pin6, input_pin7, input_pin8, input_pin9 "
                   "FROM gates "
                   "WHERE circuit = :textcircuit "
                   "AND (input_pin0 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin0 IS null) "
                   "AND (input_pin1 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin1 IS null) "
                   "AND (input_pin2 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin2 IS null) "
                   "AND (input_pin3 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin3 IS null) "
                   "AND (input_pin4 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin4 IS null) "
                   "AND (input_pin5 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin5 IS null) "
                   "AND (input_pin6 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin6 IS null) "
                   "AND (input_pin7 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin7 IS null) "
                   "AND (input_pin8 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin8 IS null) "
                   "AND (input_pin9 IN (:t0, :t1, :t2, :t3, :t4, :t5, :t6, \
                         :t7, :t8, :t9, :rt0, :rt1, :rt2, :rt3, :rt4, :rt5, \
                         :rt6, :rt7, :rt8, :rt9) OR input_pin9 IS null) "
                   "AND (:rt0 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt1 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt2 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt3 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt4 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt5 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt6 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt7 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt8 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9) "
                   "OR :rt9 IN (input_pin0, input_pin1, input_pin2, \
                        input_pin3, input_pin4, input_pin5, input_pin6, \
                        input_pin7, input_pin8, input_pin9)) "
                   ";"
        )

        if self.loaded is True:
            SQL_text = SQL_text.bindparams(textcircuit=s_circuit,
                                           t0=s_textinputpins[0],
                                           t1=s_textinputpins[1],
                                           t2=s_textinputpins[2],
                                           t3=s_textinputpins[3],
                                           t4=s_textinputpins[4],
                                           t5=s_textinputpins[5],
                                           t6=s_textinputpins[6],
                                           t7=s_textinputpins[7],
                                           t8=s_textinputpins[8],
                                           t9=s_textinputpins[9],
                                           rt0=s_textreqinputpins[0],
                                           rt1=s_textreqinputpins[1],
                                           rt2=s_textreqinputpins[2],
                                           rt3=s_textreqinputpins[3],
                                           rt4=s_textreqinputpins[4],
                                           rt5=s_textreqinputpins[5],
                                           rt6=s_textreqinputpins[6],
                                           rt7=s_textreqinputpins[7],
                                           rt8=s_textreqinputpins[8],
                                           rt9=s_textreqinputpins[9]
                                           )

            query = self.conn.execute(SQL_text)

        else:
            raise IOError("SQL file not opened before executing \
                          readgateswithinputs")

        results = self.parse_SQL_query(query)

        for result in results:
            gate = result[0]
            output_pin = result[1]
            input_pins = set([pin for pin in result[2:] if pin != 'None'])
            returngatedb.add(gate, output_pin, input_pins)

        return returngatedb

    def readgatewithoutput(self, output_pin):

        """
        Reads from the VerilogSQL file the data from the gates table the
        gate that has inputoutput pin that is given by the passed
        output_pin.

        output_pin: output pin desired.

        Returns a GateDB.db object of the gate element which adheres to the
        criterion.
        """

        returngatedb = GateDB()

        s_circuit = self.circuit
        s_outputpin = output_pin

        # SQL code to find gate that has the given output pin in a given.
        #
        # select *
        # from gates
        # where circuit = 'c17'
        # and output_pin = 'N11'
        # ;

        SQL_text = text(
                        "SELECT * "
                        "FROM gates "
                        "WHERE circuit = :textcircuit "
                        "AND output_pin = :textoutputpin "
                        ";"
                        )

        if self.loaded is True:
            SQL_text = SQL_text.bindparams(textcircuit=s_circuit,
                                           textoutputpin=s_outputpin
                                           )
            query = self.conn.execute(SQL_text)

        else:
            raise IOError("SQL file not opened before executing \
                          readgateswithoutputs")

        # Only one line from SQL query should have returned.
        for line in query:
            result = line

        # Remove parantheses and single quotes from results
        if not result:
            raise ValueError("findgatewithouputs did not return gate.")
        else:
            result = self.parse_SQL_query(result)

        # result[0] is ID
        # result[1] is circuit
        gate = result[2]
        output_pin = result[3]
        input_pins = set([pin for pin in result[4:] if pin != 'None'])

        returngatedb.add(gate, output_pin, input_pins)

        return returngatedb

    def update_pin_values(self):
        """
        Starting with circuit input pins, update pin values. Perform
        iteratively by getting all values that can be calculated from input
        pins, then calculate new values based on newly calculated pins, etc.
        The gives the advantage of not having to load full gate database
        to calculate pin values.

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

        """
        At each round,
        new_inputs: New input pins that should be used to find new gates_table
        used_inputs: Input pins whose values are already known.
        new_outputs: New gate output pins whose values can be used in the next
        round as new_inputs.
        """

        new_inputs = self.VerilogDB.input_pins
        used_inputs = set()
        new_outputs = set()

        while any(new_inputs):
            newgatedb = self.readgateswithinputs(used_inputs, new_inputs)
            used_inputs |= new_inputs
            new_outputs = set(newgatedb.db.keys())
            # Move new outputs to new inputs for next round if they are not
            # circuit output pins.
            new_inputs = new_outputs - self.VerilogDB.output_pins
            for new_output in new_outputs:
                gate_input_pins = newgatedb.db[new_output].input_pins
                gate_type = newgatedb.db[new_output].gate
                gate_input_values = [node_values[pin]
                                     for pin in gate_input_pins]
                node_values[new_output] = newgatedb.gateoutput(
                                           gate_type, gate_input_values)

        for pin in node_values:
            if pin in self.VerilogDB.node_pins:
                self.VerilogDB.node_pin_values[pin] = node_values[pin]
            elif pin in self.VerilogDB.input_pins:
                self.VerilogDB.input_pin_values[pin] = node_values[pin]
            elif pin in self.VerilogDB.output_pins:
                self.VerilogDB.output_pin_values[pin] = node_values[pin]

    def symmpathcountSQL(self):
        """
        Using VerilogSQL database, generate and write a SQL db that contains
        the number of paths which have a certain path delay, measured in
        units of single transistor delays.

        Requires self.gatedb to have been loaded from the SQL database using
        as well as all gate list and pin lists to have been loaded by running
        self.loadfile(), self.loadgates(), self.loadinputpins(),
        self.loadnodepins(), and self.loadoutputpins().

        Paths are considered from the circuit output pins towards the circuit
        input pins. They are stored in a dictionary symmpaths where the key is
        the next pin closest to the input and the value is a list of the path
        delays accumulated so far (accounting for multipule paths due to fan
        out). For each next pin, the next path delay value is added to the
        table and the key/pin changed.

        Note that the next pins should be added to the longest paths so that
        they terminate as soon as possible, where they will be moved to the
        database.

        Note that this assumes a circuit topology free of feedback loops, such
        as those which appear in flip-flop structures. In that case, the
        flip-flops should be expressed in the Verilog code as flip-flops,
        then evaluated as a special case, rather than expressed in its
        primitive XOR gates, etc. (which would not see the feedback loop).
        Otherwise, loops will cause this method to find path lengths which
        are infinite in length and thus cause an infinite loop.

        Writes results to SQL database named "symmpathcount.sqlite3"
        If the circuit name already exists in the SQL file, the program will
        return without running.
        """

        enginesymmpathcount = create_engine(
                              'sqlite:///db/symmpathcount.sqlite3', echo=False)
        self.metadatasymmpathcount.bind = enginesymmpathcount
        self.metadatasymmpathcount.create_all(checkfirst=True)
        conn = enginesymmpathcount.connect()
        sel = select([self.symmpath_count_table.c.circuit])
        sel = sel.where(self.symmpath_count_table.c.circuit == self.circuit)
        results = conn.execute(sel).fetchall()

        for line in results:
            if self.circuit in str(line):
                print("symmpathcountSQL tried analyzing circuit that is " +
                      "already in database; will not run.")
                return

        symmpaths = dict()
        for pin in self.VerilogDB.output_pins:
            symmpaths[pin] = [0]

        finishedpaths = {}

        count = 0
        while any(symmpaths):

            count += 1
            if count % 4096 == 0:
                print("count: ", count)
                print("symmpath size: ",
                      sum([len(symmpath) for symmpath in symmpaths.values()])
                      )
                print()

            maxpath = max(symmpaths.values())
            for key in symmpaths:
                if symmpaths[key] == maxpath:
                    maxpathpin = key

            extendpin = maxpathpin

            outputgatedb = self.readgatewithoutput(extendpin)
            gate = outputgatedb.db[extendpin].gate
            input_pins = outputgatedb.db[extendpin].input_pins

            new_delay = outputgatedb.path_delay([gate])
            old_delays = symmpaths[extendpin]

            for pin in input_pins:
                if pin in symmpaths.keys():
                    symmpaths[pin] = (
                        [old_delay + new_delay for old_delay in old_delays]
                        + symmpaths[pin]
                     )
                elif pin not in symmpaths.keys():
                    symmpaths[pin] = (
                        [old_delay + new_delay for old_delay in old_delays]
                    )

            symmpaths.pop(extendpin)

            new_finishedpaths = {pin: symmpaths[pin]
                                 for pin in symmpaths.keys()
                                 if pin in self.VerilogDB.input_pins
                                 }

            for pin in new_finishedpaths.keys():
                if pin in finishedpaths.keys():
                    finishedpaths[pin] = (finishedpaths[pin] +
                                          new_finishedpaths[pin]
                                          )
                elif pin not in finishedpaths.keys():
                    finishedpaths[pin] = new_finishedpaths[pin]

            for pin in new_finishedpaths.keys():
                symmpaths.pop(pin)

            if (sum([len(finishedpath) for finishedpath
                     in finishedpaths.values()]) > 10000 or
                     not symmpaths):

                for pin in finishedpaths.keys():

                    new_delays = finishedpaths[pin]

                    sel = select([self.symmpath_count_table])
                    sel = sel.where(
                        self.symmpath_count_table.c.circuit == self.circuit
                    )
                    sel = sel.where(
                        self.symmpath_count_table.c.pin == pin
                    )

                    results = conn.execute(sel).fetchall()

                    results = [self.parse_SQL_query(line) for line in results]

                    for new_delay in list(set(new_delays)):
                        if new_delay in [int(result[3]) for result in results]:
                            SQL_update = self.symmpath_count_table
                            SQL_update = SQL_update.update(
                                self.symmpath_count_table,
                                values={self.symmpath_count_table.c.num_paths:
                                        self.symmpath_count_table.c.num_paths +
                                        new_delays.count(new_delay)
                                        }
                            )
                            SQL_update = SQL_update.where(
                                (self.symmpath_count_table.c.circuit ==
                                 self.circuit)
                            )
                            SQL_update = SQL_update.where(
                                self.symmpath_count_table.c.pin == pin
                            )
                            SQL_update = SQL_update.where(
                                (self.symmpath_count_table.c.path_delay ==
                                 new_delay)
                            )
                            conn.execute(SQL_update)

                        elif (new_delay not in
                              [int(result[3]) for result in results]):
                            SQL_insert = self.symmpath_count_table
                            SQL_insert = SQL_insert.insert()
                            SQL_insert = SQL_insert.values(
                                          {'circuit': self.circuit,
                                           'pin': pin,
                                           'path_delay': new_delay,
                                           'num_paths':
                                           new_delays.count(new_delay)
                                           })

                            conn.execute(SQL_insert)
                finishedpaths = {}

        conn.close()

    def parse_SQL_query(self, result):
        """
        Parse SQL query results. Results come in the form of:
        (1, 'c17', 'N2', 2, 1, None, ...)

        This method will parse and return in list form, removing the single
        parentheses and converting strings to integers if appropriate.
        """

        # Remove parantheses and single quotes.
        return_result = re.sub("[()']",
                               "",
                               str(result)
                               )
        # Split into lists.
        return_result = return_result.split(', ')

        # Convert strings to integers, if appropriate.
        for k in return_result:
            if k.isdigit():
                k = int(k)

        return return_result
