from table_parse import *
from valy_wiki_parse import *
from typing import Iterator
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *
from name_maps import adj_class_map, case_map, quant_map, adj_pos_map, gender_map, declen_map
import valy_db
from colorama import Fore, Back, Style
conn, cursor = valy_db.g_conn_cursor()


def g_noun_vals(list_obj: list[list[tuple]]) -> set[tuple]:
    global case_map, quant_map
    maps = [case_map, quant_map]
    def _g_noun_vals(x: int, y: int):
        if y < 1:
            raise Exception(f"adj data starts at y == 1 was given {y}")
        if x < 1:
            raise Exception(f"adj data starts at x == 1 was given {x}")
        
        # word form, quantity, case
        vals:list[str] = [list_obj[y][x][0], list_obj[0][x][0], list_obj[y][0][0]]
        # print(vals[1])
        for i in range(len(vals)):
            vals[i] = vals[i].lower()
            for m in maps:
                if vals[i] in m:
                    vals[i] = m[vals[i]]
                    break
        
        return tuple(vals)
    res = set()
    for x in range(len(list_obj[0])):
        for y in range(len(list_obj)):
            if list_obj[y][x][1] == 'td':
                res.add(_g_noun_vals(x, y))
    return res
def get_adj_values(table_name: str, list_obj: list[list[tuple]]) -> set[tuple]:
    global case_map, quant_map, adj_class_map, adj_pos_map, gender_map
    maps = [case_map, quant_map, adj_class_map, adj_pos_map, gender_map]
    def _get_adj_values(x: int, y: int):
        if y < 2:
            raise Exception(f"adj data starts at y == 2 was given {y}")
        if x < 1:
            raise Exception(f"adj data starts at x == 1 was given {x}")
        
        # word form, d_type, pre/post positive, gender, quantity, case
        vals:list[str] = [list_obj[y][x][0], table_name, list_obj[0][0][0], list_obj[0][x][0], list_obj[1][x][0], list_obj[y][0][0]]
        # print(vals[1])
        vals[1] = cursor.execute("Select name From adj_d_types Where name_long = Lower(?)", (vals[1],)).fetchone()[0]
        for i in range(len(vals)):
            vals[i] = vals[i].lower()
            if vals[-1] == "adverbial":
                vals[2] = 'n/a'
                vals[3] = 'n/a'
                vals[4] = 'n/a'
            for m in maps:
                if vals[i] in m:
                    vals[i] = m[vals[i]]
                    break
        
        return tuple(vals)
    res = set()
    for x in range(len(list_obj[0])):
        for y in range(len(list_obj)):
            if list_obj[y][x][1] == 'td':
                res.add(_get_adj_values(x, y))
    return res


