# import sqlite3

# conn = sqlite3.connect("valy.sqlite3")
# cursor = conn.cursor()
# # cursor.execute("PRAGMA table_info(word_forms)")
# # schema = cursor.fetchall()

# # for column in schema:
# #     print(column)
# # cursor.execute("SELECT COUNT(*) FROM word_forms")
# # count = cursor.fetchone()[0]
# # print(f"Number of rows in word_forms: {count}")
# # res = cursor.execute("select * from word_forms").fetchone()
# # print(len(res))
# # print(res)
# conn.close()

import valy_db
from valy_db import g_conn_cursor
import sqlite3
from rrjr.rrjr_printing import pr_separate
from typing import Iterator
import os
conn, cursor = g_conn_cursor()

# print("word_forms:" + "\n " + "\n ".join([str(tup) for tup in valy_db.get_schema(conn, "word_forms")]))
# pr_separate()
# print("word_info:" + "\n " + "\n ".join([str(tup) for tup in valy_db.get_schema(conn, "word_info")]))
""" get word froms that aren't pau or col
field_names = [x[1] for x in valy_db.get_schema(conn, "word_forms") if ("pau" not in x[1] and "col" not in x[1])]
print(field_names)"""

# print("word_forms:" + "\n " + "\n ".join([f"len: {len(tup)}: {tup}" for tup in conn.execute("select * from word_forms").fetchall()]))
# res = conn.execute("select * from word_info").fetchall()
# print(f"word_info: " + "\n " + "\n ".join([f"len: {len(tup)}: {tup}" for tup in res]))
# print(f"{len(res)} items")
# print("Looking for ñāqes:" + "\n " + 
#     "\n ".join([f"len: {len(tup)}: {tup}" for tup in conn.execute("select * from word_info where word = ?", ("ñāqes",)).fetchall()]))

# print(f"join res: " + "\n " + "\n ".join([f"len: {len(tup)}: {tup}" for tup in res]))
# print(f"{len(res)} items")

def g_word_form_q(form_to_test: str, endings: list,):
     placeholders = " OR ".join([f"nom_sing LIKE ?"] * len(endings))
     return f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON nom_sing = word WHERE {placeholders}"""
endings = ('%ir', '%i', '%is')
res = conn.execute(g_word_form_q("acc_pl", endings), endings).fetchall()
print(res)

cursor.close()
conn.close()