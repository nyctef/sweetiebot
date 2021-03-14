from os import getenv
import psycopg2

pg_conn_str = getenv("SB_PG_DB", None)
if not pg_conn_str:
    raise Exception("SB_PG_DB needs to be set")

conn = psycopg2.connect(pg_conn_str)
cur = conn.cursor()


def upload_file(path, table_name):
    sql = f"INSERT INTO {table_name}(text) VALUES (%s) ON CONFLICT (text) DO NOTHING"
    with open(path, "r", encoding="utf8") as f:
        for line in f.readlines():
            cur.execute(sql, (line.strip(),))


if __name__ == "__main__":
    upload_file("./data/deowl_fails.txt", "deowl_fails")
    upload_file("./data/actions.txt", "actions")
    upload_file("./data/cadmusic.txt", "cadmusic")
    upload_file("./data/sass.txt", "sass")

    conn.commit()
    cur.close()
    conn.close()
