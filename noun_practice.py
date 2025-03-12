import sqlite3
from valy_db import g_conn_cursor
import sys
import os
from typing import Iterable, Callable
import rrjr.rrjr_fm as rrjr_fm
import csv
import random
import time
import math
import valy_stats
conn, cursor = g_conn_cursor()

# region Maps and Collections
case_map = {"Nominative": "nom", "Accusative": "acc", "Genitive": "gen", "Dative": "dat", "Locative": "loc",
"Instrumental": "ins", "Comitative": "com", "Vocative":"voc" }
# full_quant_map = {"Singular": "sing", "Plural": "pl", "Paucal": "pau", "Collective": "col"}
quant_map = {"Singular": "sing", "Plural": "pl"}
field_names = ['acc_sing', 'gen_sing', 'dat_sing', 'loc_sing', 'ins_sing', 'com_sing', 'voc_sing', 'nom_pl', 'acc_pl', 'gen_pl', 'dat_pl', 'loc_pl', 'ins_pl', 'com_pl', 'voc_pl']
cases: tuple[tuple[str, int]] = tuple(e[0] for e in cursor.execute("Select name from cases Where name != 'adv'"))
quants: tuple[tuple[str, int]] = tuple(e[0] for e in cursor.execute(
    """Select name from quants 
    Where name = 'sing'
    Or name = 'pl'"""))
declens: tuple[tuple[str, int]] = tuple(e[0] for e in cursor.execute(
    """Select name from declens"""))
options_map = {'cases': cases, 'quants': quants, 'declens':declens}
# endregion
def get_form(base_word:str, field_name: str) -> str:
    res: str = cursor.execute(f"selct from word_forms({field_name}) where nom_sing = ?", (base_word,)).fetchone()
    return res
def field_map(case: str, quant: str) -> str:
    return f"{case_map[case]}_{quant_map[quant]}"

def g_word_form_q(form_to_test):
     return f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON word_forms.nom_sing = word_info.word"""

def g_from_w_endings(form_to_test: str, endings: Iterable):
     placeholders = " OR ".join([f"nom_sing LIKE ?"] * len(endings))
     return f"""SELECT wf.nom_sing, wf.{form_to_test}, wi.declen FROM word_forms as wf
INNER JOIN word_info wi ON nom_sing = word WHERE {placeholders}"""
word_form_query_noun = """
Select n.base, nf.form, n.declen,'noun', nf.id
From noun_forms nf
Inner Join nouns n On nf.noun_id = n.id
Where nf.g_case = ?
And nf.quant = ?
And n.declen = ?"""

''' # Ex for geting only 3rd declen
declen_to_test = "3rd"
res = conn.execute(f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON word_forms.nom_sing = word_info.word WHERE word_info.declen = '{declen_to_test}'""").fetchall()
'''



# region Game Init
save_changes = True
resp = None
time_max = 120
test_max = 9
endings = None
# endings = ('%ir', '%i', '%is')
params = (("endings", endings), ("field_names", field_names))
failed_file_name = None
def get_failed_file():
    global failed_file_name
    if not failed_file_name:
        failed_file_name = rrjr_fm.g_seq_filename("learning_log/failed/failed_forms.txt")
        f = open(failed_file_name, "a", newline='', encoding="UTF-8")
        wr = csv.writer(f, delimiter='\t')
        wr.writerow(params)
        wr.writerow(('base', 'form', 'declen#', 'declen', 'resp', 'time'))
    else:
        f = open(failed_file_name, "a", newline='', encoding="UTF-8")
    return f
#endregion

_ = input("Valyrian Declen test " +
(f"({test_max})" if test_max > 0 else "(endless)") + "\nAny to start!")

count = 1
while (test_max < 1 or count <= test_max): # Game Loop
    
    #region Query DB
    # case_quant = random.choice(field_names)
    # form_tup = (random.choice(cases)[1], random.choice(quants)[1])
    _case = None
    quant = None
    prompt_keys_to_opts_key = {'case':'cases', 'quant':'quants', 'declen':'declens'}
    prompt_args = {'case':None, 'quant':None, 'declen':None}
    for pa in prompt_args.keys():
        r_list = valy_stats.find_worst(pa)
        opts = options_map[prompt_keys_to_opts_key[pa]]
        skipped = False
        for _r in r_list:
            if _r[0] in opts:
                prompt_args[pa] = _r[0]
                print('set', pa, ':', prompt_args[pa])
                break
            else:
                print(f'{pa} skipping {_r[0]}')
                if not skipped:
                    skipped = True
        if skipped:
            print(f'opts: {opts}')
        assert prompt_args[pa] != None, f"prompt arg {pa} could not find valid arg"

    form_tup = tuple(prompt_args.values())
    print('form_tup', form_tup)
    
    case_quant = f"{prompt_args['case']}_{prompt_args['quant']}"
    print("case_quant", case_quant, 'declen')
    if False:
        res: list[str] = cursor.execute(g_from_w_endings(case_quant, endings), endings).fetchall()
    else:
        res: tuple[str, str, str] = cursor.execute(word_form_query_noun, form_tup).fetchall()
        # print(res)
        # input("Any to continue..")

    #endregion
    scroll_amt = os.get_terminal_size().lines -1
    print("\n" * scroll_amt + f"\033[{scroll_amt}A", end='')
    # os.system('cls' if os.name == 'nt' else 'clear')
    random_entry = random.choice(res)
    # print(random_entry)
    start = time.time()
    resp = input(f"What is the {case_quant} of {random_entry[0]}?\n")
    stop = time.time()
    elspd_time = round(stop - start, 2)
    if elspd_time > time_max: # don't log time if too long
         elspd_time = None
    if not (resp != "/quit" and resp != "/q"):
        break
    if resp.lower() == random_entry[1].lower():
        # valy_stats.log_stats_noun(*word_args, True)
        passed = True
        print("CORRECT!")
    else:
        passed = False
        # valy_stats.log_stats_noun(*word_args, False)
        print("FAILURE")
        # Log incorrects
    print(f" ans: {random_entry[1]}")
    valy_stats.add_response(random_entry[-1], resp, random_entry[-2], passed, elspd_time)
    input("Any to conintue" + (f" ({count}/{test_max}).." if test_max > 0 else ".."))
    count += 1
if(save_changes):
    conn.commit()
cursor.close()
conn.close()