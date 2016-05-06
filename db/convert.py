"""
Convert text file databases into SQLite databases to be used by all other modules. Uses SQLite3 via SQLAlchemy.
"""

from sqlalchemy import *
from db.loadverilog import *
from db.gates import *

def convert_verilog_SQLite(circuit):
    """
    Convert verilog text data into SQLite.

    circuit is circuit to be converted.

    Table input_pins (id INTEGER, circuit TEXT, input_pin TEXT)
    Table output_pins (id INTEGER, circuit TEXT, output_pin TEXT)
    Table node_pins (id INTEGER, circuit TEXT, node_pin TEXT)
    Table gates (id INTEGER, circuit TEXT, output_pin TEXT, gate TEXT, input_pin TEXT)

    Returns 1 if data inserted
    Returns 0 if data already exists
    """

    verilog_db = load_verilog(circuit)

    engine = create_engine('sqlite:///verilog.sqlite3', echo=False)

    metadata = MetaData()

    input_pins = Table('input_pins', metadata,
                       Column('id', INTEGER, primary_key=True),
                       Column('circuit', TEXT),
                       Column('input_pin', TEXT)
                       )

    output_pins = Table('output_pins', metadata,
                        Column('id', INTEGER, primary_key=True),
                        Column('circuit', TEXT),
                        Column('output_pin', TEXT)
                        )

    node_pins = Table('node_pins', metadata,
                      Column('id', INTEGER, primary_key=True),
                      Column('circuit', TEXT),
                      Column('node_pin', TEXT)
                      )

    gates = Table('gates', metadata,
                  Column('id', INTEGER, primary_key=True),
                  Column('circuit', TEXT),
                  Column('gate', TEXT),
                  Column('output_pin', TEXT),
                  Column('input_pin', TEXT)
                  )

    metadata.create_all(engine)
    conn = engine.connect()

    # Check if circuit is already in SQLite database input_pins table
    s = select([input_pins.c.circuit]).distinct()
    result = conn.execute(s).fetchall()
    result = str(result)

    if circuit in result:
        conn.close()
        return 0

    # Write SQL database from verilog_db

    input_pins_sorted = verilog_db.input_pins_sorted()

    insert_SQL = []
    for pin in input_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'input_pin': pin
                        }]

    conn.execute(input_pins.insert(), insert_SQL)

    output_pins_sorted = verilog_db.output_pins_sorted()

    insert_SQL = []
    for pin in output_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'output_pin': pin
                        }]

    conn.execute(output_pins.insert(), insert_SQL)

    node_pins_sorted = verilog_db.node_pins_sorted()

    insert_SQL = []
    for pin in node_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'node_pin': pin
                        }]

    conn.execute(node_pins.insert(), insert_SQL)

    insert_SQL = []
    for pin in node_pins_sorted + output_pins_sorted:
        for inpin in verilog_db.gates.db[pin].input_pin:
            insert_SQL += [{'circuit': circuit,
                            'gate': verilog_db.gates.db[pin].gate,
                            'output_pin': pin,
                            'input_pin': inpin
                            }]

    conn.execute(gates.insert(), insert_SQL)

    conn.close()
    return 1

# Code used to generate verilog.sqlite3, 5/4/2016
# convert_verilog_SQLite('c17')
# convert_verilog_SQLite('c432')
# convert_verilog_SQLite('c499')
# convert_verilog_SQLite('c880a')
# convert_verilog_SQLite('c1355')
# convert_verilog_SQLite('c1908')
# convert_verilog_SQLite('c2670')
# convert_verilog_SQLite('c3540')
# convert_verilog_SQLite('c5315')
# convert_verilog_SQLite('c6288')
# convert_verilog_SQLite('c7552')


