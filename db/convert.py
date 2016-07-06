"""
Convert text file databases into SQLite databases to be used by all other
modules. Uses SQLite3 via SQLAlchemy.
"""

from mmap import mmap
from db.loadverilog import (
    load_verilog,
    VerilogSQL
)
from db.gates import Gates
from sqlalchemy import (
    create_engine,
    MetaData,
    select,
    Table,
    Column,
    Integer,
    String,
)


def convert_verilog_SQLite(circuit):
    """
    Convert verilog text data into SQLite.

    circuit is circuit to be converted.

    Table input_pins_table (id Integer, circuit String, input_pin String)
    Table output_pins_table (id Integer, circuit String, output_pin String)
    Table node_pins_table (id Integer, circuit String, node_pin String)
    Table gates_table (
                 id Integer, circuit String, output_pin String, gate String,
                 input_pin0 String, input_pin1 String, input_pin2 String,
                 input_pin3 String, input_pin4 String, input_pin5 String,
                 input_pin6 String, input_pin7 String, input_pin8 String,
                 input_pin9 String
    )

    Returns 1 if data inserted
    Returns 0 if data already exists
    """

    VerilogSQLdb = VerilogSQL()

    verilog_db = load_verilog(circuit)

    engine = create_engine('sqlite:///verilog.sqlite3', echo=False)

    VerilogSQLdb.metadata.create_all(engine)

    conn = engine.connect()

    # Check if circuit is already in SQLite database input_pins table
    try:
        s = select([VerilogSQLdb.input_pins_table.c.circuit]).distinct()
        result = conn.execute(s).fetchall()
        result = str(result)

        if circuit in result:
            conn.close()
            return 0

    except:
        print('Error from SQLAlchemy while checking for existence of tables.')
        # return -1

    # Write SQL database from verilog_db

    input_pins_sorted = verilog_db.input_pins_sorted()

    insert_SQL = []
    for pin in input_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'input_pin': pin
                        }]

    conn.execute(VerilogSQLdb.input_pins_table.insert(), insert_SQL)

    output_pins_sorted = verilog_db.output_pins_sorted()

    insert_SQL = []
    for pin in output_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'output_pin': pin
                        }]

    conn.execute(VerilogSQLdb.output_pins_table.insert(), insert_SQL)

    node_pins_sorted = verilog_db.node_pins_sorted()

    insert_SQL = []
    for pin in node_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'node_pin': pin
                        }]

    conn.execute(VerilogSQLdb.node_pins_table.insert(), insert_SQL)

    insert_SQL = []
    for pin in node_pins_sorted + output_pins_sorted:

        temp_SQL = {}
        for k, inpin in enumerate(verilog_db.gatedb.db[pin].input_pin):
            temp_SQL['input_pin'+str(k)] = inpin

        temp_SQL.update({'circuit': circuit,
                         'gate': verilog_db.gatedb.db[pin].gate,
                         'output_pin': pin
                         })

        insert_SQL += [temp_SQL]

    # Only SQL Insert's of the same size can be batch inserted.
    minsize = min([len(entry) for entry in insert_SQL])
    maxsize = max([len(entry) for entry in insert_SQL])

    for k in range(minsize, maxsize+1):
        temp_SQL = [entry for entry in insert_SQL if len(entry) is k]
        conn.execute(VerilogSQLdb.gates_table.insert(), temp_SQL)

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

# This database renamed verilog_bak.sqlite3, 7/6/2016. DB changed so that
# gates_table lists all input pins in same db entry rather than as separate
# entries each.
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
    Convert symmpath text data into SQLite. Due to size of symmpath files,
    serial read text file and write into SQLite file.

    circuit is circuit to be converted.

    Table gate_list (id Integer, circuit String, symmpath_id Integer,
                     gate_list String, path_delay Integer)
    Table path_list (id Integer, circuit String, symmpath_id Integer,
                     path_list String)

    Returns 1 if data inserted
    Returns 0 if data already exists
    """

    engine = create_engine('sqlite:///symmpath.sqlite3', echo=False)

    metadata = MetaData()

    gate_list = Table('gate_list', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('circuit', String),
                      Column('symmpath_id', String),
                      Column('gate_list', String),
                      Column('path_delay', Integer),
                      )

    path_list = Table('path_list', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('circuit', String),
                      Column('symmpath_id', String),
                      Column('path_list', String),
                      Column('input_pin', String),
                      Column('output_pin', String),
                      Column('node_pins', String),
                      Column('all_pins', String)
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
        file_symmpath = mmap.mmap(file_data.fileno(),
                                  0,
                                  access=mmap.ACCESS_READ
                                  )

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
                             'path_delay':
                             Gates().path_delay(gate_line.split(','))
                             }]

        for path in paths:
            path_temp = path.split(',')
            input_pin = path_temp[-1]
            output_pin = path_temp[0]
            node_pins = ','.join(
             sorted(path_temp[1:-1],
                    key=lambda number:
                    int(''.join(k for k in number if k.isdigit()))))
            all_pins = ','.join(
             sorted(path_temp,
                    key=lambda number:
                    int(''.join(k for k in number if k.isdigit()))))

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
