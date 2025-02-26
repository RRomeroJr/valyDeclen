import bs4
from rrjr.rrjr_fm import sp_open
import sys
from bs4.element import Tag
import pprint

def parse_table(wt:Tag)-> dict[dict[str]]:

    w_forms = {}
    # x_to_quant = {0: "Singular", 1: "Plural", 2: "Paucal", 3:"Collective"}
 
    t_rows: list[Tag] = wt.find("tbody", recursive=False).find_all("tr",recursive=False)
    # print(t_rows[0])

    t_headers: list[Tag] = t_rows[0].find_all("th",recursive=False)
    for h in t_headers:
      text = h.text.strip()
      if text != "":
          w_forms[text] = {}
        

    print(len(w_forms), w_forms)
    assert len(w_forms) == 4, "w_forms len not 4"

    x_to_header = {h[0]+1:h[1] for h in enumerate(w_forms.keys())}
    print(x_to_header)
    print("len t_rows", len(t_rows))
    for y in range(1, len(t_rows)):
      t_datas: list[Tag] = t_rows[y].find_all("td", recursive=False)
      case = t_datas[0].text.strip()
      offset = 0

      x = 1
      while x < len(t_datas):
        h_i = x
        if (x_to_header[x] in w_forms )and (case in w_forms[x_to_header[x]]):
          while (case in w_forms[x_to_header[h_i]]) and h_i < len(w_forms):
            h_i += 1
        
        text = t_datas[x].text.strip()
        # print(x_to_header[x], case, text)
        w_forms[x_to_header[h_i]][case] = text

        row_span = None
        try:
          row_span = int(t_datas[x].get("rowspan"))
        except:
           pass
        if row_span and (row_span > 1):
            for rs in range(1, row_span):
              span_case = t_rows[y + rs].find("td").text.strip()
              print(x_to_header[h_i], span_case, text)
              w_forms[x_to_header[h_i]][span_case] = text
        x += 1
      # pprint.pprint(w_forms["Collective"])
      # input("Next..")
    # pprint.pprint(w_forms)
    for quant, d in w_forms.items():
      assert len(w_forms[quant]) == 8, "quant {} has {} items\n\n{}".format(quant, len(w_forms[quant]), d)
    print("Parse noun table tests passed!")
    return w_forms
          
          


    
