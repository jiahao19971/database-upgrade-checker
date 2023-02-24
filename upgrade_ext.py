from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os, io
import paramiko
import psycopg2, json

load_dotenv()
REMOTE_HOST=os.environ['REMOTE_HOST']
REMOTE_USERNAME=os.environ['REMOTE_USERNAME']
REMOTE_KEY=os.environ['REMOTE_KEY']
DATABASE=os.environ['DATABASE']
USERNAME=os.environ['USERNAME']
PWD=os.environ['PASSWORD']
NEW_INSTANCE=os.environ['NEW_INSTANCE']


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
        remote_bind_address=(NEW_INSTANCE, 5432), 
        local_bind_address=('localhost', 3456)
    )
    server.start()

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = psycopg2.connect(
            database=database,
            user=USERNAME,
            host=server.local_bind_host,
            port=server.local_bind_port,
            password=PWD
        )

        cur = conn.cursor()
        extension_checker = "SELECT b.name, b.default_version, a.extversion as installed_version FROM pg_extension a left join pg_available_extensions b on b.name = a.extname;"

        cur.execute(extension_checker)
        data = cur.fetchall()

        for ext in data:
            if ext[1] != ext[2]:
                print(f"extension upgrade needed for {ext[0]}")
                
                extension_upgrader = f"ALTER EXTENSION {ext[0]} UPDATE TO '{ext[1]}';"
                print(f"{ext[0]} to {ext[1]}")
                cur.execute(extension_upgrader)

        cur.close()
        conn.commit()