def convert_symmpaths_SQLite(circuit):
    """
    Convert symmpath text data into SQLite. Due to size of symmpath files, serial read text file and write
    into SQLite file.

    circuit is circuit to be converted.

    Table gate_list (id INTEGER, circuit TEXT, symmpath_id INTEGER, gate_list TEXT, path_delay INTEGER)
    Table path_list (id INTEGER, circuit TEXT, symmpath_id INTEGER, path_list TEXT)

    Returns 1 if data inserted
    Returns 0 if data already exists
    """

    symmpath_db = load_verilog(circuit)

    engine = create_engine('sqlite:///symmpath.sqlite3', echo=False)

    metadata = MetaData()

    gate_list = Table('gate_list', metadata,
                      Column('id', INTEGER, primary_key=True),
                      Column('circuit', TEXT),
                      Column('symmpath_id', INTEGER),
                      Column('gate_list', TEXT),
                      Column('path_delay', INTEGER),
                      )

    path_list = Table('path_list', metadata,
                      Column('id', INTEGER, primary_key=True),
                      Column('circuit', TEXT),
                      Column('symmpath_id', INTEGER),
                      Column('path_list', TEXT),
                      Column('input_pin', TEXT),
                      Column('output_pin', TEXT),
                      Column('node_pins', TEXT),
                      Column('all_pins', TEXT)
                      )

    metadata.create_all(engine)
    conn = engine.connect()

    # Check if circuit is already in SQLite database input_pins table
    s = select([gate_list.c.circuit]).distinct()
    result = conn.execute(s).fetchall()
    result = str(result)

    if circuit in result:
        conn.close()
        return 0

    # Convert symmpath file into SQLite db.
    filename = "../symmpaths/" + circuit + "symmpaths.txt"
    with open(filename, "r") as file_data:
        file_symmpath = mmap.mmap(file_data.fileno(), 0, access=mmap.ACCESS_READ)

    gate_line = file_symmpath.readline()
    gate_line = gate_line.decode('ascii')
    gate_line = gate_line[:-2]
    gate_line = gate_line.replace(" ", "")
    paths = []
    insert_gates_SQL = []
    insert_paths_SQL = []
    symmpath_id = 0

    while True:

        symmpath_id += 1

        while True:
            path_line = file_symmpath.readline()
            path_line = path_line.decode('ascii')
            path_line = path_line[:-2]
            path_line = path_line.replace(" ", "")

            if not path_line:
                break
            elif path_line[0] == 'N':
                paths += [path_line]
            elif path_line[0] != 'N':
                next_gate_line = path_line
                break

        insert_gates_SQL = [{'circuit': circuit,
                             'symmpath_id': symmpath_id,
                             'gate_list': gate_line,
                             'path_delay': Gates().path_delay(gate_line.split(','))
                             }]

        for path in paths:
            path_temp = path.split(',')
            input_pin = path_temp[-1]
            output_pin = path_temp[0]
            node_pins = ','.join(sorted(path_temp[1:-1],
                                        key=lambda number: int(''.join(k for k in number if k.isdigit()))))
            all_pins = ','.join(sorted(path_temp, key=lambda number: int(''.join(k for k in number if k.isdigit()))))

            insert_paths_SQL += [{'circuit': circuit,
                                  'symmpath_id': symmpath_id,
                                  'path_list': path,
                                  'input_pin': input_pin,
                                  'output_pin': output_pin,
                                  'node_pins': node_pins,
                                  'all_pins': all_pins
                                  }]

        conn.execute(gate_list.insert(), insert_gates_SQL)
        conn.execute(path_list.insert(), insert_paths_SQL)

        paths = []
        insert_gates_SQL = []
        insert_paths_SQL = []

        gate_line = next_gate_line

        # Let last symmetric path group be written before exiting
        if not path_line:
            break

# Code used to generate symmpath.sqlite3, 5/6/2016
# convert_symmpaths_SQLite('c17')
# convert_symmpaths_SQLite('c432')
# convert_symmpaths_SQLite('c499')
# convert_symmpaths_SQLite('c880a')
# convert_symmpaths_SQLite('c1355')
# convert_symmpaths_SQLite('c1908')
# convert_symmpaths_SQLite('c2670')
# convert_symmpaths_SQLite('c5315')

