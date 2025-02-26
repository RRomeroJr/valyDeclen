import sqlite3
from valy_db import g_conn_cursor
import sys
import os
from typing import Iterable
# region Maps and Collections
case_map = {"Nominative": "nom", "Accusative": "acc", "Genitive": "gen", "Dative": "dat", "Locative": "loc",
"Instrumental": "ins", "Comitative": "com", "Vocative":"voc" }
# quant_map = {"Singular": "sing", "Plural": "pl", "Paucal": "pau", "Collective": "col"}
quant_map = {"Singular": "sing", "Plural": "pl"}
field_names = ['acc_sing', 'gen_sing', 'dat_sing', 'loc_sing', 'ins_sing', 'com_sing', 'voc_sing', 'nom_pl', 'acc_pl', 'gen_pl', 'dat_pl', 'loc_pl', 'ins_pl', 'com_pl', 'voc_pl']
# endregion
def get_form(base_word:str, field_name: str) -> str:
    conn, cursor = g_conn_cursor()
    res: str = conn.execute(f"selct from word_forms({field_name}) where nom_sing = ?", (base_word,)).fetchone()
    cursor.close()
    conn.close()
    return res
def field_map(case: str, quant: str) -> str:
    return f"{case_map[case]}_{quant_map[quant]}"

def g_word_form_q(form_to_test):
     return f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON word_forms.nom_sing = word_info.word"""
def g_from_w_endings(form_to_test: str, endings: Iterable):
     placeholders = " OR ".join([f"nom_sing LIKE ?"] * len(endings))
     return f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON nom_sing = word WHERE {placeholders}"""

''' # Ex for geting only 3rd declen
declen_to_test = "3rd"
res = conn.execute(f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON word_forms.nom_sing = word_info.word WHERE word_info.declen = '{declen_to_test}'""").fetchall()
'''
import rrjr.rrjr_fm as rrjr_fm
import csv
import random
import time
import math

# region Game Init
failed_file_name = rrjr_fm.g_seq_filename("learning_log/failed/failed_forms.txt")
with open(failed_file_name, "a", newline='', encoding="UTF-8") as f:
        wr = csv.writer(f, delimiter='\t')
        wr.writerow(('base', 'form', 'declen#', 'declen', 'resp', 'time'))

resp = None
time_max = 120
count = 1
test_max = 9
endings = ('%ir', '%i', '%is')
#endregion

_ = input("Valyrian Declen test " +
(f"({test_max})" if test_max > 0 else "(endless)") + "\nAny to start!")

while (test_max < 1 or count <= test_max): # Game Loop
    #region Query DB
    conn, cursor = g_conn_cursor()
    form_to_test = random.choice(field_names)
    res = conn.execute(g_from_w_endings(form_to_test, endings), endings).fetchall()
    cursor.close()
    conn.close()
    #endregion
    os.system('cls' if os.name == 'nt' else 'clear')
    random_entry = random.choice(res)

    start = time.time()
    resp = input(f"What is the {form_to_test} of {random_entry[0]}?\n")
    stop = time.time()
    elspd_time = round(stop - start, 2)
    if elspd_time > time_max: # don't log time if too long
         elspd_time = -1
    if not (resp != "/quit" and resp != "/q"):
        break
    if resp == random_entry[1]:
        print("CORRECT!")
    else:
        print("FAILURE")
        # Log incorrects
        with open(failed_file_name, "a", newline='', encoding="UTF-8") as f:
            wr = csv.writer(f, delimiter='\t')
            wr.writerow(random_entry + (form_to_test, resp, elspd_time) )
    
    print(f" ans: {random_entry[1]}")
    input("Any to conintue" + (f" ({count}/{test_max}).." if test_max > 0 else ".."))
    count += 1