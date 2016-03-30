"""
    This script will generate results for a whole set of input values.

    Order of input values applied is for pins [N1, N2, N5, ...] and inputs are [0, 0, 0, .. ], [1, 0, 0, ...], to
    [1, 1, 1, ...].
"""

import pathsets
import math

def runscript():

    circuit = 'c17'
    cake = pathsets.Pathset(circuit, 'verilog')
    # Save the pathlengths of each output pin, then final element is the set of input values
    results = []
    for outputpin in cake.db_output_pins:
        results.append([outputpin, []])

    for testcase in range(2**len(cake.db_input_pins)):
        print("")
        print('========================')

        input_pin_list_sorted = sorted(cake.db_input_pins, key=lambda number: int(number[1:]))
        for (index, inputpin) in enumerate(input_pin_list_sorted):
            cake.db_node_values[inputpin] = (testcase >> index) & 1

        output_pin_list_sorted = sorted(cake.db_output_pins, key=lambda number: int(number[1:]))

        cake.make_db_node_values()

        input_string = ''
        for k in input_pin_list_sorted:
            input_string += str(cake.db_node_values[k])
        print('Input pins: ', input_pin_list_sorted)
        print('Input: ', input_string)

        for outputpin in output_pin_list_sorted:

            cake.dd_paths_iterative([[outputpin]])

    cake.write_results()