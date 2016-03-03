
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

        db_gates: A dictionary of gates, where the keys are the output pins and the values are a list comprised of
        a gate type and the input pins.

        db_node_depths: A dictionary of node depths, index by a 2tuple of (node, inputpin): {depth(s)}. Note that
        multiple path lengths between a node and an input pin are only recorded once, becaause it is saved as a
        set, not a list.

        db_node_values: A dictionary of node values, that is the value of all nodes in a circuit given a set of inputs

The make_db_node_depths() method creates db_node depth, which is a dictionary of node depths of all nodes in the
circuit.

The make_db_node_values_rand() method creates db_node_values, based on the input pin values, using randomly generated
numbers.

The make_db_node_values() method creates db_node_values, based on pin values of the input pins in db_node_values.

The make_db_dd_paths() method fills the variable paths with paths for determining the delay-defining path.

The branch_point() method returns th

The gate_output() determines the output given a gate type and input values

The dd_path_value returns the value for which the input pins are the delay-defining paths.

The evaluate_paths method will, once all paths have reached input pins, determine the delay-defining path(s) and the
symmetric paths that were used, and the list of pins that were covered.

"""

import sys
import mmap
import random


class Pathset(object):

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
        self.const_gates = {'and': 'and ', 'nand': 'nand', 'or': 'or  ', 'nor': 'nor '}

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

        verilog_line = verilog_line[verilog_line.find('N'):verilog_line.find(';')]
        self.db_node_pins = set(verilog_line.split(','))

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
                self.db_gates[outpin] = [gate]+inpin
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

            if verilog_line[0:4] in self.const_gates:
                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')

                outpin = verilog_line[0]
                inpins = verilog_line[1:]

                if not set(inpins).issubset(set(self.db_input_pins) | set(j[0] for j in self.db_node_depths.keys())):
                    print("")
                    print("Pins found while creating db_node_depths that were out of order. Please check the verilog\
                    code")
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

    def make_db_node_values_rand(self, PRNG_seed, PRNG_offset_initial):
        """
        Generate random input pin values based on PRNG_seed and PRNG_offset_initial then determine the values
        of all nodes in the circuit

        PRNG_seed: Seed for PRNG
        PRNG_offset_initial: Offset count for getting a bit from the PRNG.
        """

        random.seed(PRNG_seed)
        for j in range(PRNG_offset_initial):
            random.getrandbits(1)

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

            if verilog_line[0:4] in self.const_gates:
                gate = verilog_line[0:4]
                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')
                outpin = verilog_line[0]
                inpins = verilog_line[1:]

                if any(j not in self.db_node_values for j in inpins):
                    print("")
                    print("Pins were not already determined when running make_db_node_values, particularly:")
                    print([j for j in inpins if j not in self.db_node_values])
                    print("Exiting...")
                    print("")
                    file_verilog.close()
                    sys.exit()

                inpins_values = {self.db_node_values[j] for j in inpins}
                output = self.gate_output(gate, inpins_values)
                self.db_node_values[outpin] = output

            elif verilog_line == '':
                break

        if any(j not in self.db_input_pins | self.db_output_pins | self.db_node_pins for j in self.db_node_values):
            print("")
            print("Some nodes were not evaluated when running make_db_node_pins, namely:")
            print([j for j in self.db_input_pins | self.db_output_pins | self.db_node_pins
                   if j not in self.db_node_values])
            print("Exiting..")
            print("")

        file_verilog.close()

    def make_db_node_values(self):
        """
        Determine the value of all nodes in the circuit based on values of input pins.
        """

        self.db_init_node_values = [[j, self.db_node_values[j]]
                                    for j in sorted(self.db_node_values, key=lambda number: int(number[1:]))
                                    if j in self.db_input_pins]

        filename = self.verilog_path + "/" + self.circuit + ".v"
        with open(filename, "r") as filedata:
            file_verilog = mmap.mmap(filedata.fileno(), 0, access=mmap.ACCESS_READ)

        while True:
            verilog_line = file_verilog.readline()
            verilog_line = verilog_line.decode('ascii')

            if verilog_line[0:4] in self.const_gates:
                gate = verilog_line[0:4]
                verilog_line = verilog_line[verilog_line.find('(')+1:verilog_line.find(')')]
                verilog_line = verilog_line.split(', ')
                outpin = verilog_line[0]
                inpins = verilog_line[1:]

                if any(j not in self.db_node_values for j in inpins):
                    print("")
                    print("Pins were not already determined when running make_db_node_values, particularly:")
                    print([j for j in inpins if j not in self.db_node_values])
                    print("Exiting...")
                    print("")
                    file_verilog.close()
                    sys.exit()

                inpins_values = {self.db_node_values[j] for j in inpins}
                output = self.gate_output(gate, inpins_values)
                self.db_node_values[outpin] = output

            elif verilog_line == '':
                break

        if any(j not in self.db_input_pins | self.db_output_pins | self.db_node_pins for j in self.db_node_values):
            print("")
            print("Some nodes were not evaluated when running make_db_node_pins, namely:")
            print([j for j in self.db_input_pins | self.db_output_pins | self.db_node_pins
                   if j not in self.db_node_values])
            print("Exiting..")
            print("")

        file_verilog.close()

    def dd_path_value(self, gate, inputs):
        """
        Calculate the input values that determine the path delay through the gate.
        gate: A string, which must be one of the values listed in const_gates, which is the gate being used.
        inputs: A set of  input values being applied to the gate. IT IS ASSUMED that the inputs set is a complete
        set of input values to the gate (no matter how many inputs it may have).
        Returns the input value through for which the input pins determine the path delay through the gate.
        """

        if gate == self.const_gates['and']:
            if any(j == 0 for j in inputs):
                return 0
            else:
                return 1
        elif gate == self.const_gates['nand']:
            if any(j == 0 for j in inputs):
                return 0
            else:
                return 1
        elif gate == self.const_gates['or']:
            if any(j == 1 for j in inputs):
                return 1
            else:
                return 0
        elif gate == self.const_gates['nor']:
            if any(j == 1 for j in inputs):
                return 1
            else:
                return 0
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

        Returns either "min" or "max," referring to the conditions described above.
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

        if gate == self.const_gates['and']:
            if any(j == 0 for j in inputs):
                return 0
            else:
                return 1
        elif gate == self.const_gates['nand']:
            if any(j == 0 for j in inputs):
                return 1
            else:
                return 0
        elif gate == self.const_gates['or']:
            if any(j == 1 for j in inputs):
                return 1
            else:
                return 0
        elif gate == self.const_gates['nor']:
            if any(j == 1 for j in inputs):
                return 0
            else:
                return 1
        else:
            print("")
            print("Unknown gates found when running gate_output, namely: ", gate, ".")
            print("Exiting...")
            print("")
            sys.exit()

    def branch_point(self, paths):
        """
        Calculates the branch point among a list of paths. The branch point number of jumps between nodes until the \
        outpin of the gate where the branch occurs is reached, i.e., paths [N1,N2,N3] and [N1,N2,N4] have a branch point
        of 1.

        paths: list of paths being evaluated
        """

        # Length of any path will work as worst-case-scenario
        branch_point = 0
        for k in range(len(paths[0])):
            if any(path[k] is not paths[0][k] for path in paths):
                branch_point = k-1
                break
        return  branch_point

    def dd_paths_recursive(self, paths):
        """
        Determines recursively the path delays of delay-defining paths. For each recursion, any paths that have any
        non-input pins should be expanded then recursively applied to this function or all paths end at input pins
        and the min/max can be evaluated for each step.

        path: list of paths being evaluated.

        Returns a list of either the path length (if the final pin is an input pin) or the path; the final
        element indicates whether the "max" or "min" of the path delays should be used.
        """

        # All the paths that do not end in an input must be extended and recursively reevaluated
        extend_paths = [path for path in paths if path[-1] not in self.db_input_pins]
        result_paths = []
        for path in extend_paths:
            gate = self.db_gates[path[-1]][0]
            input_pins = self.db_gates[path[-1]][1:]
            defining_value = self.dd_path_value(gate, [self.db_node_values[j] for j in input_pins])
            path = [path+[j] for j in self.db_gates[path[-1]][1:] if self.db_node_values[j] == defining_value]
            result_paths += self.dd_paths_recursive(path)
        paths = [path for path in paths if path[-1] in self.db_input_pins]
        paths += [path for path in result_paths]

        # If all paths in paths have reached an input pin, the min/max operation can be used to reduce the list
        if all(path[-1] in self.db_input_pins for path in paths):
            # branch_point is the output pin at which the paths diverted at a gate, which determines whether the min
            # delay (only one input value required) or max delay (all input values required). At each split, branch
            # point occurs when initial segment of paths are all the same nodes.

            # Length of any path will work as worst-case-scenario
            branch_point = self.branch_point(paths)

            branch_node = paths[0][branch_point]

            minmax = self.dd_path_minmax(self.db_gates[branch_node][0], self.db_node_values[branch_node])
            if minmax == 'min':
                minmax = min([len(path)-1 for path in paths])
            if minmax == 'max':
                minmax = max([len(path)-1 for path in paths])

            return [path for path in paths if len(path) == minmax+1]

    def results (self):
        """
        Returns a set list of results: [ the output pin, the value of the output pin, max/min requirement,
        [the delay-determinibg paths], [covered nodes] ].
        """

a = Pathset('c17', 'verilog')
print('---------------')
# a.db_node_values['N1'] = 1
# a.db_node_values['N2'] = 0
# a.db_node_values['N3'] = 1
# a.db_node_values['N6'] = 0
# a.db_node_values['N7'] = 0
# a.make_db_node_values()
# print(a.db_node_values)
#result = a.dd_paths_recursive([['N22']])
#print(result)
print('---------------')