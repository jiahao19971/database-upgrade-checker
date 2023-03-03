from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os, io
import paramiko
import psycopg2, json, sys, re

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

        get_all_tb = "select * from information_schema.tables where table_schema != 'bucardo' AND table_schema != 'information_schema' AND table_schema not like 'pg%' AND table_name not like 'pg%';"

        cur.execute(get_all_tb)
        cur2.execute(get_all_tb)

        tb = cur.fetchall()
        tb2 = cur2.fetchall()

        if len(tb) == len(tb2):
            print("Equal amount of table")

            for table in tb:
                count_table = f'SELECT count(*) FROM "{table[1]}"."{table[2]}";'

                cur.execute(count_table)
                cur2.execute(count_table)

                tb_count = cur.fetchall()
                tb_count2 = cur2.fetchall()

                if tb_count[0][0] != tb_count2[0][0]:
                    print(f'incorrect table count for "{table[1]}"."{table[2]}"')
                else:
                    print(f'Correct table count for "{table[1]}"."{table[2]}"')

        conn.commit()
        conn2.commit()
        cur.close()
        cur2.close()
    
            # for table in table_size:
            #     for table2 in table_size2:
                    # if table[0] == table2[0] and table[1] == table2[1]:
                    #     if table[2] != table2[2]:




    #     database_size_checker = f"select pg_size_pretty(pg_database_size('{database}'))"

    #     cur.execute(database_size_checker)
    #     cur2.execute(database_size_checker)

    #     database_size = cur.fetchall()
    #     database_size2 = cur2.fetchall()

    #     db_size = re.sub("[^0-9]", '', database_size[0][0])
    #     db_size2 = re.sub("[^0-9]", '', database_size2[0][0])
    #     if db_size != db_size2:
    #         print(f"checking table for {database} old: {db_size} vs new: {db_size2}")


    #         table_size_checker = """
    #                                 SELECT
    #                                     schema_name,
    #                                     relname,
    #                                     table_size

    #                                     FROM (
    #                                         SELECT
    #                                             pg_catalog.pg_namespace.nspname           AS schema_name,
    #                                             relname,
    #                                             pg_relation_size(pg_catalog.pg_class.oid) AS table_size

    #                                         FROM pg_catalog.pg_class
    #                                             JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid
    #                                         ) t
    #                                     WHERE schema_name NOT LIKE 'pg_%'
    #                                     ORDER BY table_size DESC;
    #                             """

    #         cur.execute(table_size_checker)
    #         cur2.execute(table_size_checker)

    #         table_size = cur.fetchall()
    #         table_size2 = cur2.fetchall()

    #         for table in table_size:
    #             for table2 in table_size2:
    #                 if table[0] == table2[0] and table[1] == table2[1]:
    #                     if table[2] != table2[2]:
    #                         print(f"incorrect data size for schema: {table[0]}, table: {table[1]}")                
           
    
    # conn.commit()
    # conn2.commit()