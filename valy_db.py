import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_printing import pr_separate
import sqlite3
from typing import Any, Sequence


case_map = {"Nominative": "nom", "Accusative": "acc", "Genitive": "gen", "Dative": "dat", "Locative": "loc",
"Instrumental": "ins", "Comitative": "com", "Vocative":"voc" }
quant_map = {"Singular": "sing", "Plural": "pl", "Paucal": "pau", "Collective": "col"}
declen_map = {"first":"1st", "second":"2nd", "third":"3rd", "fourth":"4th", "fifth":"5th", "sixth":"6th"}
gender_map = {"lunar":"lun", "solar":"sol", "terrestrial":"ter", "aquatic":"aq"}
initialized = False
field_names = [f"{cs}_{qs}" for qs in quant_map.values() for cs in case_map.values()]
conn: sqlite3.Connection = None
cursor: sqlite3.Cursor = None
def g_conn_cursor():
    global conn, cursor, initialized
    if not initialized:
        init()
    return conn, cursor
def s_conn(_conn: sqlite3.Connection):
    global conn
    global cursor
    conn = _conn
    cursor = conn.cursor()
def init(reinit = False):
    global conn, cursor, initialized
    if initialized and not reinit:
        if conn or cursor:
            print("Warning re-initing valy_db. Things pointing to valy_db's conn/ cursor will now be different from valy_db's conn/ cursor.")
        return
    conn= sqlite3.connect("valy.sqlite3")
    cursor = conn.cursor()
    """Apparently SQLite doesn't enforce foreign keys
    vv by default. Which is very cool :). vv"""
    cursor.execute("PRAGMA foreign_keys = ON;")
    initialized = True
    print("Valy DB init'd")
def create_words_forms_table():
    data_type = "VARCHAR(30)"
    create_params = [field_names[0] + f" {data_type}" + " PRIMARY KEY"]
    for i, fn in enumerate(field_names):
        if i == 0:
            continue
        create_params.append(f"{fn} {data_type}")
    print(create_params)

    cursor.execute("create table word_forms({})".format(", ".join(create_params)))
    log_schema(conn, "word_forms")


def enter_to_word_forms(entry: dict[dict[str]]):

    entry_dict: dict[str, dict[str, str]] = entry["forms"]
    key = "nom_sing"
    k_val = entry["forms"]["Singular"]["Nominative"]
    create_query = "insert into word_forms ({}) VALUES (?)".format(key)
    conn.commit()
    cursor.execute(create_query, (k_val,))
    for quant_name, quant_dict in entry_dict.items():
        for case_name, case_val in quant_dict.items():
            field_name = f"{case_map[case_name]}_{quant_map[quant_name]}"
            data = case_val
            if field_name == key:
                continue
            update_query = "UPDATE word_forms SET {} = ? WHERE {} = ?".format(field_name, key)
            cursor.execute(update_query, (data, k_val))
    conn.commit()


def enter_to_word_info(entry: list[dict[str]]):

    q_tuple = (entry["word"], declen_map[entry["declen"]], gender_map[entry["gender"]])
    create_query = "insert into word_info (word, declen, gender) VALUES (?, ?, ?)"
    cursor.execute(create_query, (q_tuple))
    conn.commit()



def create_word_info_table():

    cursor.execute("create table word_info(word VARCHAR(30) PRIMARY KEY, declen TEXT, gender TEXT)")
    conn.commit()
    # loging
    log_schema(conn,"word_info")

def log_schema(conn, table_name):
    print(table_name + ": " + "\n" + " \n".join([str(tup) for tup in get_schema(conn, table_name)]))
    
def get_schema(conn: sqlite3.Connection, table_name: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    return schema
def enter_in_db(entry: dict[str]):
    enter_to_word_forms(entry)
    enter_to_word_forms(entry)
#endregion

# wikitables:list[bs4.element.Tag] = [tag for tag in mw_parser_output.find_all(class_="wikitable") if tag.get('class') == ['wikitable']]
# assert len(wikitables) > 0, """no wikitables found
#   url: {}""".format(url)

# with sp_open("mwpo", "w", encoding="UTF-8") as f:
#     f.write(mwpo.prettify())
