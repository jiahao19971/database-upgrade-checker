from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os, io
import paramiko
import psycopg2

load_dotenv()
REMOTE_HOST=os.environ['REMOTE_HOST']
REMOTE_USERNAME=os.environ['REMOTE_USERNAME']
REMOTE_KEY=os.environ['REMOTE_KEY']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PWD=os.environ['PASSWORD']
OLD_INSTANCE=os.environ['OLD_INSTANCE']

with open(REMOTE_KEY, "r") as key:
    SSH_KEY=key.read()

    # pass key to parmiko to get your pkey
    pkey = paramiko.RSAKey.from_private_key(io.StringIO(SSH_KEY))

    server = SSHTunnelForwarder(
        (REMOTE_HOST, 22), 
        ssh_username=REMOTE_USERNAME, 
        ssh_pkey=pkey, 
        host_pkey_directories="./",
        allow_agent=False,
        remote_bind_address=(OLD_INSTANCE, 5432), 
        local_bind_address=('localhost', 1234)
    )
    server.start()

    to_arr_db = DATABASE.split(",")

    database = to_arr_db[0]

    conn = psycopg2.connect(
        database=database,
        user=USERNAME,
        host=server.local_bind_host,
        port=server.local_bind_port,
        password=PWD
    )

    transaction_checker = "SELECT count(*) FROM pg_catalog.pg_prepared_xacts;"

    reg_checker = """
        SELECT count(*) FROM pg_catalog.pg_class c, pg_catalog.pg_namespace n, pg_catalog.pg_attribute a
            WHERE c.oid = a.attrelid
                AND NOT a.attisdropped
                AND a.atttypid IN ('pg_catalog.regproc'::pg_catalog.regtype,
                                    'pg_catalog.regprocedure'::pg_catalog.regtype,
                                    'pg_catalog.regoper'::pg_catalog.regtype,
                                    'pg_catalog.regoperator'::pg_catalog.regtype,
                                    'pg_catalog.regconfig'::pg_catalog.regtype,
                                    'pg_catalog.regdictionary'::pg_catalog.regtype)
                AND c.relnamespace = n.oid
                AND n.nspname NOT IN ('pg_catalog', 'information_schema');
    """

    replication_checker = "SELECT * FROM pg_replication_slots;"

    ## replication_found: drop it
    drop_replication = "SELECT pg_drop_replication_slot({slot_name});"

    unknown_data_type_checker = "SELECT DISTINCT data_type FROM information_schema.columns WHERE data_type ILIKE 'unknown';"

    show_all_db = "SELECT datname FROM pg_database WHERE datistemplate = false;"

    cur = conn.cursor()

    cur.execute(show_all_db)
    all_db = cur.fetchall()

    print(all_db)

    cur.execute(transaction_checker)
    transaction_count = cur.fetchall()

    if transaction_count[0][0] != 0:
        print("There is still transaction, please terminate and rollback the trx before proceeding")

    cur.execute(reg_checker)
    reg_count = cur.fetchall()

    if reg_count[0][0] != 0:
        print("There is still reg* being used, please drop reg* before attempting an upgrade")

    cur.execute(replication_checker)
    replication_count = cur.fetchall()

    if len(replication_count) > 0:
        print("Drop replication here")

        # cur.execute(replication_checker)
        # replication_count = cur.fetchall()

        # if len(replication_count) > 0:
        #     print("Drop replication failed please try again")

    cur.execute(unknown_data_type_checker)
    unknown_dtype = cur.fetchall()

    if len(unknown_dtype) > 0:
        print("Please remove unknown datatype")

    print("Checking completed")

    cur.close()
    conn.commit()

