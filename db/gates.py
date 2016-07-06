"""
Class definition for gates. Contains constants for gate names, gate delays as a
function of transistor delays,
"""


class Gates:

    def __init__(self):

        self.names = {'and', 'nand', 'or', 'nor', 'not', 'xor', 'buf'}
        self.delays = {'nand': 1, 'nor': 1, 'xor': 1, 'not': 1,
                                  'and': 1, 'or': 1, 'buf': 1}

    def path_delay(self, gate_list):

        try:
            delays = [self.delays[gate] for gate in gate_list]
            delays = sum(delays)

        except ValueError:
            print('Error in gate list received for calculating path delay')

        return delays
