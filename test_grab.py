import requests
from table_parse import *
from typing import Iterator
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *
from valy_wiki_parse import *
from name_maps import adj_class_map
import valy_db
import phrase_handler
# noun
# url = r"http://localhost:8080/noun_%C3%B1%C4%81qes/%C3%91%C4%81qes%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"
# adj
test_url_adj = r"http://localhost:8080/adjs/class_3/Z%C5%8Dbrie%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"
test_url_noun = r"http://localhost:8080/noun/%C3%B1aqes/%C3%91%C4%81qes%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"
url = test_url_noun
get = requests.get(url)

soup = bs4.BeautifulSoup(get.text, "html.parser")
# endregion

#region Get Word Entry Grps
word_type_opts = {"Noun"}
hv_h2 = soup.find('span', id="High_Valyrian").parent
entry_grps = g_entry_grps(hv_h2, word_type_opts)
print("len(entry_grps)", len(entry_grps))
e_grp = entry_grps[0]
#-------------------------------------------------------------
pr_separate()

def test():
    # phrase_handler.handle_adj(e_grp)
    phrase_handler.handle_noun(e_grp)

if __name__ == '__main__':
    test()


# for r in res:
#     print(len(r), r)
# Len should be 388 I think for class 2 and 3
# 2 tables x 8 cases * 4 quanty/ gender * 2 posistions : 128
# + 2 tables x 8 cases * 8 quanty/ gender * 2 posistions : 256
# 4 adv forms : 4   128 + 256 + 4 = 388
# conn, cursor = valy_db.g_conn_cursor()
# valy_db.add_adj_to_db(word, adj_class_map[adj_class], res)
# cursor.close()
# conn.close()
# print(res)