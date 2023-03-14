import os
from typing import Dict, List

from conllu import parse
from conllu.models import SentenceList

SEP = "\t"
NEWLINE = "\n"
EMPTY = "_"


def get_ud_splits(ud_folder: str, language: str) -> Dict[str, List[Dict[str, SentenceList]]]:
    ud_id = f"no_{language}-ud-"

    ud_train = os.path.join(ud_folder, f"{ud_id}train.conllu")
    ud_test = os.path.join(ud_folder, f"{ud_id}test.conllu")
    ud_dev = os.path.join(ud_folder, f"{ud_id}dev.conllu")

    return {
        "train": parse(open(ud_train, "r", encoding="utf-8").read()),
        "test": parse(open(ud_test, "r", encoding="utf-8").read()),
        "dev": parse(open(ud_dev, "r", encoding="utf-8").read())
    }
