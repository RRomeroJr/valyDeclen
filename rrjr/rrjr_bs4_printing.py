import bs4
from rrjr_py.rrjr_fm import sp_open
from typing import Iterator
import pprint
from bs4 import PageElement
from bs4 import Tag
import colorama
from colorama import Fore, Back, Style
colorama.init()
def g_tag_head(tag: Tag):
    attrs = " ".join(f"{k}={v}" for k,v in tag.attrs.items())
    if attrs != "":
        attrs = " " + attrs
    return f"<{tag.name}{attrs}>"

    
