import re
from custom_types import ConlluType
from typing import List, Dict
from util import SEP, EMPTY



def make_feature_connection(start: int, end: int, _type: str = None) -> str:
    """
    Args:
        start (int): _description_
        end (int): _description_
        _type (str, optional): _description_. Defaults to "default".
    Returns:
        str: a string of the form: name=start<end:type for Bridging and Split antecedent
    """
    return f"{end}<{start}{f':{_type}' if _type else ''}"


def make_markable(_id, m_id, etype, start, end):
    return {
        "node_type": etype,  # B: beginning mark, E: end mark, S: single-node
        "start": start,
        "end": end,
        "id": _id,
        "m_id": m_id  # the markable without parentheses
    }


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


def make_misc_string(misc, ents):
    """
    first, handle entities,
    then append the rest of the misc fields
    """
    entities = []
    for ent in ents:
        if ent["m_id"] not in entities:
            entities.append(ent)

    _misc_list = []
    for key, value in misc.items():
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
    return SEP.join(conllu_dict.values())
