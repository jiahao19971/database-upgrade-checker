from dotenv import load_dotenv
import os, sys
from tunnel.tunnel import Tunneler
from db.db import DBLoader


load_dotenv()
DATABASE=os.environ['DATABASE']
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

def main():
    server = Tunneler(OLD_INSTANCE, 5432)

    server = server.connect()

    server.start()

    server2 = Tunneler(NEW_INSTANCE, 5432)

    server2 = server2.connect()

    server2.start()

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = DBLoader(server, database)
        conn = conn.connect()
        conn2 = DBLoader(server2, database)
        conn2 = conn2.connect()

        cur = conn.cursor()
        cur2 = conn2.cursor()

        table_size_checker = """
                                select
                                    table_schema,
                                    table_name,
                                    pg_total_relation_size('"'||table_schema||'"."'||table_name||'"')
                                from information_schema.tables
                                where table_schema NOT LIKE 'pg_%' AND table_schema != 'bucardo' AND table_schema != 'information_schema' AND table_name not like 'pg%';
                            """

        cur.execute(table_size_checker)
        cur2.execute(table_size_checker)

        table_size = cur.fetchall()
        table_size2 = cur2.fetchall()

        for table in table_size:
            for table2 in table_size2:
                if table[0] == table2[0] and table[1] == table2[1]:
                    if table[2] != table2[2]:
                        print(f"incorrect data size for schema: {table[0]}, table: {table[1]}")   

                        count_table = f'SELECT count(*) FROM "{table[0]}"."{table[1]}"'
                        try:
                            cur.execute(count_table)
                            cur2.execute(count_table)

                            table_count = cur.fetchall()
                            table_count2 = cur2.fetchall()

                            if table_count[0][0] != table_count2[0][0]:
                                print(f'something is wrong with table: "{table[0]}"."{table[1]}"') 
                            else:
                                print(f'nothing wrong with table: "{table[0]}"."{table[1]}" after checking on count')   
                        except Exception as err:
                            print(err)

        # for table in table_size:
        #     index_size = f'SELECT pg_indexes_size("{table[0]}"."{table[1]}")'

        #     cur.execute(index_size)
        #     cur2.execute(index_size)

        #     index_count = cur.fetchall()
        #     index_count2 = cur2.fetchall()

        #     print(index_count)
        #     print(index_count2)

        
    cur.close()
    cur2.close()
    conn.commit()
    conn2.commit()

if __name__ == "__main__":
    main()