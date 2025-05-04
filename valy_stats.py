import rrjr_py.rrjr_fm as rrjr_fm
import csv
import random
import time
import math
import os
import sys
import sqlite3
from typing import Union
import valy_db
from pprint import pprint
conn, cursor = valy_db.g_conn_cursor()
stats_file_path = "learning_stats.csv"
headings = {"Nouns:"}
stats_dict: dict[str, dict[str, list[str]]] = None
def load_stats() -> dict:
    global stats_dict
    global stats_file_path
    stats_dict = {}
    open_kwargs = {"mode":"w", "newline":"","encoding": "UTF-8"}
    if not os.path.exists(stats_file_path):
        with open(stats_file_path, **open_kwargs) as _:
            pass
    open_kwargs["mode"] = "r"
    with open(stats_file_path, **open_kwargs) as f:
        reader = csv.reader(f, delimiter='\t')
        currHeading = None
        for r in reader:
            print(len(r), r)
            print(currHeading)
            if len(r) == 1 and r[0] in headings:
                currHeading = r[0]
                stats_dict[currHeading] = {}
            elif len(r) > 1:
                print("adding", r)
                stats_dict[currHeading][r[0]] = r[1:]
    for h in headings:
        if h not in stats_dict:
            stats_dict[h] = {}
    # print("after load", stats_dict)
def write_stats():
    global stats_dict
    global stats_file_path
    with open(stats_file_path, "w", newline="", encoding="UTF-8") as f:
        writer= csv.writer(f, delimiter='\t')
        for k, val_dict in stats_dict.items():
            # print(k)
            writer.writerow((k,))
            for sk, sv in val_dict.items():
                stat_row = (sk,)+tuple(v for v in sv)
                # print(stat_row)
                writer.writerow(stat_row)

    
def log_stats_noun(base: str, form: str, case_quant: str, passed: bool):
    key_name = f"{base}_{case_quant}_{form}_pass%"
    word_pass_list = stats_dict["Nouns:"].get(key_name, [0, 0])
    word_pass_list = [int(x) for x in word_pass_list]

    if passed:
        word_pass_list[0] += 1
    word_pass_list[1] += 1
    stats_dict["Nouns:"][key_name] = word_pass_list
    write_stats()



def add_response(form_id: int, resp:str, word_type: str, passed: bool, resp_time: int| float | None = None):
    if isinstance(resp_time, float):
        resp_time = int(resp_time * 100.0)
    query = """--Add data to responses
    Insert into responses (form_id, resp, word_type, passed, resp_time)
    Values (?, ?, ?, ?, ?)"""
    cursor.execute(query, (form_id, resp, word_type, passed, resp_time))
    last = cursor.execute("Select * From responses where id = ?", (cursor.lastrowid,)).fetchone()
    form_check = cursor.execute("Select form From noun_forms where id = ?", (last[1],)).fetchone()
    print(f'({form_check[0] if form_check else form_check})', last)
def find_worst_case():
    query = """ --Noun version
    WITH pass_rates AS (
        SELECT nf.g_case,
            SUM(CASE WHEN r.passed THEN 1 ELSE 0 END) AS passed,
            SUM(CASE WHEN r.passed THEN 0 ELSE 1 END) AS failed,
            Avg(r.resp_time) As avg_resp_time
            COUNT(r.form_id) AS total
        FROM responses AS r
        LEFT JOIN noun_forms nf ON r.form_id = nf.id
        LEFT JOIN nouns n ON n.id = nf.noun_id 
        GROUP BY nf.g_case
    )
    SELECT g_case, passed, failed, total, avg_resp_time, IIF(total > 0, (passed * 1.0/ total) * 100.0, 0.0) AS pass_rate
    FROM pass_rates
    Order By pass_rate Asc, failed Desc, avg_resp_time Asc
"""
    _r = cursor.execute(query).fetchone()
    pprint(_r)
    return _r[0]
