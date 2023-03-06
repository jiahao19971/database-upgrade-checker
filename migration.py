from dotenv import load_dotenv
import os, sys
from tunnel.tunnel import Tunneler
from db.db import DBLoader

load_dotenv()
DATABASE=os.environ['DATABASE']
OLD_INSTANCE=os.environ['OLD_INSTANCE']

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

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = DBLoader(server, database)
        conn = conn.connect()

        cur = conn.cursor()

        ## Query
        query_count = "select nspname from pg_catalog.pg_namespace where nspname not like 'pg%';"
        # query_count = "select count(*) from pg_indexes where tablename not like  'pg%';"
        cur.execute(query_count)

        ## Fetch Data
        data = cur.fetchall()

        for schema in data:
            if schema[0] != "information_schema" and schema[0] != "shared_extensions":
                create_pkey = f"ALTER TABLE \"{schema[0]}\".companies_hubspot_deal_submissions ADD COLUMN id SERIAL PRIMARY KEY;"

                try:
                    cur.execute(create_pkey)
                except Exception as err:
                    print(err)
                    conn.rollback()  
                conn.commit()


                chg_name = f'ALTER TABLE \"{schema[0]}\".finance_merchant_payment_request_transactions rename to "finance_merchant_payment_request_transaction"'

                try:
                    cur.execute(chg_name)
                except Exception as err:
                    print(err)
                    conn.rollback()  
                conn.commit()

        conn.commit()

if __name__ == "__main__":
    main()


                
