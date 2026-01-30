from dataclasses import asdict, dataclass
from vaantamil.utility import உயிர்_மெய்_எழுத்துகள், மெய்யா, நெடிலா


all_rules = {
    "க்": {1: "[க்]"},
    "ங்": {2: "[ங்][க்]"}, 
    "ச்": {3: "[ச்]"},
    "ஞ்": {4: "[ஞ்][ச்],[ய்]"},
    "ட்": {5: "[ட்],[க்][ச்][ப்]"},
    "ண்": {6: "[ண்][ட்],[க்ச்ஞ்ப்ம்ய்வ்]"},
    "த்": {7: "[த்]"},
    "ந்": {8: "[ந்][த்],[ய்]"},
    "ப்": {9: "[ப்]"},
    "ம்": {10: "[ம்][ப்],[ய்வ்]"},
    "ய்": {11: "[ய்],[க்ச்த்ப்ஞ்ந்ம்வ்]"},
    "ர்": {12: "[க்ச்த்ப்ஞ்ந்ம்ய்வ்]"},
    "ழ்": {13: "[க்ச்த்ப்ஞ்ந்ம்ய்வ்]"},
    "வ்": {14: "[வ்]"},
    "ல்": {15: "[ல்],[க்ச்ப்த்ய்வ்]"},
    "ள்": {16: "[ள்],[க்ச்ப்த்ய்வ்]"},
    "ற்": {17: "[ற்],[க்ச்ப்]"},
    "ன்": {18: "[ன்][ற்],[க்ச்ஞ்ப்ம்ய்வ்]"},
}
three_rules = {
    "ய்": {11: "[க்க்][ச்ச்][த்த்][ப்ப்][ங்க்][ஞ்ச்][ந்த்][ம்ம்]"},
    "ர்": {12: "[க்க்][ச்ச்][த்த்][ப்ப்][ங்க்][ஞ்ச்][ந்த்][ம்ம்]"},
    "ழ்": {13: "[க்க்][ச்ச்][த்த்][ப்ப்][ங்க்][ஞ்ச்][ந்த்][ம்ம்]"},
}

@dataclass
class மெய்ம்மயக்கம்: #மெய் மயக்கு -> மயக்கம்
    எண்: int
    எழுத்துகள்: list[str]
    விதி: str

@dataclass
class மெய்ம்மயக்கம்_தரவு:
    உடனிலை: list[மெய்ம்மயக்கம்]
    இனம்: list[மெய்ம்மயக்கம்]
    வேற்று_நிலை: list[மெய்ம்மயக்கம்]
    மூன்று: list[மெய்ம்மயக்கம்]

def get_rule(letter: str) -> str:
    rules = all_rules.get(letter)
    if not rules:
        return ""
    
    rule_no, nxt = next(iter(rules.items()))
    return f"மெய்ம்மயக்கம்{rule_no}: {letter} + {nxt}"

def get_three_rule(letter: str) -> str:
    rules = three_rules.get(letter)
    if not rules:
        return ""
    
    rule_no, nxt = next(iter(rules.items()))
    return f"மெய்ம்மயக்கம்{rule_no}: {letter} + {nxt}"



def மெய்ம்மயக்கம்_சோதனை(word):
    array = உயிர்_மெய்_எழுத்துகள்(word)
    udanilai = has_udanilai_meimmayakkam(array)
    inam = has_inam_meimmayakkam(array)
    veerrunilai = has_veerrunilai_meimmayakkam(array)
    three = has_three_meimmayakkam(array)

    data = மெய்ம்மயக்கம்_தரவு(
        உடனிலை=udanilai,
        இனம்=inam,
        வேற்று_நிலை=veerrunilai,
        மூன்று=three
    )

    data_dict = asdict(data)
    output = format_meimmayakkam_output(word, array, data_dict)
    return output

def has_udanilai_meimmayakkam(array: list[str]):
    rules = []
    length = len(array) - 2
    for i in range(1, length):
        # exact same consonant twice (க்+க், ண்+ண், etc.) 
        # exclude ர்+ர் and ழ்+ழ்
        if not மெய்யா(array[i - 1]) and array[i] == array[i + 1] and not மெய்யா(array[i + 2]):
            if array[i] == "ர்" or array[i] == "ழ்":
                continue

            rules.append(
                மெய்ம்மயக்கம்(
                    எண்=i,
                    எழுத்துகள்=[array[i], array[i + 1]],
                    விதி=get_rule(array[i]),
                )
            )

    return rules

VALLINAM = ["க்", "ச்", "ட்", "த்", "ப்", "ற்"]
MELLINAM = ["ங்", "ஞ்", "ண்", "ந்", "ம்", "ன்"]

def has_inam_meimmayakkam(array: list[str]):
    rules = []
    for i in range(1, len(array) - 2):
        # MELLINAM → VALLINAM pattern
        if not மெய்யா(array[i - 1]) and array[i] in MELLINAM and not மெய்யா(array[i + 2]):
            mellinam_index = MELLINAM.index(array[i])
            if VALLINAM[mellinam_index] == array[i + 1]:
                rules.append(
                    மெய்ம்மயக்கம்(
                        எண்=i,
                        எழுத்துகள்=[array[i], array[i + 1]],
                        விதி=get_rule(array[i]),
                    )
                )

    return rules

