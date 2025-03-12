import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_printing import pr_separate
import sqlite3
from typing import Any, Sequence
from enum import Enum, auto


case_map = {"Nominative": "nom", "Accusative": "acc", "Genitive": "gen", "Dative": "dat", "Locative": "loc",
"Instrumental": "ins", "Comitative": "com", "Vocative":"voc" }
quant_map = {"Singular": "sing", "Plural": "pl", "Paucal": "pau", "Collective": "col"}
declen_map = {"first":"1st", "second":"2nd", "third":"3rd", "fourth":"4th", "fifth":"5th", "sixth":"6th"}
gender_map = {"lunar":"lun", "solar":"sol", "terrestrial":"ter", "aquatic":"aq"}
initialized = False
field_names = [f"{cs}_{qs}" for qs in quant_map.values() for cs in case_map.values()]
conn: sqlite3.Connection = None
cursor: sqlite3.Cursor = None
class Commit_Modes(Enum):
    ENABLED = auto()
    ROLLBACK = auto()
    IGNORE = auto()
__commit_mode = Commit_Modes.ROLLBACK
def s_commit_mode(inp: str|Commit_Modes):
    global __commit_mode
    if isinstance(inp, str):
        found = False
        for cm in Commit_Modes:
            if inp == cm.name:
                __commit_mode = cm
                found = True
        if not found:
            raise Exception(f"{inp} is not a value commit mode.")
    elif isinstance(inp, Commit_Modes):
        __commit_mode = inp
    else:
        raise Exception(f'Invalid type sent to valy_db.s_commit_mode {type(inp)}')
    print(f'Valy db set to {__commit_mode}') 
        

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

def add_adj_to_db(word: str, adj_class: int, forms = set[tuple[str, str, str, str, str, str]]) -> int:
    """Returns back adj_id"""
    #tuple looks like (word_form, d_type, position, gender, quantity, case)
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute("INSERT INTO adjs(base, class) VALUES(?,?)", (word, adj_class))
    adj_id = cursor.lastrowid
    for f in forms:
        assert len(cursor.execute("Select * From adjs Where id = ?", (adj_id,)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From adj_d_types Where name = ?", (f[1],)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From adj_positions Where name = ?", (f[2],)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From genders Where name = ?", (f[3],)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From quants Where name = ?", (f[4],)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From cases Where name = ?", (f[5],)).fetchall()) == 1, f
    cursor.executemany(f"""INSERT INTO adj_forms
    (form, adj_id, d_type, pos, gender, quant, g_case) VALUES(?, {adj_id}, ?, ?, ?, ?, ?)""", forms)
    print("add adj to db end")
    return adj_id
def add_noun_to_db(word: str, declen: str, gender: str, forms = set[tuple[str, str, str]]) -> int:
    """Returns back noun_id"""
    #tuple looks like (word_form, quantity, case)
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute("INSERT INTO nouns(base, declen, gender) VALUES(?, ?, ?)", (word, declen, gender))
    noun_id = cursor.lastrowid
    for f in forms:
        assert len(cursor.execute("Select * From nouns Where id = ?", (noun_id,)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From quants Where name = ?", (f[1],)).fetchall()) == 1, f
        assert len(cursor.execute("Select * From cases Where name = ?", (f[2],)).fetchall()) == 1, f

    cursor.executemany(f"""INSERT INTO noun_forms
    (noun_id, form, quant, g_case) VALUES({noun_id}, ?, ?, ?)""", forms)
    print("add noun to db end")
    return noun_id
def g_sql(table_name):
    r = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';").fetchone()
    return r[0] if r else None

def commit():
    # print('__commit_mode', __commit_mode)
    if(__commit_mode == Commit_Modes.ENABLED):
        print("Commiting database")
        conn.commit()
    elif(__commit_mode == Commit_Modes.IGNORE):
        print(f"Commit mode {__commit_mode.name}. Ignoring call to commit")
    else:
        print(f'valy_db.commit() called but __commit_mode not ENABLED. Rolling back..\n __commit_mode == {__commit_mode.name}')
        conn.rollback()
def rollback():
    conn.rollback()

