import bs4
from rrjr_fm import sp_open
from rrjr_printing import pr_separate
import sys
from bs4.element import Tag
import pprint

def parse_table_noun(wt:Tag)-> dict[dict[str, str]]:
    
    # x_to_quant = {0: "Singular", 1: "Plural", 2: "Paucal", 3:"Collective"}
    t_rows: list[Tag] = wt.find("tbody", recursive=False).find_all("tr",recursive=False)

    # First row are headers
    w_forms: dict[str,dict] = {}
    t_headers: list[Tag] = t_rows[0].find_all("th",recursive=False)
    for h in t_headers:
      text = h.text.strip()
      if text != "":
          w_forms[text] = {}
        
    # Should be 4. sing, pl, pau, col
    print(len(w_forms), w_forms)
    assert len(w_forms) == 4, "w_forms len not 4"

    x_to_header = {i:h for i, h in enumerate(w_forms.keys(), start=1)}
    print(x_to_header)
    print("len t_rows", len(t_rows))
    for y in range(1, len(t_rows)):
      t_datas: list[Tag] = t_rows[y].find_all("td", recursive=False)

      # First in row is the case
      case = t_datas[0].text.strip()
      offset = 0

      x = 1
      while x < len(t_datas):
        h_i = x
        if (x_to_header[x] in w_forms) and (case in w_forms[x_to_header[x]]):
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
    for quant, case_dict in w_forms.items():
      assert len(w_forms[quant]) == 8, "quant {} has {} items\n\n{}".format(quant, len(w_forms[quant]), case_dict)
    print("Parse noun table tests passed!")
    return w_forms

def naive_parse(t_rows:list[Tag]) -> list[list[str]]:
  """This trys to turn table row tags into a 2d list of lists.
  items when span multiple cols/ rows become multiple slots
  in this 2d array."""
  # print("naive_parse")
  x_max = 0
  ti: list[Tag] = t_rows[0].find_all(["th", "td"], recursive=False)
  for t in ti:
    span = int(t.get("colspan", 1))
    x_max += span


  res: list[list[tuple]] = [[None for _ in range(x_max)] for _ in range(len(t_rows))]
  def print_res():
    for r in res:
      print(len(r), r)
  y = 0
  x = 0
  x1 = x
  while y < len(t_rows):
    # print("y is now", y, "len(t_rows)", len(t_rows))
    t_items: list[Tag] = t_rows[y].find_all(["th", "td"], recursive=False)
    x = 0
    x1 = x
    while x < len(t_items):
      text = t_items[x].text.strip()
      while res[y][x1] != None:
        print("found", res[y][x1], "⏩")
        x1 += 1
      list_item = [text, t_items[x].name]
      rowspan = min([len(t_rows) - 1, int( t_items[x].get("rowspan", 1) )])
      colspan = min([x_max - 1, int( t_items[x].get("colspan", 1) )])
      y1 = y
      while y1 < y + rowspan:
        # if(rowspan > 1):
        #     print(f"rowspaning {text}. {rowspan}")
        x2 = x1
        while x2 < x1 + colspan:
          # if(colspan > 1):
          #   print(f"colspaning {text}. {colspan}")
          res[y1][x2] = list_item
          # print_res()
          x2 += 1
        y1 += 1
      x1 = x2
      # pr_separate()
      x += 1
    y += 1
      
  return res

def parse_table_adj(wt:Tag):
 
  t_rows: list[Tag] = wt.find("tbody", recursive=False).find_all("tr",recursive=False)
  # print(t_rows[0])
  # Have to skip the first row bc it contains nav stuff.
  table_lists = naive_parse(t_rows[1:])
  return table_lists
