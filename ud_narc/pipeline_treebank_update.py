import os

from align_treebank import align_treebank

ud_treebanks = {
    "bokmål": os.path.join(os.getcwd(), "data", "UD", "UD_Norwegian-Bokmaal"),
    "nynorsk": os.path.join(os.getcwd(), "data", "UD", "UD_Norwegian-Nynorsk"),
}

other_treebanks = {
    "norne": {
        "bokmål": os.path.join(os.getcwd(), "data", "norne", "ud", "nob"),
        "nynorsk": os.path.join(os.getcwd(), "data", "norne", "ud", "nno"),
    }
}

if __name__ == "__main__":
    lang = "bokmål"
    corpus = "norne"

    ud_path = ud_treebanks[lang]
    outdated_treebank_path = other_treebanks[corpus][lang]
    output_path = os.path.join(os.getcwd(), "output", "aligned")
    align_treebank(outdated_treebank_path, ud_path, output_path)
