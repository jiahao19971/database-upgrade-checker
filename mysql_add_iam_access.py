import mysql.connector
from dotenv import load_dotenv
import os, mariadb
from tunnel.tunnel import Tunneler
from db.db import DBLoader

load_dotenv()
DATABASE=os.environ['DATABASE']
NEW_INSTANCE=os.environ['NEW_INSTANCE']

def main():
    to_arr_server = NEW_INSTANCE.split(",")
    for servers in to_arr_server:
        server = Tunneler(servers, 3306)

        server = server.connect()

        server.start()

        db = DBLoader(server, DATABASE)

        cnx = mysql.connector.connect(
                            user=db._get_database_username(), 
                            password=db._get_database_password(),
                            host=server.local_bind_host,
                            port=server.local_bind_port,
                            database=DATABASE)
        
        # cnx = mariadb.connect(
        #     user=db._get_database_username(), 
        #     password=db._get_database_password(),
        #     host=server.local_bind_host,
        #     port=server.local_bind_port,
        #     database=DATABASE
        # )
        
        cursor = cnx.cursor()

        create_iam_user = os.environ['CREATE_USER']

        query = f"SELECT count(*) FROM user WHERE User='{create_iam_user}';"

        cursor.execute(query)
        
        data = cursor.fetchall()

        if data[0][0] != 1:
            show_grant = 'SHOW GRANTS FOR root;'
            

            cursor.execute(show_grant)
            grant = cursor.fetchall()

            create_user = f"CREATE USER {create_iam_user} IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';"
            grant_superuser = grant[0][0].replace('root', create_iam_user)

            cursor.execute(create_user)
            cursor.execute(grant_superuser)
            print("Created IAM USER")
        else:
            print(f"User {create_iam_user} exist")

        query = f"SELECT * FROM user WHERE User='{create_iam_user}';"

        cursor.execute(query)
        
        data = cursor.fetchall()

        column_name = cursor.column_names

        for idx, col in enumerate(column_name):
            print(f"{col}: {data[0][idx]}")

if __name__ == "__main__":
    main()