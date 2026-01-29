path = "tests/dic1.dic"


def read_dic(path):
    """
    path: path to a Nooj dictionary file (.dic)
    returns:
        A list of dictionaries (one for each line)

        example .dic:
        amo,amare,V+PRIM=o;as;are;aui;atum+Theme=INF+TRAD=aimer+FLX=GP1_INF+VX=act+P=1+NB=sg+GP=1+TP=pres+MOD=ind
        debebuntur,debere,V+PRIM=eo;es;ere;bui;bitum+Theme=INF+TRAD=devoir+FLX=GP2_INF+GP=2+TP=fut+MOD=ind+VX=pas+P=3+NB=pl

        example return:
        [{
            "inflected form" : "amo",
            "lemma": "amare", # Optional
            "category": "V",
            "traits": {
                "Theme" : "INF",
                "FLX" : "GP1_INF",
                "GP" : "1",
            }
        },...]
    """

    lst = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Remove leading/trailing whitespace (newlines, spaces)
            line = line.strip()

            # Skip comment lines (starting with #) or empty lines
            if line.startswith("#"):
                continue
            line_lst = line.split(",")

            # Exlude lines that have no comma or more than 2 commas
            # Validate line structure: must have between 2 and 3 elements
            # (Form + Specs) OR (Form + Lemma + Specs)
            if not 2 <= len(line_lst) <= 3:
                continue

            dic_line = {}

            # 1. Extract the inflected form (always the first element)
            dic_line["inflected form"] = line_lst[0]

            # 2. Extract the lemma (if present, it is the second element in a 3-item line)
            if len(line_lst) > 2:
                dic_line["lemma"] = line_lst[1]

            # 3. Extract lexical specifications (always the last element)
            lexical_spec = line_lst[-1]

            # Split features separated by '+' (e.g., V+Theme=INF+...)
            lexical_spec_lst = lexical_spec.split("+")

            # The grammatical category is always the first item before the first '+'
            dic_line["category"] = lexical_spec_lst[0]

            # Initialize dictionary for morphological traits (attributes)
            dic_line["traits"] = {}

            # Iterate over the remaining attributes
            for trait in lexical_spec_lst:

                # Skip items that are not Key=Value pairs, i.e. the category
                if "=" not in trait:
                    continue
                trait_lst = trait.split("=")
                key = trait_lst[0]
                value = trait_lst[1]
                dic_line["traits"][key] = unescape(value)

            lst.append(dic_line)

    return lst


def unescape(txt: str):
    """
    Removes backslashes used to escape special NooJ characters.
    Example: "apple\\+pie" becomes "apple+pie".

    Args:
        txt (str): The raw string with escape characters.

    Returns:
        str: The clean string.
    """

    # List of special characters that NooJ escapes
    spec_char = ["\\", '"', " ", ",", "+", "-", "#"]

    for i, character in enumerate(txt):
        # Check if current char is a backslash and next char is a special character
        if character == "\\" and txt[i + 1] in spec_char:
            txt = txt[:i] + txt[i + 1 :]

    return txt


if __name__ == "__main__":
    print(read_dic(path))
