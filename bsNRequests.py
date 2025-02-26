import bs4
import requests
import rrjr.rrjr_fm as rrjr_fm
from rrjr import sp_open
import sys
from bsParseTable import *
from typing import Iterator
# import pprint
import pprint
from bs4 import PageElement
from bs4 import Tag
import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *
from valy_wiki_parse import *
import sqlite3
import valy_db
from valy_db import g_conn_cursor
import csv
import time
import random
import logging
import traceback
headers = {
	"Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
	"Accept-Encoding": "gzip, deflate, br, zstd",
	"Accept-Language": "en-US,en;q=0.5",
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"
}
root_logger= logging.getLogger()
root_logger.setLevel(logging.ERROR) # or whatever
handler = logging.FileHandler(rrjr_fm.g_seq_filename('process_out/fail/process_fail.log'), encoding='utf-8')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(handler)

colorama.init()

test_url = r"http://localhost:8080/%C3%91%C4%81qes%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"

def process_url(url, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
    get = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(get.text, "html.parser")
    # endregion

    #region Get Word Entry Grps
    word_type_opts = {"Noun"}
    hv_h2 = soup.find('span', id="High_Valyrian").parent
    declen_strs = {"first", "second", "third", "fourth", "fifth", "sixth"}
    gender_strs = {"lunar", "solar", "terrestrial", "aquatic"}
    pr_separate()
    entry_grps = g_entry_grps(hv_h2, word_type_opts)
    pr_separate()


    print("entry_grps:", len(entry_grps), "👈")
    valid_entry_grps: list[dict[str]] = []
    split_max = 3
    for i, g in enumerate(entry_grps): # Logging gps
        print(f"grp {i}:")
        indent = "".join([" "] * 2)
        try:
            for j, t in enumerate(g):
                print(indent + g_tag_head(t))
                if j == 1:
                    declen, gender = g_declen_gender_f_p(t)
                    assert declen in declen_strs, f"invalid declen at {i}: {declen}"
                    assert gender in gender_strs, f"invalid gender at {i}: {gender}"
                if j == 4:
                    table_dict = parse_table(t)
                    assert table_dict != None, f"Could not get table dict in grp {1}"
            valid_entry_grps.append(
                {"word": table_dict["Singular"]["Nominative"],
                "declen": declen,
                "gender": gender,
                "forms": table_dict
                })
        except Exception as e:
            print(f"passing on {i}\n {e}")
    print(valid_entry_grps)
    veg_len = len(valid_entry_grps)
    if veg_len <= 0:
        print(f"{Fore.RED}gāomon issa ❌{Style.RESET_ALL}")
    elif veg_len > 1:
        print(f"Success.. but len greater than 1.. {Fore.YELLOW}⚠{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}tolvȳn sȳz issa 👍{Style.RESET_ALL}")
    entry = valid_entry_grps[0]
    valy_db.enter_to_word_info(entry)
    valy_db.enter_to_word_forms(entry)
    
    wi_tup = conn.execute("select * from word_info where word = ?", (entry["word"],)).fetchone()
    wf_tup = conn.execute("select * from word_forms where nom_sing = ?", (entry["word"],)).fetchone()
    print(entry["word"] + ":\n" +
        " \n".join(["word info: " + str(wi_tup), "new word form entry found ✅" if wf_tup else f"no word form entry found ❌"]))

def main():
    urls_tups = []
    with open("noun_urls.txt", "r", encoding="UTF-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for r in reader:
            urls_tups.append(tuple(r))
    conn, cursor = g_conn_cursor()
    valy_db.s_conn_cursor(conn, cursor)
    valy_db.create_word_info_table()
    valy_db.create_words_forms_table()
    # urls_tups = urls_tups[:2]
    failed = []
    count = 0
    count_max = len(urls_tups)
    print("urls len:", len(urls_tups))
    for word, url in urls_tups:
        print(f"\r\033[Kprocessing.. ({round(count/count_max, 2)})", end="\r")
        # time.sleep(4)
        try:
            # assert False, "test asert"
            process_url(url, conn, cursor)
        except Exception as e:
            print("\r\033[K", e)
            failed.append((word, url, e))
            log_str = f"{word}, url: {url}"
            logging.error(log_str, exc_info=True)
        count += 1
        if count < count_max: 
            random_delay = random.randint(17, 28)
            print(f"\r\033[Krandom delay {random_delay}.. ({round(count/count_max, 2)})", end="\r")
            time.sleep(random_delay)
        # print("..end!")
    cursor.close()
    conn.close()
    print("\r\033[Kfailed len:", len(failed))

            
if __name__ == "__main__":
    main()