VEERRU_MEIMMAYAKKAM_FIRST = ["ட்", "ற்", "ஞ்", "ண்", "ந்", "ம்", "ன்", "ய்", "ர்", "ழ்", "ள்", "ல்", "வ்"]
VEERRU_MEIMMAYAKKAM_SECOND: dict[str, list[str]] = {
    "ட்": ["க்", "ச்", "ப்"],
    "ற்": ["க்", "ச்", "ப்"], #கற்க, பயிற்சி, கற்பு
    "ஞ்": ["ய்"],
    "ண்": ["க்", "ச்", "ஞ்", "ப்", "ம்", "ய்", "வ்"], # வெண்கலம், மண்சேறு, வெண்ஞமலி் (நாய்), நண்பகல், வெண்மலர், மண்யாது, மண்வலுது 
    "ந்": ["ய்"], #பொந்யாது
    "ம்": ["ய்", "வ்"], # கலம்யாது, வலம்வரும்
    "ன்": ["க்", "ச்", "ஞ்", "ப்", "ம்", "ய்", "வ்"], # பொன்கலம், புன்செய், புன்ஞமலி, புன்பயிர், நன்மை, பொன்யாது, பொன்வலிது    
    "ய்": ["க்", "ச்", "ஞ்", "த்", "ந்", "ப்", "ம்", "வ்"], #செய்கை, வேய்சிறிது (மூங்கில்), வேய்ஞான்றது (மூங்கில் முதிர்ந்தது), செய்தல், வேய்நீண்டது, வேய்பெரிது, பேய்மனம், ஆய்வு
    "ர்": ["க்", "ச்", "ஞ்", "த்", "ந்", "ப்", "ம்", "வ்"], #வேர்கள், வேர்சிறிது, வேர்ஞான்றது, தேர்தல், நீர்நிலை, மார்பு, கூர்மை, தேர்வு
    "ழ்": ["க்", "ச்", "ஞ்", "த்", "ந்", "ப்", "ம்", "வ்"], #மகிழ்கையில், தாழ்சிறிது, வீழ்ஞான்ற (தொங்கிய விழுது), மகிழ்தல், வாழ்நாள், வாழ்பவன், வாழ்மனை, வாழ்வு
    "ள்": ["க்", "ச்", "த்", "ப்", "ய்", "வ்"], #ஆள்கை, நீள்சதுரம், ஆள்தல், மீள்பவர், வாள்யாது, வாள்வலிது
    "ல்": ["க்", "ச்", "த்", "ப்", "ய்", "வ்"], #நல்கு, பல்சுவை, முயல்தல், இயல்பு, வேல்யாது, வேல்வலிது
    "வ்": ["ய்"], #தெவ்யாது (தெவ் - பகை)
}

def has_veerrunilai_meimmayakkam(array: list[str]):
    rules = []
    for i in range(1, len(array) - 2):
        if not மெய்யா(array[i - 1]) and array[i] in VEERRU_MEIMMAYAKKAM_FIRST and not மெய்யா(array[i + 2]):
            second_list = VEERRU_MEIMMAYAKKAM_SECOND.get(array[i], [])
            if array[i + 1] in second_list:
                rules.append(
                    மெய்ம்மயக்கம்(
                        எண்=i,
                        எழுத்துகள்=[array[i], array[i + 1]],
                        விதி=get_rule(array[i]),
                    )
                )

    return rules


THREE_MEIMMAYAKKAM_FIRST = ["ய்", "ர்", "ழ்"]
THREE_MEIMMAYAKKAM_SECOND = ["க்", "ச்", "த்", "ப்", "ங்", "ஞ்", "ந்", "ம்"]
THREE_MEIMMAYAKKAM_THIRD = ["க்", "ச்", "த்", "ப்", "க்", "ச்", "த்", "ம்"]

def has_three_meimmayakkam(array: list[str]):
    rules = []
    for i in range(len(array) - 3):    
        if (
            array[i] in THREE_MEIMMAYAKKAM_FIRST and
            array[i + 1] in THREE_MEIMMAYAKKAM_SECOND and
            not மெய்யா(array[i + 3])):
            print(array[i])
            second_group_index = THREE_MEIMMAYAKKAM_SECOND.index(array[i + 1])
            if THREE_MEIMMAYAKKAM_THIRD[second_group_index] == array[i + 2]:
                # if ((i == 2 or i == 3) and நெடிலா(array[i - 1]) or i > 3):
                rules.append(
                    மெய்ம்மயக்கம்(
                        எண்=i,
                        எழுத்துகள்=[array[i], array[i + 1], array[i + 2]],
                        விதி=get_three_rule(array[i]),
                    )
                )

    return rules

def format_meimmayakkam_output(word: str, array: list[str], result: dict) -> str:
    lines: list[str] = []

    if array:
            lines.append(word)
            lines.append("['" + "','".join(array) + "']")
            lines.append("")

    for _, items in result.items():
        if not items:
            continue  # skip empty lists

        for item in items:
            rule = item.get("விதி")
            num = item.get("எண்")
            letters = item.get("எழுத்துகள்")

            lines.append(rule)
            lines.append(f"     - {num}: {letters}")
            lines.append("")

    return "\n".join(lines).rstrip()

