import pathsets

def runscript():

    PRNG_seed = 12

    cake = pathsets.Pathset('c17', 'verilog')

    for PRNG_offset in range(10):
        print("")
        print('========================')
        cake.make_db_node_values(PRNG_seed, PRNG_offset)
        print(cake.db_init_node_values)
        for outpin in cake.db_output_pins:
            result = cake.dd_paths_recursive([[outpin]])
            branch_point = cake.branch_point(result)
            branch_node = result[0][branch_point]
            minmax = cake.dd_path_minmax(cake.db_gates[branch_node][0], cake.db_node_values[branch_node])
            result = [minmax] + result
            if minmax == "max":
                covered_nodes = [node for path in result[1:] for node in path]
            if minmax == "min":
                covered_nodes = [node for path in result[1:] for node in path[branch_point:]]
            covered_nodes = sorted(list(set(covered_nodes)), key=lambda number: int(number[1:]))
            print(result)
            print(covered_nodes)
