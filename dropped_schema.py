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

        create_drop = "select format('DROP TRIGGER %I ON %I;', tgname, tgrelid::regclass) from pg_trigger where tgname like 'bucardo_%';"

        cur.execute(create_drop)

        data = cur.fetchall()

        arr = []

        for i in data:
            arr.append(i[0])

        for z in arr:
            test = z.replace("\";", ";")
            newt = test.replace(".", "\".")
            up = newt.replace("\"\"\"", "\"")

            cur.execute(up)

        cur.close()
        conn.commit()

if __name__ == "__main__":
    main()