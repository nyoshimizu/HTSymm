"""
Convert text file databases into SQLite databases to be used by all other modules. Uses SQLite3 via SQLAlchemy.
"""

from sqlalchemy import *
from db.loadverilog import *


def convert_verilog_SQLite(circuit):
    """
    Convert verilog text data into SQLite.

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

    conn.execute(input_pins.insert(), insert)

    output_pins_sorted = verilog_db.output_pins_sorted()

    insert_SQL = []
    for pin in output_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'output_pin': pin
                        }]

    conn.execute(output_pins.insert(), insert)

    node_pins_sorted = verilog_db.node_pins_sorted()

    insert_SQL = []
    for pin in node_pins_sorted:
        insert_SQL += [{'circuit': circuit,
                        'node_pin': pin
                        }]

    conn.execute(node_pins.insert(), insert)

    insert_SQL = []
    for pin in node_pins_sorted + output_pins_sorted:
        for inpin in verilog_db.gates.db[pin].input_pin:
            insert_SQL += [{'circuit': circuit,
                            'gate': verilog_db.gates.db[pin].gate,
                            'output_pin': pin,
                            'input_pin': inpin
                            }]

    conn.execute(gates.insert(), insert)

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

