import sqlite3
from valy_db import g_conn_cursor
import sys
import os
from typing import Iterable, Callable
import rrjr_py.rrjr_fm as rrjr_fm
import csv
import random
import time
import math
import valy_stats
from typing import Any
conn, cursor = g_conn_cursor()

# region Maps and Collections
case_map = {"Nominative": "nom", "Accusative": "acc", "Genitive": "gen", "Dative": "dat", "Locative": "loc",
"Instrumental": "ins", "Comitative": "com", "Vocative":"voc" }
# full_quant_map = {"Singular": "sing", "Plural": "pl", "Paucal": "pau", "Collective": "col"}
quant_map = {"Singular": "sing", "Plural": "pl"}
field_names = ['acc_sing', 'gen_sing', 'dat_sing', 'loc_sing', 'ins_sing', 'com_sing', 'voc_sing', 'nom_pl', 'acc_pl', 'gen_pl', 'dat_pl', 'loc_pl', 'ins_pl', 'com_pl', 'voc_pl']
cases: tuple[str] = tuple(e[0] for e in cursor.execute("Select name from cases Where name != 'adv'"))
quants: tuple[str] = tuple(e[0] for e in cursor.execute(
    """Select name from quants 
    Where name = 'sing'
    Or name = 'pl'"""))
declens: tuple[str] = tuple(e[0] for e in cursor.execute(
    """Select name from declens"""))
d_types: tuple[str] = tuple(e[0] for e in cursor.execute("Select name From adj_d_types Where name = 'pos'").fetchall())
adj_genders: tuple[str] = tuple(e[0] for e in cursor.execute("Select name From genders").fetchall())
adj_quants: tuple[str] = tuple(e[0] for e in cursor.execute("Select name from quants where name = 'sing/col' Or name = 'pl/pau'").fetchall())
adj_cases: tuple[str] = tuple(e[0] for e in cursor.execute("Select name From cases Where name != 'adv'"))
positions: tuple[str] = tuple(e[0] for e in cursor.execute("Select name From adj_positions Where name = 'postpos'").fetchall())

options_map_nouns = {'cases': cases, 'quants': quants, 'declens':declens,}
options_map_adjs = {'cases': adj_cases, 'quants': adj_quants, 'd_types':d_types, 'positions': positions, 'genders': adj_genders}
options_map = {'noun': options_map_nouns, 'adj': options_map_adjs}
# endregion
def g_prompt_args_adj() -> dict[str,str]:
    global d_types, adj_genders, adj_quants, adj_cases, positions, options_map
    adj_opt_map = options_map['adj']
    prompt_keys_to_opts_key = {'g_case': 'cases', 'quant': 'quants', 'd_type': 'd_types', 'pos': 'positions', 'gender': 'genders'}
    prompt_args = {'d_type': None, 'pos': None, 'gender': None, 'g_case': None, 'quant': None}

    for pa in prompt_args.keys():
        r_list = valy_stats.find_worst3('adj', pa)
        opts = adj_opt_map[prompt_keys_to_opts_key[pa]]
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

    return prompt_args

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
def g_adj_form_q(d_type: str = None, pos: str = None, gender: str = None, g_case: str = None, quant: str = None, _class: str = None):
    word_form_q_adj = """
    Select a.base, af.form, a.class, 'adj', af.id
    From adj_forms af
    Inner Join adjs a On af.adj_id = a.id"""
    conds = []
    if d_type:
        conds.append(f"af.d_type = ?")
    if pos:
        conds.append(f"af.pos = ?")
    if gender:
        conds.append(f"af.gender = ?")
    if g_case:
        conds.append(f"af.g_case = ?")
    if quant:
        conds.append(f"af.quant = ?")
    if _class:
        conds.append(f"a._class = ?")
    if len(conds) > 0:
        word_form_q_adj += """
    Where """
        word_form_q_adj += f"""{conds[0]}""" 
        for i in range(1, len(conds)):
            word_form_q_adj += f"""
    And {conds[i]}"""

    print(word_form_q_adj)
    return word_form_q_adj

''' # Ex for geting only 3rd declen
declen_to_test = "3rd"
res = conn.execute(f"""SELECT word_forms.nom_sing, word_forms.{form_to_test}, word_info.declen FROM word_forms
INNER JOIN word_info ON word_forms.nom_sing = word_info.word WHERE word_info.declen = '{declen_to_test}'""").fetchall()
'''



# region Game Init
save_changes = False
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

    prompt_args_noun = None
    # prompt_args_noun = NYI
    form_tup_noun = None
    print('form_tup_noun', form_tup_noun)
    print(prompt_args_noun)

    # prompt_args_adj = None
    prompt_args_adj = g_prompt_args_adj()
    form_tup_adj = tuple(prompt_args_adj.values())
    print('form_tup_adj', form_tup_adj)
    print(prompt_args_adj)

    if False:
        res: list[str] = cursor.execute(g_from_w_endings(case_quant, endings), endings).fetchall()
    else:
        res_noun, res_adj = None, None
        if form_tup_noun:
            res_noun: list[tuple[str, str, Any, str, int]] = cursor.execute(word_form_query_noun, form_tup_noun).fetchall()
        elif form_tup_adj:
            res_adj: list[tuple[str, str, Any, str, int]] = cursor.execute(g_adj_form_q(*form_tup_adj), form_tup_adj).fetchall()
        res_tup = (res_noun, res_adj)
        res: list[tuple[str, str, Any, str, int]] = []
        for rt in res_tup:
            if rt:
                res.extend(rt)
        # print(res)
        # input("Any to continue..")

    #endregion
    scroll_amt = os.get_terminal_size().lines -1
    print("\n" * scroll_amt + f"\033[{scroll_amt}A", end='')
    random_entry = random.choice(res)
    base, answer, form_id, word_type = random_entry[0], random_entry[1], random_entry[-1], random_entry[-2]
    form_tup = None
    if word_type == 'noun':
        form_tup = form_tup_noun
    elif word_type == 'adj':
        form_tup = form_tup_adj
    else:
        raise Exception(f"No form tup somehow! word_type: {word_type}")
    # print(random_entry)
    start = time.time()
    resp = input(f"What is the {form_tup} of {base}?\n")
    stop = time.time()
    elpsd_time = round(stop - start, 2)
    if elpsd_time > time_max:
         # don't log time if too long
         elpsd_time = None
    if not (resp != "/quit" and resp != "/q"):
        break
    if any(resp.lower() == e.lower() for e in  random_entry[1].split('/')):
        passed = True
        print("CORRECT!")
    else:
        passed = False
        print("FAILURE")
    print(f" ans: {answer}")
    valy_stats.add_response(form_id, resp, word_type, passed, elpsd_time)
    input("Any to conintue" + (f" ({count}/{test_max}).." if test_max > 0 else ".."))
    count += 1
if(save_changes):
    conn.commit()
cursor.close()
conn.close()