def find_worst(inp:str) -> list[tuple[str, int, int, int, float]]:
    nf_valid = {'case':'g_case', 'quant':'quant'}
    noun_valid = {'declen': 'declen', 'gender': 'gender'}

    table_alias = None
    if inp not in nf_valid and inp not in noun_valid:
        raise Exception("invalid col name for find worst. ({})".format(inp))
    if inp in noun_valid:
        table_alias = 'n'
        # raise Exception(f"{inp} noun cols are NYI :(")
    if inp in nf_valid:
        inp = nf_valid[inp]
        table_alias = 'nf'
    def _find_worst() -> Union[tuple, None]:
        query = f""" --Noun Form version
        WITH pass_rates AS (
            SELECT {table_alias}.{inp},
                SUM(CASE WHEN r.passed THEN 1 ELSE 0 END) AS passed,
                SUM(CASE WHEN r.passed THEN 0 ELSE 1 END) AS failed,
                Avg(r.resp_time) As avg_resp_time,
                COUNT(r.form_id) AS total
            FROM responses AS r
            LEFT JOIN noun_forms nf ON r.form_id = nf.id
            LEFT JOIN nouns n ON n.id = nf.noun_id 
            GROUP BY {table_alias}.{inp}
        )
        SELECT {inp}, passed, failed, total, Round(avg_resp_time, 3), IIF(total > 0, (passed * 1.0/ total) * 100.0, 0.0) AS pass_rate
        FROM pass_rates
        Order By pass_rate Asc, failed Desc, avg_resp_time Asc
    """
        return cursor.execute(query).fetchall()
    
    _r = _find_worst()
    pprint(_r)
    return _r
def find_worst2(word_type: str, inp:str) -> list[tuple[str, int, int, int, float]]:
    valid_word_types = {'noun', 'adj'}
    nf_valid = {'case':'g_case', 'quant':'quant'}
    noun_valid = {'declen': 'declen', 'gender': 'gender'}
    adj_valid = {'class': 'class'}
    af_valid = {'d_type':'d_type', 'pos': 'pos', 'gender': 'gender', 'quant': 'quant'}
    col_to_table_adjs = {'d_type':'adj_d_types', 'pos': 'adj_positions', 'gender': 'genders', 'quant': 'quants', 'class': 'adj_classes'}
    col_to_table_nouns = {'g_case': 'cases', 'quant': 'quants', 'declen': 'declens', 'gender': 'genders'}
    id_types = set('class')
    table_alias = None
    if word_type not in valid_word_types:
        raise Exception('Invalid word type supplied')
    if not any(inp in d for d in (noun_valid, nf_valid, adj_valid, af_valid)):
        raise Exception("invalid col name for find worst. ({})".format(inp))
    if word_type == 'noun':
        base_table = 'nouns'
        forms_table = 'noun_forms'
        if inp in nf_valid:
            inp = nf_valid[inp]
            inp_mapped = col_to_table_nouns[inp]
            table_alias = 'ft'
        elif inp in noun_valid:
            inp = noun_valid[inp]
            inp_mapped = col_to_table_nouns[inp]
            table_alias = 'b'
        # raise Exception("not doing nouns yet")
    if word_type == 'adj':
        base_table = 'adjs'
        forms_table = 'adj_forms'
        if inp in adj_valid:
            inp = adj_valid[inp]
            inp_mapped = col_to_table_adjs[inp]
            table_alias = 'b'
        elif inp in af_valid:
            inp = af_valid[inp]
            inp_mapped = col_to_table_adjs[inp]
            table_alias = 'ft'

    col_name = 'name' if inp not in id_types else 'id'

    def _find_worst() -> Union[tuple, None]:
        query1 = f""" --Adj version
        WITH pass_rates AS (
            SELECT col.name as name,
                SUM(CASE WHEN r.passed = 1 THEN 1 ELSE 0 END) AS passed,
                SUM(CASE WHEN r.passed = 0 THEN 1 ELSE 0 END) AS failed,
                AVG(r.resp_time) AS avg_resp_time,
                COUNT(r.form_id) AS total
            FROM {inp_mapped} As col"""
        if table_alias == 'b':
            query2 = f"""
            Left Join {base_table} b On col.{col_name} = b.{inp}
            Left Join {forms_table} ft On b.id = ft.{word_type}_id"""

        else:
            query2 = f"""
            Left Join {forms_table} ft on col.{col_name} = ft.{inp}
            Left Join {base_table} b On ft.{word_type}_id = b.id"""

        query3 = f"""
            Left Join responses r On ft.id = r.form_id And r.word_type = '{word_type}'
            Group By col.{col_name}
        )"""

        query = query1 + query2 + query3 + """
        SELECT name, passed, failed, total, Round(avg_resp_time, 3), IIF(total > 0, (passed * 1.0/ total) * 100.0, 0.0) AS pass_rate
        FROM pass_rates
        Order By pass_rate Asc, failed Desc, avg_resp_time Asc
        """
        # print(query)
        worst_list = cursor.execute(query).fetchall()
        pprint(worst_list)
        count = cursor.execute(f"Select count(*) from responses As r where r.word_type = '{word_type}'").fetchone()[0]
        count2 = 0
        for i in worst_list:
            count2 += i[3]
        assert count == count2, f"count mismatch 1: {count}, 2: {count2}"
        print("👌", count, count2)
        return worst_list
    
    _r = _find_worst()
    pprint(_r)
    return _r
