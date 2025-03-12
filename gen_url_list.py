import requests
import rrjr.rrjr_fm as rrjr_fm
from typing import Iterator
import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *
from valy_wiki_parse import *
import csv
colorama.init()
url = r"http://localhost:8080/dict/High%20Valyrian%20Dictionary%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"
get = requests.get(url)

res = g_urls_from_dict_page(get.text, {"adj."}, {"indecl."})

file_name = rrjr_fm.g_seq_filename("urls/adj_urls.txt")
with open(file_name, "w", newline="", encoding="UTF-8") as f:
    wr = csv.writer(f, delimiter="\t")
    for r in res:
        wr.writerow(r)
print(f"found {len(res)} urls")
