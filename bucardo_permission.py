from dotenv import load_dotenv
import os, sys
from tunnel.tunnel import Tunneler
from db.db import DBLoader

load_dotenv()
OLD_INSTANCE=os.environ['OLD_INSTANCE']
DATABASE=os.environ['DATABASE']

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

create_fn = """
    CREATE OR REPLACE FUNCTION public.rds_session_replication_role(role text)
    RETURNS text
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $function$
            DECLARE
                    curr_val text := 'unset';
            BEGIN
                    EXECUTE 'SET session_replication_role = ' || quote_literal(role);
                    EXECUTE 'SHOW session_replication_role' INTO curr_val;
                    RETURN curr_val;
            END
    $function$;
"""

revoke_fn_public = "revoke all on function rds_session_replication_role(text) from public;"

grant_replication_role = "grant execute on function rds_session_replication_role(text) to rds_superuser;"

grant_postgres_superuser = "grant rds_superuser to postgres;"

def main():
    server = Tunneler(OLD_INSTANCE, 5432)

    server = server.connect()

    server.start()

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = DBLoader(server, database)
        conn = conn.connect()
        
        cur = conn.cursor()

        cur.execute(create_fn)

        conn.commit()
        cur.execute(revoke_fn_public)
        conn.commit()

        cur.execute(grant_replication_role)
        conn.commit()

        cur.execute(grant_postgres_superuser)
        conn.commit()

        conn.close()

if __name__ == "__main__":
    main()