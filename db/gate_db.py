"""
Class definition for gate database. It contains the list of gates and
relational databases, and defines gate names and their path delays.
"""

import re


class GateDB:

    names = {'and', 'nand', 'or', 'nor', 'not', 'xor', 'buf'}
    delays = {'nand': 1, 'nor': 1, 'xor': 1, 'not': 1,
              'and': 2, 'or': 2, 'buf': 2}

    def __init__(self):
        # Key by output pin, value is GateElement object
        self.db = {}

    def __repr__(self):

        try:
            keylist = list(self.db.keys())
        except TypeError:
            print("GateDB __repr__ finds db is not dict type.")

        # Sort output pins (keys) by digits.
        keylistsorted = sorted(keylist, key=lambda akey:
                               ''.join(letter for letter in akey
                                       if letter.isdigit()))

        print_repr = ''

        for key in keylistsorted:
            print_repr += str(self.db[key]) + "\n"

        return print_repr

    def add(self, gate, output_pin, input_pins):

        # Add GateElement to self.db
        self.db[output_pin] = self.GateElement(gate, output_pin, input_pins)

    class GateElement:

        def __init__(self, gate, output_pin, input_pins):
            # input_pin is set of input pins
            self.gate = gate
            self.output_pin = output_pin
            self.input_pins = input_pins

            assert gate in GateDB.names

        def __repr__(self):
            return "O: {}, G: {}, I: {}".format(
                                         self.output_pin,
                                         self.gate,
                                         re.sub("[\[\]']",
                                                "",
                                                str(self.sorted_input_pins())
                                                )
                                         )

        def sorted_input_pins(self):
            return sorted(list(self.input_pins), key=lambda number:
                          int(''.join(k for k in number if k.isdigit())))

    def path_delay(self, gate_list):
        """
        Calculate path delay of gatelist.
        Returns path delay.
        """

        try:
            delays = [self.delays[gate] for gate in gate_list]
            delays = sum(delays)

        except ValueError:
            print('Error in gate list received for calculating path delay')

        return delays

    def gateoutput(self, gate, inputs):
        """
        Calculates output value for a given gate for given input values.

        gate: String of gate type; should conform to set of gates GateDB.names.
        inputs: List of values of input pins.

        Returns output value.
        """

        if gate not in GateDB.names:
            raise ValueError("GateDB.gateoutput received gate type not in " +
                             "GateDB.names: " + gate)

        elif gate == 'and':
            if any([input == '0' for input in inputs]):
                return 0
            else:
                return 1

        elif gate == 'nand':
            if any([input == 0 for input in inputs]):
                return 1
            else:
                return 0

        elif gate == 'or':
            if any([input == 1 for input in inputs]):
                return 1
            else:
                return 0

        elif gate == 'nor':
            if any([input == 1 for input in inputs]):
                return 0
            else:
                return 1

        elif gate == 'not':
            if len(inputs) > 1:
                raise ValueError("GateDB.gateoutput received more than one " +
                                 "inputs for a NOT gate.")
            elif inputs == [0]:
                return 1
            elif inputs == [1]:
                return 0

        elif gate == 'xor':
            if len(inputs) != 2:
                raise ValueError("GateDB.gateoutput did not receive two " +
                                 "inputs for XOR gate: " + len(inputs) + ".")
            elif 0 in inputs and 1 in inputs:
                return 1
            else:
                return 0

        elif gate == 'buf':
            if len(inputs) > 1:
                raise ValueError("GateDB.gateoutput received more than one " +
                                 "input for BUF gate.")
            elif inputs == [0]:
                return 0
            elif inputs == [1]:
                return 1

        else:
            raise ValueError("GateDB.gateoutput received gate that resulted " +
                             "in no return value: " + gate + ".")
