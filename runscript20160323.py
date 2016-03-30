"""
    This script will generate results for an random set of input values.

    Order of input values applied is for pins [N1, N2, N5, ...] and inputs are [0, 0, 0, .. ], [1, 0, 0, ...], to
    [1, 1, 1, ...].
"""

import pathsets

def runscript():

    PRNG_seed = 1
    PRNG_num = 10000
    PRNG_offset = 0

    cake = pathsets.Pathset('c432', 'verilog')

    for PRNG in range(PRNG_num):
        print("")
        print('========================')
        print(PRNG, '/', PRNG_num)

        cake.make_db_node_values('PRNG', PRNG_seed, PRNG+PRNG_offset)

        input_pin_list_sorted = sorted(cake.db_input_pins, key=lambda number: int(number[1:]))

        input_string = ''
        for k in input_pin_list_sorted:
            input_string += str(cake.db_node_values[k])

        for outpin in cake.db_output_pins:

            cake.dd_paths_iterative([[outpin]])

    cake.write_results()
