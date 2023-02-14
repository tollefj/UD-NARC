import os
import re
from conllu import parse
from conllu.models import SentenceList

from custom_types import ConlluType
from typing import List, Dict

SEP = "\t"
NEWLINE = "\n"
EMPTY = "_"
            
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zæøåA-ZÆØÅ0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def sort_entity_groups(ents: List[Dict[str, str]]):
    ents = sorted(ents, key=lambda ent: ent["start"], reverse=True)
    # B: beginning entity
    # E: ending entity
    # S: single-node entity
    # use a stack to alter the order of the entities
    opening_ents = [e for e in ents if e["node_type"] == "B"]
    closing_ents = [e for e in ents if e["node_type"] == "E"]
    singlenode_ents = [e for e in ents if e["node_type"] == "S"]

    # opening ents are sorted by MAX index of the entity span,
    # as they are the last entity to be opened
    # opening ents should be sorted by the LENGTH OF THE SPAN MENTION
    def sort_span_length(ent):
        return ent["end"] - ent["start"]
    opening_ents = sorted(opening_ents, key=sort_span_length, reverse=True)
    
    entity_stack = []
    # If there are no closing entity brackets
    # single-node entity must follow all opening entity brackets
    if len(closing_ents) == 0:
        entity_stack.extend(opening_ents)
        entity_stack.extend(singlenode_ents)
    # Single-node entity must either precede all
    # closing entity brackets or follow all opening entity brackets
    elif len(opening_ents) == 0:
        entity_stack.extend(singlenode_ents)
        entity_stack.extend(closing_ents)
    elif len(singlenode_ents) == 0:
        entity_stack.extend(closing_ents)
        entity_stack.extend(opening_ents)
    else:
        entity_stack.extend(singlenode_ents)
        entity_stack.extend(closing_ents)
        entity_stack.extend(opening_ents)

    return entity_stack


def make_misc_string(parser, token_index):
    """
    first, handle entities,
    then append the rest of the misc fields
    """
    _misc_dict = parser.misc_dict[token_index]

    # entities = parser.entity_info[token_index]
    entities = []
    for ent in parser.entity_info[token_index]:
        if ent["m_id"] not in entities:
            entities.append(ent)

    _misc_list = []
    for key, value in _misc_dict.items():
        # Split antecedents must have at least two elements...
        if ConlluType.SPLIT.value == key and len(value) < 2:
            continue
        value_string = ",".join(value)
        _misc_list.append(f"{key}={value_string}")
    
    if len(entities) > 0:
        # sort the entities!
        entities = sort_entity_groups(entities)
        ent_ids = [ent["id"] for ent in entities]
        # _misc_dict[ConlluType.ENTITY.value] = ent_ids
        # add all the entities to the misc string
        _misc_list.append(f"{ConlluType.ENTITY.value}={''.join(ent_ids)}")
    
    return "|".join(_misc_list) if len(_misc_list) > 0 else EMPTY


def make_conllu_line(token_id, token, misc):
    """ Format following the CoNLLU standard:
    ID: Word index, integer starting at 1 for each new sentence; may be a range for multiword tokens; may be a decimal number for empty nodes (decimal numbers can be lower than 1 but must be greater than 0).
    FORM: Word form or punctuation symbol.
    LEMMA: Lemma or stem of word form.
    UPOS: Universal part-of-speech tag.
    XPOS: Language-specific part-of-speech tag; underscore if not available.
    FEATS: List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
    HEAD: Head of the current word, which is either a value of ID or zero (0).
    DEPREL: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
    DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.
    MISC: Any other annotation.
    """
    # these are later merged with available UD data
    conllu_dict = {
        "ID": str(token_id + 1),
        "FORM": token,
        "LEMMA": "_",
        "UPOS": "_",
        "XPOS": "_",
        "FEATS": "_",
        "HEAD": "_",
        "DEPREL": "_",
        "DEPS": "_",
        "MISC": misc
    }
    return SEP.join(conllu_dict.values()) + NEWLINE

def get_ud_splits(language: str) -> Dict[str, List[Dict[str, SentenceList]]]:
    ud_folder = f"../../data/norne-merged/"
    ud_id = f"no_{language}-ud-"

    ud_train = os.path.join(ud_folder, f"{ud_id}train.conllu")
    ud_test = os.path.join(ud_folder, f"{ud_id}test.conllu")
    ud_dev = os.path.join(ud_folder, f"{ud_id}dev.conllu")

    return {
        "train": parse(open(ud_train, "r", encoding="utf-8").read()),
        "test": parse(open(ud_test, "r", encoding="utf-8").read()),
        "dev": parse(open(ud_dev, "r", encoding="utf-8").read())
    }
