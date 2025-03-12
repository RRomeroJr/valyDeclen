import bs4
import requests
import rrjr.rrjr_fm as rrjr_fm
from typing import Callable, Iterator
import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *
from valy_wiki_parse import g_entry_grps
import valy_db
import csv
import time
import random
import logging
import traceback
import phrase_handler
valy_db.init()
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
conn, cursor = valy_db.g_conn_cursor()

colorama.init()

test_url_noun = r"http://localhost:8080/noun/%C3%B1aqes/%C3%91%C4%81qes%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"
test_url_adj = r"http://localhost:8080/adjs/failed_d_type/Ruaka%20-%20The%20Languages%20of%20David%20J.%20Peterson.htm"

def process_url(word, url):
    print(f"Grabing html, for {word}\n{url}")
    get = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(get.text, "html.parser")
    # endregion

    #region Get Word Entry Grps
    word_type_opts: dict[str, Callable] = {"Noun": phrase_handler.handle_noun, "Adjective": phrase_handler.handle_adj}
    hv_h2 = soup.find('span', id="High_Valyrian").parent
    pr_separate()
    entry_grps = g_entry_grps(hv_h2, word_type_opts)
    
    # assert len(entry_grps) == 1, f"{Fore.RED}len(entry_grps) != 1. found {len(entry_grps)} ❌{Style.RESET_ALL}"

    print(f"{Fore.CYAN}tolvȳn sȳz issa 👍{Style.RESET_ALL}")
    # only for now only handling the case where there is 1 entry grp
    for i, g in enumerate(entry_grps):
        pr_separate()
        print(f'group {i}')
        try:
            w_type = g[0].find("span").get("id")
            if w_type in word_type_opts:
                word_type_opts[w_type](g)
        except Exception as e:
            conn.rollback()
            traceback.print_exc()
            raise Exception(f"Process for {word} grp {i}:{Fore.RED} failed {Style.RESET_ALL}skipping group ⏩") from e
    

def main():
    print("Initalizing..")
    urls_tups = []
    test = True
    url_paths_adjs = "urls/adj_urls.txt"
    url_paths_nouns = "urls/noun_urls.txt"
    url_paths = url_paths_nouns
    if(not test):
        with open(url_paths, "r", encoding="UTF-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for r in reader:
                urls_tups.append(tuple(r))
    else:
        valy_db.s_commit_mode(valy_db.Commit_Modes.ROLLBACK)
        urls_tups.append(('ñaqes', test_url_noun))
        urls_tups.append(('ruaka', test_url_adj))
    # urls_tups = urls_tups[:10]
    
    failed = []
    count = 0
    count_max = len(urls_tups)
    print("Looping urls, len:", len(urls_tups))
    for word, url in urls_tups:
        print(f"\r\033[Kprocessing {word}.. ({round(count/count_max, 2)})", end="\r")
        # time.sleep(4)
        try:
            # assert False, "test asert"
            process_url(word, url)
        except Exception as e:
            print("\r\033[K", e)
            failed.append((word, url, e))
            log_str = f"{word}, url: {url}"
            logging.error(log_str, exc_info=True)
        count += 1
        if count < count_max: 
            random_delay = random.randint(17, 28)
            print(f"\r\033[KFinished {word} waiting random delay {random_delay}.. ({round(count/count_max, 2)})", end="\r")
            time.sleep(random_delay)
    print("..end!")
    valy_db.cursor.close()
    valy_db.conn.close()
    print("\r\033[Kfailed len:", len(failed))

            
if __name__ == "__main__":
    main()
