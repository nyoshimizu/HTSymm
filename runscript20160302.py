"""
    This script will generate results for a whole set of input values. By doing so, 2-D plots of the path
    pathlength results vs input values can be used to 'view' the symmetries: the x- and y-axis are the value of the
    input pins and the values are the path lengths, as measured by # of transistors.

    Order of input values applied is for pins [N1, N2, N5, ...] and inputs are [0, 0, 0, .. ], [1, 0, 0, ...], to
    [1, 1, 1, ...].
"""

import pathsets
import math

def runscript():

    circuit = 'c432'
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
        print('Input: ', input_string)

        print(len(input_pin_list_sorted))

        for outputpin in cake.db_output_pins:
            result = cake.dd_paths_iterative([[outputpin]])
            branch_point = cake.branch_point(result)
            branch_node = result[0][branch_point]
            minmax = cake.dd_path_minmax(cake.db_gates[branch_node][0], cake.db_node_values[branch_node])
            result = [minmax] + result
            if minmax == "max":
                covered_nodes = [node for path in result[1:] for node in path]
            if minmax == "min":
                covered_nodes = [node for path in result[1:] for node in path[branch_point:]]
            pathlength = cake.path_length_T(result[-1])

            for k in range(len(output_pin_list_sorted)):
                if outputpin == output_pin_list_sorted[k]:
                    results[k][1].append(pathlength)

    file_results = open('results/' + circuit + '_results.txt', "a+")

    for result_set in results:
        # Write output pin
        file_results.write(result_set[0]+"\n")
        # Write list of path delays
        file_results.write(",".join(str(k) for k in result_set[1]) + "\n")

    for result_set in results:

        # Write output pin
        file_results.write(result_set[0]+"\n")
        # Write table of path delays
        column_num = math.floor(len(cake.db_input_pins)/2)
        row__num = len(cake.db_input_pins) - column_num
        column_num = 2**column_num
        row__num = 2**row__num

        for row in range(row__num):
            column_start = row*column_num
            column_end = column_start + column_num
            file_results.write(",".join(str(k) for k in result_set[1][column_start:column_end]) + "\n")

    file_results.close()

    print()
    print('Results:')
    print(results)