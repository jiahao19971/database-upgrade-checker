from dotenv import load_dotenv
import os
from tunnel.tunnel import Tunneler
from db.db import DBLoader

load_dotenv()
DATABASE=os.environ['DATABASE']
NEW_INSTANCE=os.environ['NEW_INSTANCE']

def main():
    to_arr_server = NEW_INSTANCE.split(",")
    for servers in to_arr_server:
        server = Tunneler(servers, 5432)

        server = server.connect()

        server.start()

        conn = DBLoader(server, DATABASE)
        conn = conn.connect()

        create_iam_user = os.environ['CREATE_USER']

        cur = conn.cursor()
        user_checker = f"SELECT count(*) FROM pg_catalog.pg_user WHERE usename = '{create_iam_user}';"

        cur.execute(user_checker)
        data = cur.fetchall()

        if data[0][0] != 1:
            create_user = f"CREATE USER {create_iam_user} WITH LOGIN CREATEDB CREATEROLE;"
            grant_iam = f"GRANT rds_iam TO {create_iam_user};"
            grant_superuser = f"GRANT rds_superuser TO {create_iam_user};"

            cur.execute(create_user)
            cur.execute(grant_iam)
            cur.execute(grant_superuser)
            print("Created IAM USER")
        else:
            print(f"User {create_iam_user} exist")

        user = f"""SELECT r.rolname, r.rolcreaterole, r.rolcreatedb, r.rolcanlogin,
                    ARRAY(SELECT b.rolname
                        FROM pg_catalog.pg_auth_members m
                        JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
                        WHERE m.member = r.oid) as memberof
                FROM pg_catalog.pg_roles r
                WHERE r.rolname = '{create_iam_user}' 
                ORDER BY 1;
            """
        cur.execute(user)
        user_data = cur.fetchall()
        print(f"Username: {user_data[0][0]}")
        print(f"Create Role: {user_data[0][1]}")
        print(f"Create DB: {user_data[0][2]}")
        print(f"Can Login: {user_data[0][3]}")
        print(f"Member of: {user_data[0][4]}")

        cur.close()
        conn.commit()

if __name__ == "__main__":
    main()