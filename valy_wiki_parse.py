import bs4
from bsParseTable import *
from typing import Iterator
import pprint
from bs4 import PageElement
from bs4 import Tag
import colorama
from colorama import Fore, Back, Style
from rrjr.rrjr_bs4_printing import *
from rrjr.rrjr_printing import *


#region Get Word Entry Grps
def g_entry_grps(hv_h2: Tag, word_type_opts: dict[str]) -> list[list[Tag]]:
    mwpo: Tag = hv_h2.parent
    mwpo_children: list[Tag] = mwpo.findChildren(recursive=False)
    print("mwpo children len: ", len(mwpo_children))
    entry_grps: list[list[Tag]] = []
    curr_entry = None
    hv_h2_i = None
    for i, tag in enumerate(mwpo_children):
        if tag == hv_h2:
            hv_h2_i = i
        if not hv_h2_i:
            print(f"{i}: (BEFORE HV) {g_tag_head(tag)} ▶")
            continue 
        if not curr_entry:
            tid = None
            try:
                tid = tag.find("span").get("id")
            except:
                pass
            if tid and tid in word_type_opts:
                print(f"{Fore.GREEN}{i}: {g_tag_head(tag)} {tid} ✅{Style.RESET_ALL}")

                entry_grps.append([tag])
                curr_entry = entry_grps[-1]
            else:
                print(f"{i}: {g_tag_head(tag)}")
        else:
            print(f"{Fore.GREEN} {i}: {g_tag_head(tag)} ✅➕{Style.RESET_ALL}")
            entry_grps[-1].append(tag)
    return entry_grps

def g_declen_gender_f_p(p: Tag) -> str:
    try:
        split = p.find("i").text.split(" ")
    except Exception as e:
        raise Exception("could not get p split") from e

    return (split[0], split[2])



def g_urls_from_dict_page(html_doc) -> list[str]:

    soup = bs4.BeautifulSoup(html_doc, 'html.parser')

    # Find the <div> with class "mw-parser-output"
    div = soup.find('div', class_='mw-parser-output')

    # Prepare a list to store the tuples
    result: list[str] = []
    rejected: list[str] = []
    ul_findall: list[Tag] = div.find_all(['ul'], recursive=False)
    stem_url = "https://wiki.languageinvention.com"
    # Iterate over the direct children of the <div>
    for child in ul_findall:
        if child.name == 'ul':
            # Check if the next sibling is a <dl>
            next_sibling = child.find_next_sibling()
            if next_sibling and next_sibling.name == 'dl':
                dl_text = next_sibling.get_text()
                dl_text_1st = dl_text.split(" ")[0]
                # Check if the <dl> meets the criteria
                if 'n.' == dl_text_1st and '6col.' not in dl_text and '6pau.' not in dl_text:
                    # result.append((child, next_sibling))
                    word = child.find("a").text
                    url = "{}".format(  child.find("a").get("href"))
                    result.append((word, url))
                    continue
        # rejected.append(child.text)
    # print(rejected)
    return result
    