def find_worst3(word_type: str, inp:str) -> list[tuple[str, int, int, int, float]]:
    valid_word_types = {'noun', 'adj'}
    word_type_to_base = {'noun': 'nouns', 'adj': 'adjs'}
    word_type_to_form = {'noun': 'noun_forms', 'adj': 'adj_forms'}
    base_table = word_type_to_base[word_type]
    forms_table = word_type_to_form[word_type]
    fks_base = cursor.execute(f"Pragma foreign_key_list({base_table})").fetchall()
    fks_form = cursor.execute(f"Pragma foreign_key_list({forms_table})").fetchall()
    fk = None
    table = None
    for _fk in fks_base:
        if inp not in _fk:
            continue
        table = base_table
        fk = _fk
        break
    if not fk:
        for _fk in fks_form:
            if inp not in _fk:
              continue
            table = forms_table
            fk = _fk 
            break
    
    assert fk != None, f'couldn\'t find fk for word_type: {word_type}, inp: {inp}'
    print(table)
    fk_table = fk[2]
    fk_col = fk[4]

    def _find_worst() -> Union[tuple, None]:
        query1 = f""" --Adj version
        WITH pass_rates AS (
            SELECT fk.{fk_col} as name,
                SUM(CASE WHEN r.passed = 1 THEN 1 ELSE 0 END) AS passed,
                SUM(CASE WHEN r.passed = 0 THEN 1 ELSE 0 END) AS failed,
                AVG(r.resp_time) AS avg_resp_time,
                COUNT(r.form_id) AS total
            FROM {fk_table} As fk"""
        if any(table == e for e in ('nouns', 'adjs')):
            query2 = f"""
            Left Join {base_table} b On fk.{fk_col} = b.{inp}
            Left Join {forms_table} ft On b.id = ft.{word_type}_id"""

        elif any(table == e for e in ('noun_forms', 'adj_forms')):
            query2 = f"""
            Left Join {forms_table} ft on fk.{fk_col} = ft.{inp}
            Left Join {base_table} b On ft.{word_type}_id = b.id"""
        else:
            raise Exception(f"Couln\'t build joins table: {table}, inp: {inp}")
        query3 = f"""
            Left Join responses r On ft.id = r.form_id And r.word_type = '{word_type}'
            Group By fk.{fk_col}
        )"""

        query = query1 + query2 + query3 + """
        SELECT name, passed, failed, total, Round(avg_resp_time, 3), IIF(total > 0, (passed * 1.0/ total) * 100.0, 0.0) AS pass_rate
        FROM pass_rates
        Order By pass_rate Asc, failed Desc, avg_resp_time Asc
        """
        print(query)
        worst_list = cursor.execute(query).fetchall()
        pprint(worst_list)
        count = cursor.execute(f"Select count(*) from responses As r where r.word_type = '{word_type}'").fetchone()[0]
        count2 = 0
        for i in worst_list:
            count2 += i[3]
        assert count == count2, f"count mismatch 1: {count}, 2: {count2}"
        print("3✅", count, count2)
        return worst_list
    
    _r = _find_worst()
    pprint(_r)
    return _r
        

