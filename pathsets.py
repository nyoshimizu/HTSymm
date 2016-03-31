
""" Pathset used for extending paths and determining delay-defining path lengths.

    Attributes:

        paths: Paths are stored as lists, as their order must be preserved. Each path is saved as a list of nodes.
        For example, [N22, N10, N1]. Their values can be retrieved from the db_node_values. These can then be
        aggregated into a list to represent all the possible paths that are being considered for the delay-defining
        paths. For example, [ [N22, N10, N1], [N23, N19, N7] ].

        circuit: A string name of circuit being processed, e.g. c17.

        verilog_path: A string path of the verilog code.

        const_gates: A dictionary of constants for strings to use for gates. These strings are set to four characters,
        conforming to the four character gate names used in the Verilog codes.

        db_input_pins: A set of the input pins of the circuit.

        db_output_pins: A set of the output pins of the circuit.

        db_node_pins: A set of nodes of the circuit that are not input or output pins.

        db_gates: A dictionary of gates, where the keys are the output pins and the values are an object comprised of
        a gate type and the input pins.

        db_node_depths: A dictionary of node depths, index by a 2tuple of (node, inputpin): {depth(s)}. Note that
        multiple path lengths between a node and an input pin are only recorded once, becaause it is saved as a
        set, not a list.

        db_node_values: A dictionary of node values, that is the value of all nodes in a circuit given a set of inputs

        db_covered_nodes: A list of covered nodes.

        db_results: A list of results generated of the form, [[result1], [result2], ...]. Each [result] is of the
        form, [input_string, output pin, output pin value, min/max/either condition, path delay,
        list of delay-defining paths, list of covered nodes]

        db_mods_circuit: A list of modifications made to the original circuit. It is assumed tha the modification occurs
        where a gate is inserted at a node. Each element is of the form
        [original pin, [pins to other inputs of inserted gate], gate type as string]

The make_db_node_depths() method creates db_node depth, which is a dictionary of node depths of all nodes in the
circuit.

The make_db_node_values_rand() method creates db_node_values, based on the input pin values, using randomly generated
numbers.

The make_db_node_values() method creates db_node_values, based on pin values of the input pins in db_node_values.

The make_db_dd_paths() method fills the variable paths with paths for determining the delay-defining path.

The branch_point() method returns th

The gate_output() determines the output given a gate type and input values

The dd_path_value returns the value for which the input pins are the delay-defining paths.

The path_length_T returns the path length as number of transistors for a path, which is a list of nodes.

The dd_paths_iterative expands the circuit tree and determines the path delay and delay-defining path(s) given the
node values in db_node_values.

The covered_nodes receives the path delay results and determines nodes that are covered.

The mods_insert method will modify db_input_pins, db_output_pins, db_node_pins, and db_gates then rerun
self.make_db_node_depths() to insert the circuit mods based on db_mods_circuit.

The mods_remove method will modify db_input_pins, db_output_pins, db_node_pins, and db_gates then rerun
self.make_db_node_depths() to remove the circuit mods based on db_mods_circuit.

"""

import sys
import mmap
import random



