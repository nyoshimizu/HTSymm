"""
Class definition for gate database. It contains the list of gates and relational databases.
"""

from .gates import Gates


class GateDB:

    def __init__(self):
        self.db = {}

    class GateElement:

        def __init__(self, gate, output_pin, input_pin):

            self.gate = gate
            self.output_pin = output_pin
            self.input_pin = input_pin

            assert gate in Gates().names
