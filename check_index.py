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
        query_count = "select count(*) from pg_indexes where tablename not like  'pg%';"
        cur.execute(query_count)
        cur2.execute(query_count)

        ## Fetch Data
        data = cur.fetchall()
        data2 = cur2.fetchall()

        if data[0][0] != data2[0][0]:
            print(f"incorrect index for {database}")

            schema_check = "select schemaname, count(*) from pg_indexes where tablename not like  'pg%' group by schemaname order by schemaname;"
            cur.execute(schema_check)
            cur2.execute(schema_check)

            schema_data = cur.fetchall()
            schema_data2 = cur2.fetchall()

            incorrect_schema = []
            for schema in schema_data:
                search = [schema2 for schema2 in schema_data2 if schema[0] == schema2[0] and schema[1] != schema2[1]]

                if len(search) > 0:
                    incorrect_schema.append(search[0][0])

            createJson = []

            for schema in incorrect_schema:
                tablename_check = f"select tablename, count(*) from pg_indexes where tablename not like  'pg%' and schemaname = '{schema}' group by tablename order by tablename;"
                cur.execute(tablename_check)
                cur2.execute(tablename_check)

                table_data = cur.fetchall()
                table_data2 = cur2.fetchall()

                incorrect_table = []

                for table in table_data:
                    
                    search = [table2 for table2 in table_data2 if table[0] == table2[0] and table[1] != table2[1]]

                    if len(search) > 0:
                        incorrect_table.append(search[0][0])

                for table in incorrect_table:
                    index_checker = f"select indexname, indexdef from pg_indexes where tablename not like  'pg%' and schemaname = '{schema}' and tablename = '{table}';"
                    cur.execute(index_checker)
                    cur2.execute(index_checker)

                    index_data = cur.fetchall()
                    index_data2 = cur2.fetchall()

                    index = [[idx[0], idx[1]] for idx in index_data]
                    index2 = [[idx2[0], idx2[1]] for idx2 in index_data2]

                    missing_index = []
                    for idx in index:
                        if idx not in index2:
                            print(f"missing index {idx[0]} in schema: {schema}, table: {table}")
                            missing_index.append(idx)

                    failed_index = []
                    for indexes in missing_index:
                        print(f"Create missing index {indexes[0]}")
                        index_query = indexes[1]

                        

                        try:
                            cur2.execute(index_query)
                        except Exception as err:
                            # pass exception to function
                            print_psycopg2_exception(err)

                            failed = {
                                "name": indexes[0], 
                                "sql": indexes[1],
                                "error": str(err)
                            }

                            failed_index.append(failed)
                            # rollback the previous transaction before starting another
                            conn2.rollback()  

                            print()

                    createJson.append({
                        "database": database,
                        "schema": schema,
                        "table": table,
                        "missing_index": failed_index
                    })

                    createJson = [x for x in createJson if len(x['missing_index']) > 0]

            file_name = f"missing_index_{NEW_INSTANCE}.json"

            files = [f.name for f in os.scandir("./")]

            if file_name in files:
                with open(file_name, "r") as data:
                    data_file = json.loads(data.read())

                    for each in createJson:
                        data_file.append(each)

                    with open(f"missing_index_{NEW_INSTANCE}.json", "w") as missing_data:
                        json.dump(data_file, missing_data, ensure_ascii=False, indent=4)
            else:
                with open(f"missing_index_{NEW_INSTANCE}.json", "w") as missing_data:
                    json.dump(createJson, missing_data, ensure_ascii=False, indent=4)
        else:
            print(f'no index error found in {database}')

        cur.close()
        cur2.close()
        conn.commit()
        conn2.commit()