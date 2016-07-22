"""
This function determines the delay defining paths for a circuit. It requires a
db.VerilogDB to determine the delay-defining paths and net path delay for a
circuit given a certain input.
"""

from random import (
    seed,
    randrange
)


class rand_inputs:
    """
    A generator for creating random inputs for all input pins.

    pins is integer number of input pins in the circuit.
    seed_num is integer seed for the random generator.
    offset is integer number of PRNG numbers to skip before adding to returned
    list of inputs.

    Iterator returns rand_return, a string of binary with initial '0b removed
    and padded to match number of bits as required by pins input.

    Note that PRNG is initialized with seed when object is created, not when
    iterator is called.
    """

    def __init__(self, pins, seed_num, offset):

        self.pins = pins
        self.rand_size = 2 ** self.pins
        self.seed_num = seed_num
        self.offset = offset

        seed(seed_num)

        self.rand_return = ''
        for k in range(seed_num):
            self.rand_return = randrange(self.rand_size)

    def __next__(self):

        self.rand_return = randrange(self.rand_size)
        self.rand_return = bin(self.rand_return)[2:]
        self.rand_return.zfill(self.pins)

        return self.rand_return

