"""
Class definition for gate database. It contains the list of gates and
relational databases, and defines gate names and their path delays.
"""


class GateDB:

    names = {'and', 'nand', 'or', 'nor', 'not', 'xor', 'buf'}
    delays = {'nand': 1, 'nor': 1, 'xor': 1, 'not': 1,
              'and': 1, 'or': 1, 'buf': 1}

    def __init__(self):
        # Key by output pin, value is GateElement object
        self.db = {}

    class GateElement:

        def __init__(self, gate, output_pin, input_pin):
            # input_pin is list of input pins, e.g. ['N1', 'N2', 'N3']
            # going from starting input pin to final output pin.
            self.gate = gate
            self.output_pin = output_pin
            self.input_pin = input_pin

            assert gate in self.names

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