def handle_adj(e_grp: list[Tag]):
    global adj_class_map
    def adj_adjust_lists(list_obj: list[list[tuple]]):
        for row_list in list_obj:
            # marking 1st col as header vals
            if row_list[0][1] == "td":
                row_list[0][1] = 'th'
    forms = set()
    for t in e_grp:
        if t.name == 'p':
            # print(f" <{t.name}>", "👈")
            split = t.get_text(" ", strip = True).split(" ")
            print(split)
            word = split[0].lower()
            adj_class = split[2]
            print(word, adj_class)
        elif t.name == 'table':
            # print(f" <{t.name}>", "👈")
            t_rows: list[Tag] = t.find("tbody", recursive=False).find_all("tr",recursive=False)
            table_name_split =  t_rows[0].find('th').get_text(" ", strip = True).split(" ")
            print(table_name_split)
            """When I load the test copied page the len is 5 but on the
            actual site the len is 4. Probaly some anti bot thing but the 
            page is seemly static so idk..vvv"""
            if (len(table_name_split) == 4):
                table_name = table_name_split[0]
            elif (len(table_name_split) == 5):
                table_name = table_name_split[1]
            table_name = table_name.lower()
            # print(table_name)
            # table_name =  t_rows[0].find('th').get_text(" ", strip = True).split(" ")
            # pre_post = [t_rows[1:12]]
            # pre_post = [t_rows[12:]]
            pre_post = [t_rows[1:12], t_rows[12:]]
            # print(table_name)
            for sub_table in pre_post:
                t_items = naive_parse(sub_table)
                adj_adjust_lists(t_items)
                forms.update(get_adj_values(table_name, t_items))
    # print("word", word, "adj_class", adj_class_map[adj_class], "len(forms)", len(forms))
    # print(forms.pop())
    if adj_class not in adj_class_map:
        raise Exception(f"unknown adj class {adj_class}")
    adj_class = adj_class_map[adj_class]
    expected_forms = None
    if adj_class == 1:
        expected_forms = 452
    else:
        expected_forms = 388

    if len(forms) != expected_forms:
        raise Exception(f"{word} has an unexpected amt of forms: ({len(forms)})")
    else:
        print(f"expected forms check: {Fore.GREEN}Pass{Style.RESET_ALL} ({len(forms)})")
    def add_to_db():
        adj_id = valy_db.add_adj_to_db(word, adj_class, forms)
        adjs_res = conn.execute("select * from adjs where id = ?", (adj_id,)).fetchone()
        forms_res = conn.execute("select * from adj_forms where adj_id = ?", (adjs_res[0],)).fetchall()
        if not adjs_res:
            raise Exception(f"no adj_res for {word}❗🚨❗")
        if not len(forms_res) > 0:
            raise Exception(f"no adj_forms found for {word}❗🚨❗") 
        print(word + ":\n" +
            " \n".join(["adj info: " + str(adjs_res), f"adj forms ({len(forms_res)})\n{forms_res[0]} ✅"]))
    add_to_db()
    # conn.rollback()
    valy_db.commit()
    # return {"word": word, "adj_class": adj_class, "forms": forms}

def handle_noun(e_grp: list[Tag]):
    global gender_map, quant_map, case_map, declen_map
    def noun_adjust_lists(list_obj: list[list[tuple]]):
        for row_list in list_obj:
            # marking 1st col as header vals
            if row_list[0][1] == "td":
                row_list[0][1] = 'th'
    forms = set()
    for t in e_grp:
        if t.name == 'p':
            # print(f" <{t.name}>", "👈")
            split = t.get_text(" ", strip = True).split(" ")
            print(split)
            word = split[0].lower()
            declen_gender_split = t.find("i").get_text(" ", strip = True).split(" ")
            declen = declen_gender_split[0]
            gender = declen_gender_split[2]
            print(word, declen, gender)
        elif t.name == 'table':
            # print(f" <{t.name}>", "👈")
            t_rows: list[Tag] = t.find("tbody", recursive=False).find_all("tr",recursive=False)
            # print(table_name)
            t_items = naive_parse(t_rows)
            noun_adjust_lists(t_items)
            forms.update(g_noun_vals(t_items))
    # print("word", word, "adj_class", adj_class_map[adj_class], "len(forms)", len(forms))
    # print(forms.pop())
    if gender not in gender_map:
        raise Exception(f"unknown noun gender {gender}")
    if declen not in declen_map:
        raise Exception(f"unknown noun declen {declen}")
    gender = gender_map[gender]
    declen = declen_map[declen]

    def add_to_db():
        noun_id = valy_db.add_noun_to_db(word, declen, gender, forms)
        noun_res = conn.execute("select * from nouns where id = ?", (noun_id,)).fetchone()
        forms_res = conn.execute("select * from noun_forms where noun_id = ?", (noun_res[0],)).fetchall()
        if not noun_res:
            raise Exception(f"no noun_res for {word}❗🚨❗")
        if not len(forms_res) > 0:
            raise Exception(f"no noun forms found for {word}❗🚨❗") 
        print(word + ":\n" +
            " \n".join(["noun info: " + str(noun_res), f"noun forms ({len(forms_res)})\n{forms_res[0]} ✅"]))
    add_to_db()
    valy_db.commit()
    # conn.commit()
    # return {"word": word, "adj_class": adj_class, "forms": forms}


# for f in forms:
#     print(len(r), r)

# Len should be 388 I think for class 2 and 3
# 2 tables x 8 cases * 4 quanty/ gender * 2 posistions : 128
# + 2 tables x 8 cases * 8 quanty/ gender * 2 posistions : 256
# 4 adv forms : 4   128 + 256 + 4 = 388


# print(forms)