def convert_old_data():
    def g_files(target_path) -> list[str]:
        file_paths = []
        listdir = os.listdir(target_path)
        for e in listdir:
            sub_path_str = os.path.join(target_path, e)
            if os.path.isfile(sub_path_str):
                file_paths.append(sub_path_str)
            elif os.path.isdir(sub_path_str):
                file_paths.extend(g_files(sub_path_str))
        return file_paths
    dir_path = r'learning_log\failed'
    f_paths = g_files(dir_path)
    # pprint(g_files(dir_path))
    def get_data(csv_paths:list[str]):
        data_list = []
        for csv_path in csv_paths:
            # print("process..", csv_path)
            os_split = os.path.split(csv_path)
            dirs_split = os_split[0].split('\\')
            final = dirs_split[-1]
            # print("final:", final, "file name:", os_split[-1])
            with open(csv_path, 'r', encoding='UTF-8') as f:
                rows = csv.reader(f, delimiter='\t')
                for r in rows:
                    if final in ('no_params', 'empty_lines') and rows.line_num == 1:
                        continue
                    if final in ('failed') and rows.line_num <= 2:
                        continue
                    if len(r) < 1:
                        continue
                    data = []
                    if final not in ('no_resp'):

                        data.extend(r[:2]) # base, form
                        data.extend(r[3].split("_")) # case_quant
                        data.append(r[2]) # declen
                        data.append(r[4]) # resp
                        if final not in ('empty_lines'):
                            data.append(r[5]) # resp_time
                        else:
                            data.append(None) # resp_time availiable
                    else:
                        data.extend(r[1:3])# base, form
                        data.extend(r[0].split("_")) # case_quant
                        data.append(r[-1]) # declen
                        data.extend((None, None)) # no resp/ resp_time availiable
                    # print(rows.line_num, data)
                    assert len(data) == 7, f"len not 7 {data}\n{csv_path}"
                    data_list.append((data, csv_path))

        return data_list
    resp_data = get_data(f_paths)
    g_form_id_q = """
    Select nf.id From noun_forms As nf
    Inner Join nouns n On n.id = nf.noun_id
    Where n.base = ?
    And nf.form = ?
    And nf.g_case = ?
    And nf.quant = ?
    And n.declen = ?
"""
    insert_args = []
    for rd, path in resp_data:
        form_id = cursor.execute(g_form_id_q, rd[:5]).fetchone()
        assert form_id != None, f"No form id found for\n{rd}\n{path}"
        assert isinstance(form_id[0], int), f"form id not int. is {type(form_id)}\n{rd}\n{path}"
        form_from_found = cursor.execute("Select form from noun_forms where id = ?", (form_id[0],)).fetchone()[0]
        assert form_from_found == rd[1], f"form form found id didn't match form form data\nfound: {form_from_found} data: {rd[1]}"
        insert_args.append((form_id[0], rd[-2], 'noun', float(rd[-1]) if rd[-1] else rd[-1]))
    print("all good 👌")
    # print(insert_args)
    converted_insert_q ="""
    Insert into responses (form_id, resp, word_type, resp_time)
    Values (?, ?, ?, ?)
"""
    for ia in insert_args:
        add_response(*ia)
    pprint(cursor.execute("Select * From responses").fetchall())
        
def db_test():
    prompt = cursor.execute("Select nf.id, n.base, nf.form, n.gender, nf.g_case, nf.quant, n.declen, 'noun' From noun_forms As nf Join nouns n On n.id = nf.noun_id").fetchall()
    random.seed(42069)
    prompt = random.choice(prompt)
    print(prompt)
    form = prompt[0]
    w_type = prompt[-1]
    # info = "_".join(x for x in prompt[3:7])
    add_response(form, "yourmom", w_type)
    g_data_and_map_nouns ="""
    Select r.id As id, nf.form As form, r.resp As resp, r.info, r.word_type As w_type
    from responses As r
    Left Join noun_forms nf On r.form_id = nf.id
    Where r.id = ?  
    """

    new_row = cursor.execute(g_data_and_map_nouns, (cursor.lastrowid,)).fetchone()
    print(cursor.description)
    # maps_names = list(x[0] for x in cursor.description)
    # maps_names[1] = 'noun_' + maps_names[1]
    # print(maps_names)
    # print("mapped", valy_db.map_ids(maps_names, new_row))
    print("with nf2", new_row)
    # print(valy_db.g_sql("responses"))
    # print(cursor.execute(g_data_and_map_nouns, 1).fetchall())
def test(*args: str):
    print("running stats test", args)
    inp = True
    if len(args) > 1:
        if args[1].lower() == "false" or args[1].lower() == "0":
            inp = False
    print("inp", inp)
    log_stats_noun("ñāqes", "ñāqoti", "loc_pl", inp)

def _test_find_worst():
    nf_valid = {'case':'g_case', 'quant':'quant'}
    noun_valid = {'declen': 'declen', 'gender': 'gender'}
    adj_valid = {'class': 'class'}
    af_valid = {'d_type':'d_type', 'pos': 'pos', 'gender': 'gender', 'quant': 'quant'}
    args = []
    for k in noun_valid: args.append(('noun', k))
    for k in nf_valid: args.append(('noun', k))
    for k in adj_valid: args.append(('adj', k))
    for k in af_valid: args.append(('adj', k))
    for a in args:
        try:
            find_worst2(*a)
        except Exception as e:
            print("from", a)
            raise Exception(f"args were {a}") from e

# load_stats()
if __name__ == "__main__":
    # test(*sys.argv)
    noun_col = 'quant'
    # find_worst(noun_col)
    # find_worst2('noun', noun_col)
    _find_worst3('adj', 'gender')
    # find_worst('quant')
    # _test_find_worst()
    # print(valy_db.g_sql("responses"))