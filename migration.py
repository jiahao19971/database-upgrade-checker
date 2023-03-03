from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os, io
import paramiko
import psycopg2, json, sys

load_dotenv()
REMOTE_HOST=os.environ['REMOTE_HOST']
REMOTE_PORT=int(os.environ['REMOTE_PORT'])
REMOTE_USERNAME=os.environ['REMOTE_USERNAME']
REMOTE_KEY=os.environ['REMOTE_KEY']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PWD=os.environ['PASSWORD']
OLD_INSTANCE=os.environ['OLD_INSTANCE']
NEW_INSTANCE=os.environ['NEW_INSTANCE']

def print_psycopg2_exception(err):
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print ("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    print ("\nextensions.Diagnostics:", err.diag)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")


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

    server2 = SSHTunnelForwarder(
        (REMOTE_HOST, 22), 
        ssh_username=REMOTE_USERNAME, 
        ssh_pkey=pkey, 
        host_pkey_directories="./",
        allow_agent=False,
        remote_bind_address=(NEW_INSTANCE, 5432), 
        local_bind_address=('localhost', 3456)
    )
    server2.start()

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = psycopg2.connect(
            database=database,
            user=USERNAME,
            host=server.local_bind_host,
            port=server.local_bind_port,
            password=PWD
        )
        conn2 = psycopg2.connect(
            database=database,
            user=USERNAME,
            host=server2.local_bind_host,
            port=server2.local_bind_port,
            password=PWD
        )

        cur = conn.cursor()
        cur2 = conn2.cursor()

        ## Query
        query_count = "select nspname from pg_catalog.pg_namespace where nspname not like 'pg%';"
        # query_count = "select count(*) from pg_indexes where tablename not like  'pg%';"
        cur.execute(query_count)
        cur2.execute(query_count)

        ## Fetch Data
        data = cur.fetchall()
        data2 = cur2.fetchall()

        for schema in data:
            if schema[0] != "information_schema" and schema[0] != "shared_extensions":
                create_pkey = f"ALTER TABLE \"{schema[0]}\".companies_hubspot_deal_submissions ADD COLUMN id SERIAL PRIMARY KEY;"

                try:
                    cur.execute(create_pkey)
                    cur2.execute(create_pkey)
                except Exception as err:
                    print(err)
                    conn.rollback()  
                conn.commit()
                conn2.commit()


                chg_name = f'ALTER TABLE \"{schema[0]}\".finance_merchant_payment_request_transactions rename to "finance_merchant_payment_request_transaction"'

                try:
                    cur.execute(chg_name)
                    cur2.execute(chg_name)
                except Exception as err:
                    print(err)
                    conn.rollback()  
                conn.commit()
                conn2.commit()

        conn.commit()
        conn2.commit()



                