class Pathset(object):

    class db_gate(object):

        def __init__(self, gate, input_pins):
            self.gate = gate
            self.input_pins = input_pins

    class db_result(object):

        def __init__(self, input_string, output_pin, output_pin_value, minmax, path_delay, paths, covered_nodes):
            self.input_string = input_string
            self.output_pin = output_pin
            self.output_pin_value = output_pin_value
            self.minmax = minmax
            self.path_delay = path_delay
            self.paths = paths
            self.covered_nodes = covered_nodes

    def __init__(self, circuit, verilog_path):
        """ Return a new Pathset object. Initialize the set of paths. """

        self.paths = []
        self.circuit = circuit
        self.verilog_path = verilog_path

        self.db_input_pins = {}
        self.db_output_pins = {}
        self.db_node_pins = {}
        self.db_gates = {}
        self.db_node_depths = {}
        self.db_node_values = {}
        self.db_init_node_values = []
        self.db_covered_nodes = []
        self.db_results = []
        self.const_gates = {'and': 'and', 'nand': 'nand', 'or': 'or', 'nor': 'nor', 'not': 'not', 'xor': 'xor',
                            'buf': 'buf'}

        self.db_mods_circuit = []

        self.make_db_input_pins()
        self.make_db_output_pins()
        self.make_db_node_pins()
        self.make_db_gates()
        self.make_db_node_depths()

    def make_db_input_pins(self):
        """ Make database of input pins from the verilog code. """

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as file_data:
            file_verilog = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')
            if verilog_line[0:5] == 'input':
                break
            elif verilog_line == "":
                print("")
                print('Reached EOF verilog file without ''input''! Exiting..')
                print("")
                file_verilog.close()
                sys.exit()

        verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
        self.db_input_pins = set(verilog_line.split(','))

        file_verilog.close()

    def make_db_output_pins(self):
        """ Make database of output pins from the verilog code. """

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as file_data:
            file_verilog = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')
            if verilog_line[0:6] == 'output':
                break
            elif verilog_line == "":
                print("")
                print('Reached EOF verilog file without ''output''! Exiting..')
                print("")
                file_verilog.close()
                sys.exit()

        verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
        self.db_output_pins = set(verilog_line.split(','))

        file_verilog.close()

    def make_db_node_pins(self):
        """ Make database of node pins from the verilog code. """

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as file_data:
            file_verilog = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')
            if verilog_line[0:4] == 'wire':
                break
            elif verilog_line == "":
                print("")
                print('Reached EOF verilog file without ''wire''! Exiting..')
                print("")
                file_verilog.close()
                sys.exit()

        self.db_node_pins = set()

        while True:
            if ';' in verilog_line:
                verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
                self.db_node_pins |= set(verilog_line.split(','))
                break
            else:
                verilog_line = verilog_line[verilog_line.find('N'):-3]
                self.db_node_pins |= set(verilog_line.split(','))
                verilog_line = file_verilog.readline()
                verilog_line = verilog_line.decode('ascii')

        file_verilog.close()

    def make_db_gates(self):
        """ Make database of gates from the verilog code. """

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as file_data:
            file_verilog = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')
            if verilog_line[0:verilog_line.find(" ")] in self.const_gates:
                gate = verilog_line[0:verilog_line.find(" ")]
                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')
                outpin = verilog_line[0]
                inpin = verilog_line[1:]
                self.db_gates[outpin] = self.db_gate(gate, inpin)

            elif verilog_line == "":
                break

        file_verilog.close()

    def make_db_node_depths(self):
        """
        Make database of node depths from the verilog code, saved as a dict. Each key consists of a 2tuple of
        (node, input pin) and the value is a set of depths (there may be more than one path to reach an input
        pin). Note that as the verilog code is written where new pins are introduced only after their input pins
        have also been introduced, there is no need to check that the input pins are already listed in the dict.
        However, the algorithm will catch such mistakes anyway, checking that the input pins to a new gate already
        have their node depths defined. Note that an output pin should never show up in more than one gate.
        """

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as filedata:
            file_verilog = mmap.mmap(filedata.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')

            if verilog_line[0:verilog_line.find(' ')] in self.const_gates.values():

                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')

                outpin = verilog_line[0]
                inpins = verilog_line[1:]

                if not set(inpins).issubset(set(self.db_input_pins) | set(j[0] for j in self.db_node_depths.keys())):
                    print("")
                    print("Pins found while creating db_node_depths that were out of order. Please check the verilog" +
                          "code")
                    print("")
                    file_verilog.close()
                    sys.exit()

                for inpin in inpins:
                    if inpin in self.db_input_pins:
                        if (outpin, inpin) in self.db_node_depths:
                            self.db_node_depths[(outpin, inpin)] |= {1}
                        else:
                            self.db_node_depths[(outpin, inpin)] = {1}
                    else:
                        new_node_depths = {j: self.db_node_depths[j] for j in self.db_node_depths if j[0] == inpin}

                        for j in new_node_depths:
                            if (outpin, j[1]) in self.db_node_depths:
                                self.db_node_depths[outpin, j[1]] |= {k+1 for k in new_node_depths[inpin, j[1]]}
                            else:
                                self.db_node_depths[outpin, j[1]] = {k+1 for k in new_node_depths[inpin, j[1]]}

            elif verilog_line == '':
                break

        file_verilog.close()

    def make_db_node_values(self, initialization = 'None', PRNG_seed = 0, PRNG_offset_initial = 0):
        """
        Determine the value of all nodes in the circuit based on values of input pins.

        If initialization parameter is empty, generate values based on existing input pin values.

        If initialzation parameter is 'PRNG', generate random input pin values based on PRNG_seed and
        PRNG_offset_initial then determine the values of all nodes in the circuit.

        initialization: initialization method
        PRNG_seed: Seed for PRNG
        PRNG_offset_initial: Offset count for getting a bit from the PRNG.
        """

        if initialization == 'PRNG':

            random.seed(PRNG_seed)
            if PRNG_offset_initial * len(self.db_input_pins) > 0:
                random.getrandbits(PRNG_offset_initial * len(self.db_input_pins))

            input_pin_list_sorted = sorted(self.db_input_pins, key=lambda number: int(number[1:]))

            self.db_node_values[input_pin_list_sorted[0]] = 0
            for j in input_pin_list_sorted:
                self.db_node_values[j] = random.getrandbits(1)

        self.db_init_node_values = [[j, self.db_node_values[j]]
                                    for j in sorted(self.db_node_values, key=lambda number: int(number[1:]))
                                    if j in self.db_input_pins]

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as filedata:
            file_verilog = mmap.mmap(filedata.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')

            if verilog_line[0:verilog_line.find(' ')] in self.const_gates.keys():
                gate = verilog_line[0:verilog_line.find(' ')]
                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')
                outpin = verilog_line[0]
                inpins = verilog_line[1:]

                try:
                    inpins_values = {self.db_node_values[j] for j in inpins}
                except KeyError:
                    file_verilog.close()
                    print("Pins were not already determined when running make_db_node_values, " +
                          "particularly: " + str([j for j in inpins if j not in self.db_node_values]) + "\n")
                    print('Exiting...' + "\n")

                try:
                    output = self.gate_output(gate, inpins_values)
                except KeyError:
                    file_verilog.close()
                    print("Unknown gate type encountered, particularly: " + gate + "\n")
                    print("Exiting..." + "\n")

                self.db_node_values[outpin] = output

            elif verilog_line[0:9] == 'endmodule':
                break

        try:
            if any(j not in self.db_input_pins | self.db_output_pins | self.db_node_pins for j in self.db_node_values):
                file_verilog.close()
                raise KeyError("Some nodes were not evaluated when running make_db_node_pins, namely:" +
                               str([j for j in self.db_input_pins | self.db_output_pins | self.db_node_pins
                                    if j not in self.db_node_values]) + "\n" + "Exiting..." + "\n")
        finally:
            pass

        file_verilog.close()

    def dd_path_value(self, gate, inputs):
        """
        Calculate the input values that determine the path delay through the gate.
        gate: A string, which must be one of the values listed in const_gates, which is the gate being used.
        inputs: A set of  input values being applied to the gate. IT IS ASSUMED that the inputs set is a complete
        set of input values to the gate (no matter how many inputs it may have).
        Returns list of input value(s) through for which the input pins determine the path delay through the gate.
        """

        if gate == self.const_gates['and']:
            if any(j == 0 for j in inputs):
                return [0]
            else:
                return [1]
        elif gate == self.const_gates['nand']:
            if any(j == 0 for j in inputs):
                return [0]
            else:
                return [1]
        elif gate == self.const_gates['or']:
            if any(j == 1 for j in inputs):
                return [1]
            else:
                return [0]
        elif gate == self.const_gates['nor']:
            if any(j == 1 for j in inputs):
                return [1]
            else:
                return [0]
        elif gate == self.const_gates['not']:
            return [0, 1]
        elif gate == self.const_gates['buf']:
            return [0, 1]
        elif gate == self.const_gates['xor']:
            return [0, 1]
        elif gate == self.const_gates['nor']:
            return [0, 1]
        else:
            print("")
            print("Unknown gates found when running dd_path_value, namely: ", gate, ".")
            print("Exiting...")
            print("")
            sys.exit()

    def dd_path_minmax(self, gate, output):
        """
        Calculate whether all input values contribute to a gate output (the maximum delay determines the path delay) or
        only one input determines the output (the minimum delay determines the delay).

        gate: A string, which must be one of the values listed in const_gates, which is the gate being used.
        output: The output value of the gate.

        Returns either "min" or "max," referring to the conditions described above, or "either" if it is neither e.g.
        for a NOT gate.
        """

        if gate == self.const_gates['and']:
            if output == 0:
                return "min"
            else:
                return "max"
        elif gate == self.const_gates['nand']:
            if output == 1:
                return "min"
            else:
                return "max"
        elif gate == self.const_gates['or']:
            if output == 1:
                return "min"
            else:
                return "max"
        elif gate == self.const_gates['nor']:
            if output == "0":
                return "min"
            else:
                return "max"
        elif gate == self.const_gates['not']:
            return "either"
        elif gate == self.const_gates['xor']:
            return "either"

        else:
            print("")
            print("Unknown gates found when running dd_path_minmax, namely: ", gate, ".")
            print("Exiting...")
            print("")
            sys.exit()

    def gate_output(self, gate, inputs):
        """
        Calculate the output value of a gate with given inputs

        gate: A string, which must be one of the values listed in const_gates, which is the gate being used.
        inputs: A set of  input values being applied to the gate. IT IS ASSUMED that the inputs set is a complete
        set of input values to the gate (no matter how many inputs it may have).

        Returns the gate output value
        """

        if gate == 'and':
            if any(j == 0 for j in inputs):
                return 0
            else:
                return 1
        elif gate == 'nand':
            if any(j == 0 for j in inputs):
                return 1
            else:
                return 0
        elif gate == 'or':
            if any(j == 1 for j in inputs):
                return 1
            else:
                return 0
        elif gate == 'nor':
            if any(j == 1 for j in inputs):
                return 0
            else:
                return 1
        elif gate == 'not':
            if any(j == 1 for j in inputs):
                return 0
            else:
                return 1
        elif gate == 'xor':
            if 0 in inputs and 1 in inputs:
                return 1
            else:
                return 0
        else:
            print("")
            print("Unknown gates found when running gate_output, namely: ", gate, ".")
            print("Exiting...")
            print("")
            sys.exit()

    def branch_point(self, paths):
        """
        Calculates the branch point among a list of paths. The branch point is the number of jumps between nodes until
        the outpin of the gate where the branch occurs is reached, i.e., paths [N1,N2,N3] and [N1,N2,N4] have a branch
        point of 1.

        paths: list of paths being evaluated
        """

        # Length of any path will work as worst-case-scenario
        branch_point = 0

        for k in range(len(paths[0])):
            if any(path[k] is not paths[0][k] for path in paths):
                branch_point = k-1
                break
        return  branch_point

    def path_length_T(self, path):
        """
        Determines the path length of path, which is a list of nodes, measured as number of transistors that it passes
        through. Note that it assumes that the path through a transistor involves a fixed number of transistors,
        irrespective of the input or output values.

        Returns a whole number reflecting the number of transistors it passes through.
        """

        path_length = 0
        for step in range(len(path)-1):
            output_node = path[step]
            gate = self.db_gates[output_node].gate

            if gate in {'nand', 'nor', 'xor', 'not'}:
                path_length += 1
            elif gate in {'and', 'or', 'buf'}:
                path_length += 2
            else:
                print("")
                print("Unknown gates found when running path_length_T, namely: ", gate, ".")
                print("Exiting...")
                print("")
                sys.exit()

        return path_length

    def dd_paths_iterative(self, paths):
        """
        Determines iteratively the paths which are the delay-defining paths. At each iteration, extend paths to the
        same path length (using path_length_T). If any new paths terminate (i.e. reaches an input pin) evaluate to see
        if any paths should be culled: if a pin serves a minimum condition (i.e. only one input pin is needed to drive
        the output), then cull the other paths to that gate; if a pin serves a maximum condition (i.e. all input pins
        are needed to drive the output), do nothing.

        paths: list of paths being evaluated, i.e. [['N2', 'N1'], ['N4', 'N3', 'N1'],...]. This will likely start out
        as just an output pin. Output pins are first, then nodes that head toward the input pins.

        Add result to db_results.
        """

        save_paths = []

        path_length = 0
        while any(path[-1] not in self.db_input_pins for path in paths):

            # Extend all paths by the minimum amount and find minimum new path length
            new_path_delay_min = 999999999
            for path in paths:
                new_output_pin = path[-1]
                # new_input_pins = self.db_gates[new_output_pin][1:]
                new_input_pins = self.db_gates[new_output_pin].input_pins

                for new_input_pin in new_input_pins:
                    new_path_delay = self.path_length_T(path+[new_input_pin])

                    if new_path_delay < new_path_delay_min:
                        new_path_delay_min = new_path_delay
                        if new_path_delay == path_length + 1:
                            break

            # Extend all paths that will increase its delay to new_path_delay_min, and cull unnecessary paths.
            # If at least one path terminates at an input pin, paths can be culled using the following criteria. If the
            # gate is subject to path delay minimums, then the terminated path should be a minimum path and other paths
            # can be culled. If the gate is subject to path delay maximums, then the non-terminated paths will have
            # larger path delays and the terminated paths can be culled.
            #
            # For minmax = "min", if any of the pins is an input pin and of path delay equal to new_path_delay_min,
            # keep only the paths with the input pin.
            # For minmax = "max", if any of the pins is an input pin and of path delay equal to new_path_delay_min,
            # cull the paths with the input pin and keep the rest, unless they are all input pins.
            # Otherwise, keep all paths.
            # Note that "special_pins" are pins that are input pins and of path delay equal to new_path_delay_min.

            new_paths = []

            # Go through each node and recreate the list of paths, except those which should be culled.
            for path in paths:
                output_pin = path[-1]
                output_value = self.db_node_values[output_pin]
                gate = self.db_gates[output_pin].gate
                input_pins = self.db_gates[output_pin].input_pins
                input_values = [self.db_node_values[pin] for pin in input_pins]
                min_max = self.dd_path_minmax(gate, output_value)

                # Keep paths that are delay-defining and remove others
                dd_value = self.dd_path_value(gate, input_values)
                input_pins = [pin for pin in input_pins if self.db_node_values[pin] in dd_value]

                # Make a list of pins that are input pins and have delay equal to new_path_delay, i.e. special
                special_pins = []
                for pin in input_pins:
                    if pin in self.db_input_pins and self.path_length_T([path+[pin]]) == path_length:
                        special_pins += [pin]

                # If special pins exist, paths can be culled based on min/max condition
                if any(special_pins):
                    if min_max == "min":
                        for input_pin in special_pins:
                            new_paths += [path+[input_pin]]
                    elif min_max == "max":
                        for input_pin in input_pins:
                            if input_pin not in special_pins:
                                new_paths += [path+[input_pin]]
                        # All pins are input pins and are therefore max path delay.
                        if not any(new_paths):
                            for input_pin in input_pins:
                                new_paths += [path+[input_pin]]
                    elif min_max == "either":
                        for input_pin in input_pins:
                            new_paths += [path+[input_pin]]
                else:
                    for input_pin in input_pins:
                        new_paths += [path+[input_pin]]

            # Go through paths in paths and saved_paths to make a list of cull paths that are unnecessary due to min/max
            # conditions. Branch points are found as changes in the number of universal appearances of a node along a
            # single path.

            # Calculate universal number of occurrences of all nodes
            node_occurrence = {}
            for path in new_paths + save_paths:
                for pin in path:
                    if pin in node_occurrence:
                        node_occurrence[pin] += 1
                    else:
                        node_occurrence[pin] = 1

            # Determine branch nodes
            branch_nodes = []
            for path in new_paths + save_paths:
                sum_node_occurrence = 1
                for pin in reversed(path):
                    if node_occurrence[pin] > sum_node_occurrence:
                        if pin not in branch_nodes and pin not in self.db_input_pins:
                            branch_nodes += [pin]
                        sum_node_occurrence = node_occurrence[pin]

            # Order branch nodes in reverse order, starting farthest from the output pin in path delay. Branch nodes
            # that are closes to the output pin are evaluated last. Do so by reverse ordering branch nodes by their
            # node occurrence calculated above.

            branch_nodes = sorted(branch_nodes, key=lambda node: node_occurrence[node])

            # For each branch node, go through any relevant paths and determine if they can be culled based on min/max
            # condition

            max_path_delay = 0

            temp_cull_paths = []
            for branch_node in branch_nodes:

                # print('branch node: ', branch_node)
                minmax = self.dd_path_minmax(self.db_gates[branch_node].gate, self.db_node_values[branch_node])

                if minmax == "max":
                    max_path_delay = 0
                    for path in new_paths+save_paths:
                        if branch_node in path:
                            branch_point = path.index(branch_node)
                            if self.path_length_T(path[branch_point:]) > max_path_delay:
                                max_path_delay = self.path_length_T(path[branch_point:])
                                # print('!!!max', path, '-', max_path_delay)
                    for path in new_paths+save_paths:
                        if branch_node in path:
                            branch_point = path.index(branch_node)
                            if self.path_length_T(path[branch_point:]) < max_path_delay:
                                temp_cull_paths += [path]
                                # print('cull max', max_path_delay, ' ', self.path_length_T(path[branch_point:]))
                                # print(path)
                elif minmax == "min":
                    min_path_delay = 999999999999
                    for path in new_paths+save_paths:
                        if branch_node in path:
                            branch_point = path.index(branch_node)
                            if self.path_length_T(path[branch_point:]) < min_path_delay:
                                min_path_delay = self.path_length_T(path[branch_point:])
                                # print('!!!min', path, '-', min_path_delay)
                    for path in new_paths+save_paths:
                        if branch_node in path:
                            branch_point = path.index(branch_node)
                            if self.path_length_T(path[branch_point:]) > min_path_delay:
                                temp_cull_paths += [path]
                                # print('cull min', min_path_delay, ' ', self.path_length_T(path[branch_point:]))
                                # print(path)

                # Remove cull paths from new_paths
                new_paths = [path for path in new_paths if path not in temp_cull_paths]

                # Remove cull paths from save_paths
                save_paths = [path for path in save_paths if path not in temp_cull_paths]

            # Replace paths with newly generated new_paths. If paths end on an input pin, they should have been vetted:
            # pass on to save_paths.
            paths = []
            for path in new_paths:
                if path[-1] in self.db_input_pins:
                    save_paths += [path]
                else:
                    paths += [path]

        # Save result to db_results if does not already exist.
        input_pin_list_sorted = sorted(self.db_input_pins, key=lambda number: int(number[1:]))
        input_string = ''
        for k in input_pin_list_sorted:
            input_string += str(self.db_node_values[k])

        if not any([result for result in self.db_results if result.input_string == input_string and
                    result.output_pin == save_paths[0][0]]):

            # db_results_entry = []
            # # 0. Save input pin value string, ordered from smallest pin number to largest pin number
            # db_results_entry += [input_string]
            # # 1. Save output pin
            # db_results_entry += [save_paths[0][0]]
            # # 2. Save output pin value
            # db_results_entry += [self.db_node_values[save_paths[0][0]]]
            # # 3. Save max/min/either condition
            # branch_point = self.branch_point(save_paths)
            # branch_node = save_paths[0][branch_point]
            # minmax = self.dd_path_minmax(self.db_gates[branch_node].gate, self.db_node_values[branch_node])
            # db_results_entry += [minmax]
            # # 4. Save path delay
            # db_results_entry += [self.path_length_T(save_paths[-1])]
            # # 5. Save list of delay-defining paths
            # db_results_entry += [save_paths]
            # # 6. Save list of covered nodes
            # self.covered_nodes(save_paths)
            # db_results_entry += [self.db_covered_nodes]

            db_results_entry = self.db_result('', '', '', '', '', [], [])

            db_results_entry.input_string = input_string

            db_results_entry.output_pin = save_paths[0][0]

            db_results_entry.output_pin_value = self.db_node_values[save_paths[0][0]]

            branch_point = self.branch_point(save_paths)
            branch_node = save_paths[0][branch_point]
            minmax = self.dd_path_minmax(self.db_gates[branch_node].gate, self.db_node_values[branch_node])
            db_results_entry.minmax = minmax

            db_results_entry.path_delay = self.path_length_T(save_paths[-1])

            db_results_entry.paths = save_paths

            self.covered_nodes(save_paths)
            db_results_entry.covered_nodes = self.db_covered_nodes

            self.db_results += [db_results_entry]

    def covered_nodes(self, result):
        """
        Returns a list of nodes that are covered, i.e. whose changes would be detected in a modified path delay.

        results: A list of the form [['N1', 'N2', ...], ['N4', 'N6', ...], ...], which is a list of the delay-defining
        paths generated by dd_paths_iterative.

        Generates db_covered_nodes, which is a list of nodes that are covered by these delay-defining paths.
        """
        branch_point = self.branch_point(result)
        branch_node = result[0][branch_point]
        minmax = self.dd_path_minmax(self.db_gates[branch_node].gate, self.db_node_values[branch_node])
        if minmax == "max":
            covered_nodes = [node for path in result for node in path]
        if minmax == "min":
            covered_nodes = [node for path in result for node in path[branch_point:]]
        if minmax == "either":
            covered_nodes = [node for path in result for node in path]
        covered_nodes = sorted(list(set(covered_nodes)), key=lambda number: int(number[1:]))
        minmax = result[0]

        if minmax == "max":
            covered_nodes = [node for path in result[1:] for node in path]
        if minmax == "min":
            covered_nodes = [node for path in result[1:] for node in path[branch_point:]]

        covered_nodes = list(set(covered_nodes))
        covered_nodes = sorted(list(set(covered_nodes)), key=lambda number: int(number[1:]))

        self.db_covered_nodes = covered_nodes

    def write_results(self):
        """
        Write results to file. The results are saved to ..\results and a name of the form c17_results.txt.
        File is written as a text file with the following format:

        input list: N1, N2, N3, N6, N7

        input: 10010
        output: N23, 0
        path length: 2
        min/max: max
        covered nodes: N2, N7, N16, N19, N23
        paths:
        N23, N16, N2
        N23, N19, N7

        It will first search through the file to see if any of the results are already saved. It will only save the
        results that are not already written to file.
        """

        # Make list of results that should be saved
        file_results = open('results/' + self.circuit + '_results.txt', "r")

        results_written = []
        file_line = file_results.readline()

        if file_line[:11] != 'input list:':
            file_results.close()

            input_pin_list_sorted = sorted(self.db_input_pins, key=lambda number: int(number[1:]))
            file_results = open('results/' + self.circuit + '_results.txt', "a+")
            file_results.write('input list: ' + ','.join(pin for pin in input_pin_list_sorted) + '\n' + '\n')
            file_results.close()
            file_results = open('results/' + self.circuit + '_results.txt', "r")
            file_line = file_results.readline()

        while True:
            file_line = file_results.readline()

            if file_line[:6] == 'input:':
                results_written += [file_line[7:-1]]

            if not file_line:
                break

        file_results.close()

        file_results = open('results/' + self.circuit + '_results.txt', "a+")

        # Save results to file
        for result in self.db_results:
            if result.input_string not in results_written:
                file_results.write('input: ' + result.input_string + '\n')
                file_results.write('output: ' + result.output_pin + ', ' + str(result.output_pin_value) + '\n')
                file_results.write('min/max: ' + result.minmax + '\n')
                file_results.write('path length: ' + str(result.path_delay) + '\n')
                file_results.write('covered nodes: ' + ','.join(pin for pin in result.covered_nodes) + '\n')
                file_results.write('paths: \n')
                for path in result.paths:
                    file_results.write(','.join(pin for pin in path) + '\n')
                file_results.write('\n')

        file_results.close()

    # def mod_insert(self):
    #     """
    #     Modify db_input_pins, db_output_pins, db_node_pins, and db_gates then rerun self.make_db_node_depths() to
    #     insert the circuit mods based on db_mods_circuit. db_mods_circuit is a list with elements of modifications of
    #     the form,
    #     [original pin, [pins to other inputs of inserted gate], gate type as string]
    #
    #     Let added pins be numbered as M1, M2, ...
    #     """
    #
    #     mod_num = 0
    #
    #
    #     for mod in self.db_mods_circuit:
    #
    #         mod_num += 1
    #
    #         mod_original_pin = mod[0]
    #         mod_input_pins = mod[1]
    #         mod_gate = mod[2]
    #         mod_new_pin_name = 'M'+str(mod_num)
    #
    #         self.db_node_pins += mod_new_pin_name
    #
    #         if mod_original_pin in self.db_node_pins:
    #
    #             for output_pin in self.db_gates:
    #                 # De-link old pin from gate inputs
    #                 input_pins = self.db_gates[output_pin][1:]
    #                 if mod_original_pin in input_pins:
    #                     self.db_gates[output_pin][1] = [pin for pin in self.db_gates[output_pin][1] if
    #                                                      pin != mod_original_pin] + [mod_new_pin_name]
    #             # Link mod gate between mod new pin and original pin and mod input pins
    #             self.db_gates[mod_new_pin_name] = [mod_gate, [mod_original_pin]+mod_input_pins]
    #
    #         if mod_original_pin in self.db_output_pins:
    #
    #             self.db_gates[mod_new_pin_name] = self.db_gates[mod_original_pin]
    #             self.db_gates[mod_original_pin] = [mod_gate, [mod_new_pin_name]+mod_input_pins]
