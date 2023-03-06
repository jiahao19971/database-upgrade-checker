from dotenv import load_dotenv
import os
from tunnel.tunnel import Tunneler
from db.db import DBLoader

load_dotenv()
DATABASE=os.environ['DATABASE']
NEW_INSTANCE=os.environ['NEW_INSTANCE']

def main():
    server = Tunneler(NEW_INSTANCE, 5432)

    server = server.connect()

    server.start()

    to_arr_db = DATABASE.split(",")

    for database in to_arr_db:
        conn = DBLoader(server, database)
        conn = conn.connect()

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

if __name__ == "__main__":
    main()