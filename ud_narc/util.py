import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from conllu import parse
from conllu.models import SentenceList

SEP = "\t"
NEWLINE = "\n"
EMPTY = "_"


class Language(Enum):
    BOKMAAL = "bokmaal"
    NYNORSK = "nynorsk"


@dataclass
class Paths:
    train: str
    test: str
    dev: str


def get_ud_splits(
    ud_folder: str, language: str
) -> Dict[str, List[Dict[str, SentenceList]]]:
    ud_id = f"no_{language}-ud-"

    ud_train = os.path.join(ud_folder, f"{ud_id}train.conllu")
    ud_test = os.path.join(ud_folder, f"{ud_id}test.conllu")
    ud_dev = os.path.join(ud_folder, f"{ud_id}dev.conllu")

    return {
        "train": parse(open(ud_train, "r", encoding="utf-8").read()),
        "test": parse(open(ud_test, "r", encoding="utf-8").read()),
        "dev": parse(open(ud_dev, "r", encoding="utf-8").read()),
    }


def get_paths(
    path: str,
    file_ext=".conllu",
    train_key="train",
    test_key="test",
    dev_key="dev",
) -> Paths:
    """
    Retrieves the paths to the train, test, and dev CoNLL-U format files for a corpus.

    Args:
        path (str): The path to the corpus directory.

    Returns:
        Paths: A Paths object containing the paths to the train, test, and dev files.
    """
    files = [
        os.path.join(path, file) for file in os.listdir(path) if file.endswith(file_ext)
    ]

    return Paths(
        train=[f for f in files if train_key in f][0],
        test=[f for f in files if test_key in f][0],
        dev=[f for f in files if dev_key in f][0],
    )
