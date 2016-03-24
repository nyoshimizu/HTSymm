import pathsets

def runscript():

    PRNG_seed = 1
    PRNG_num = 10

    cake = pathsets.Pathset('c17', 'verilog')

    for PRNG_offset in range(PRNG_num):
        print("")
        print('========================')
        cake.make_db_node_values('PRNG', PRNG_seed, PRNG_offset)

        input_pin_list_sorted = sorted(cake.db_input_pins, key=lambda number: int(number[1:]))

        input_string = ''
        for k in input_pin_list_sorted:
            input_string += str(cake.db_node_values[k])

        print('Input: ', input_pin_list_sorted)
        print(input_string)
        print('--')
        print("")
        for outpin in cake.db_output_pins:
            cake.dd_paths_iterative([[outpin]])
            print('Output pin: ', cake.db_results[-1][1])
            print('Output value: ', cake.db_results[-1][5])
            print('Path length in transistors: ', cake.db_results[-1][4])
            print('Min/max: ', cake.db_results[-1][3])
            print('Covered nodes: ', cake.db_results[-1][6])
            print('')
