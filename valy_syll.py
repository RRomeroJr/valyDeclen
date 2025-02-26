import re
import typing
from other_ideas.declen_types import EndingsClass
from other_ideas.declen_types import endingObjs
''' the input is a list of words [kōz, daor, ȳdragon]
'''
vowels = r'aeiouyāēīōūȳ'
vowel_long = r'āēīōūȳ'
vowel_short = r'aeiouy'
typicalEndCons = r'rsn'
short_to_long = {vowel_short[i]: vowel_long[i] for i in range((len(vowel_short)))}
long_to_short = {vowel_long[i]: vowel_short[i] for i in range((len(vowel_short)))}
nasal_homorganic = {"n":"d", "m":"b"}
homorganic_nasal = {"d":"n", "b":"m"}

def naive_syll_break(word: str) -> re.Match[str]:
    naiveBreakRegex = r'(?P<front>[bdghjklmnñpqrstvz]*?)(?P<mid>[aeiouāēīōūyȳ]+)(?P<end>[bdghjklmnñpqrstvz]*)'
    return re.findall(naiveBreakRegex, word)
def coda_phrase_shift(inp: list[list]) -> list[list]:
    word = [[part for part in syll] for syll in inp]
    codaPhraseRegex = r'^([ptkqbdg](?=[^zsrl\W])|[hjlmnñrsvz](?=[^aeiouyāēīōūȳ]))?(.*)'
    for i in range(len(word) - 1): # For sylls in word
        if word[i][2] == '':
            continue
        res = re.search(codaPhraseRegex, word[i][2])
        if not res:
            continue
        res = res.groups()
        # print(res)
        if res[0]:
            word[i][2] = res[0]
        else:
            word[i][2] = ''
        if res[1]:
            # print("adding: |" , res[1])
            word[i + 1][0] = res[1] + word[i + 1][0]
    return word
def get_sylls(word:str) -> list[list]:
    return coda_phrase_shift(naive_syll_break(word))
def decline(inp: str, case):
    word = inp
    typicalEnding = re.search(r'([' + "".join(vowels) + r']{1,2})([' + typicalEndCons +r'])?\b', word)
    if typicalEnding:
        for declen, obj in endingObjs.items():
            if (obj.eDict["nom"] == typicalEnding[0]) and (case in obj.eDict):
                print(declen, case, "found:", obj.eDict[case])
                word = str_repl_at(inp, obj.eDict[case], typicalEnding.start(), typicalEnding.end())
                break
    else:
        raise Exception("Couldn't decline {}".format(inp)) 
    

    if(word != inp):
        word = nasal_deletion(word)
    return word

def nasal_deletion(inp: str):
    word = inp
    matches: list[re.Match] = [m for m in re.finditer(r'([{}])?([nm])r'.format(vowel_short), word)]
    # if(len(matches) > 0):
        # print("rule 1 nasal deletion")

    for m in matches:
        vowel = ''
        if m[1]:
            vowel = short_to_long[m[1]]
        newStr = f"{vowel}{nasal_homorganic[m[2]]}r"
        word = str_repl_at(word, newStr, m.start(), m.end())
        # word = word[:m.start()] + "".join(newStr) + (word[m.end():] if m.end() < len(word) else "")

    matches = [m for m in re.finditer(r'([nm])([sz])'.format(vowel_short), word)]
    if(len(matches) > 0):
        print("rule 2 nasal deletion")
    for m in matches:
        newStr = f"z"
        word = str_repl_at(word, newStr, m.start(), m.end())
        # word = word[:m.start()] + "".join(newStr) + (word[m.end():] if m.end() < len(word) else "")
    return word
def str_repl_at(inp:str, sub:str, start:int, stop:int) -> str:
    return inp[:start] + sub + (inp[stop:] if stop < len(inp) else "")

# testStr = "".join([str(x) for x in range(10)])
# print(testStr)
# print(str_repl_at(testStr, "yo", 1, 8))
# res = naive_syll_break("ñakopsemagon")
# res = [list(x) for x in res]
# mod = coda_phrase_shift(res)

# print("āeksio ->",decline("āeksio", "acc"))
# print("konor ->",decline("konor", "acc"))
print("āeksio ->",decline("āeksio", "nomp"))
print("konor ->",decline("konor", "nomp"))
print("āeksio ->",decline("āeksio", "accp"))
print("konor ->",decline("konor", "accp"))

# print("konra ->",nasal_deletion("`konra`"))
# print("ēmza ->",nasal_deletion("ēmza"))

# print("symor ->",decline("symor"))
# print("nor ->",decline("nor"))
# print("front:", res.group("front"))
# print("mid:", res.group("mid"))
# print("end:", res.group("end"))
# def main():
#     while(True):
#         try:
#             print(decline(input("Word!.. "), input("Case!.. ")))
#         except Exception as e:
#             print(e)

# if __name__ == "__main__":
#     main()
