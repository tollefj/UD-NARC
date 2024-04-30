# from sklearn.preprocessing import LabelEncoder
import os
import random
import re
import sys
from collections import defaultdict
from typing import List, Tuple

import conllu
import jsonlines


def is_new_doc(sample):
    return "newdoc id" in sample.metadata


def get_grouped_docs(data):
    # a new document will always start with "newdoc id" in the metadata field
    # group all documents by their id.
    grouped_docs = defaultdict(list)
    current_doc = None
    for sent in data:
        if is_new_doc(sent):
            current_doc = sent.metadata["newdoc id"]
        grouped_docs[current_doc].append(sent)
    return grouped_docs


# Define a regular expression pattern to match CoNLL-style mention annotations
# TODO: use udapi
# doc ids = []
# given path: "conll file"
# raw = Path(path).read_text()
# for t in raw.split("# newdoc id"):
#     if "# text =" in t:
#         st = "# newdoc id"+t+"In\n"
#         a=Document()
#         a.from_conllu_string(st)
#         doc_ids.append(a)
# for ent in doc_ids[0].coref_entities:
#     bridging = ent.all_bridgning()
#     splits = ent.split_ante
#     corefs = ent.mentions # [e.words for e in ent.mentions]

pattern = r"\((?P<mono>\w+)\)|\((?P<start>\w+)|(?P<end>\w+)\)"
CONLL_MENTION_PATTERN = re.compile(pattern)


def clean_column(col):
    # if there's any hyphen, keep only the first part :-)
    if "-" in col:
        col = col.split("-")[0]
    return col


def group_and_rename(mention: re.Match) -> str:
    # from e.g.
    # ap_20011210_242954__T1
    # to
    # T1
    chain = mention.group(mention.lastgroup)
    if "__" in chain:
        return chain.split("__")[-1]
    return chain


def compute_mentions(columns: List[str]) -> List[Tuple[Tuple[int, int], str]]:
    pending = defaultdict(list)
    mentions = []

    for i, col in enumerate(columns):
        if not col:
            continue
        col = clean_column(col)

        for m in CONLL_MENTION_PATTERN.finditer(col):
            # If the annotation is a singleton mention, add it to the mentions list
            if m.lastgroup == "mono":
                pos = (i, i + 1)
                chain = group_and_rename(m)
                mentions.append((pos, chain))
            # If the annotation is a start tag, add it to the pending list
            elif m.lastgroup == "start":
                chain = group_and_rename(m)
                if chain not in pending:
                    pending[chain] = []
                pending[chain].append(i)
            # If the annotation is an end tag, retrieve the corresponding start tag
            # from the pending list and add the mention to the mentions list
            elif m.lastgroup == "end":
                chain = group_and_rename(m)
                if len(pending[chain]) == 0:
                    continue
                pos = (pending[chain].pop(), i + 1)
                mentions.append((pos, chain))
            else:
                # This should never happen
                assert False

    return mentions


def compute_chains(columns):
    chains = dict()

    for (start, stop), chain_id in compute_mentions(columns):
        end = stop - 1
        if chain_id not in chains:
            chains[chain_id] = []
        chains[chain_id].append((start, end))

    return list(chains.values())


def get_coref_clusters_from_doc(doc):
    misc = []
    for s_id, sent in enumerate(doc):
        sent_misc = []
        for token in sent:
            # get misc if it exists:
            if "misc" in token and token["misc"] is not None:
                _misc = token["misc"]
                entity = _misc.get("Entity", None)
                sent_misc.append(entity)
            else:
                sent_misc.append(None)
        misc.extend(sent_misc)

    chains = compute_chains(misc)  # if you want a spacy-like mapping
    return chains


def get_head(mention: Tuple[int, int], heads: List[int]) -> int:
    """Returns the span's head, which is defined as the only word within the
    span whose head is outside of the span or None. In case there are no or
    several such words, the rightmost word is returned
    Args:
        mention (Tuple[int, int]): start and end (exclusive) of a span
        doc (dict): the document data
    Returns:
        int: word id of the spans' head
    """
    head_candidates = set()
    start, end = mention
    for i in range(start, end + 1):
        ith_head = heads[i]
        if ith_head is None or not (start <= ith_head < end):
            head_candidates.add(i)
    if len(head_candidates) == 1:
        return head_candidates.pop()
    return end - 1


def parse_doc(doc, part_id=None):
    """_summary_
    Args:
        doc (_type_): documents corresponding to a single document id
        part_id (_type_, optional): just the document counter
    Returns:
        _type_: a dictionary of the following structure:

        document_id:    str,
        cased_words:    [str, ...]                # words
        sent_id:        [int, ...]                # word id to sent id
        part_id:        [int, ...]                # word id to part id
        speaker:        [str, ...]                # word id to speaker
        pos:            [str, ...]                # word id to POS
        deprel:         [str, ...]                # word id to dep. relation
        head:           [int, ...]                # word id to head, None for root
        clusters:       [[[int, int], ...], ...]  # list of clusters, where each
                                                    cluster is
                                                    a list of spans of words
    """

    doc_id = doc[0].metadata["newdoc id"]
    cased_words = [word["form"] for sent in doc for word in sent]

    sent_id = []  # create a sentence mapping starting from 0
    current_sent = 0
    for sent in doc:
        sent_id.extend([current_sent] * len(sent))
        current_sent += 1

    speakers = [0] * len(cased_words)

    pos = [word["upos"] for sent in doc for word in sent]
    deprel = [word["deprel"] for sent in doc for word in sent]
    heads = [word["head"] for sent in doc for word in sent]
    feats = [word["feats"] for sent in doc for word in sent]

    heads = []
    # we need to build the proper heads, as they are...
    # 1) indexed on token ID (1-indexed, not 0)
    # 2) grounded per sentence
    token_count = 0
    missed = 0
    added_heads = 0
    added_roots = 0

    # speakers = []

    for sent in doc:
        # a sentence can have the speaker metadata attribute,
        # add it for the entire sentence if so
        # if "sentences" in sent.metadata:
        #     speakers.extend([sent.metadata["sentences"]["speaker"]] * len(sent))
        # else:
        #     speakers.extend([None] * len(sent))
        for word in sent:
            # check if this is a root:
            if word["deprel"] == "root":
                heads.append(None)
            elif word["head"]:
                word_head = int(word["head"])
                heads.append(token_count + word_head - 1)
            else:
                heads.append(None)

        token_count += len(sent)

    # label encode (None -> 0, "Name" -> 1, "Another name" -> 2, etc.)
    # le_enc = LabelEncoder()
    # fit on speakers:
    # speakers = le_enc.fit_transform(speakers)

    # now we need to group all coreference clusters...
    clusters = get_coref_clusters_from_doc(doc)
    span_clusters = []
    singletons = []
    for cl in clusters:
        if len(cl) == 1:
            singletons.append(cl)
        else:
            span_clusters.append(cl)

    data = {
        "document_id": doc_id,
        "cased_words": cased_words,
        "sent_id": sent_id,
        # "part_id":          [part_id] * len(cased_words),
        # "part_id": part_id,
        # "speaker": speakers,
        "pos": pos,
        "deprel": deprel,
        "head": heads,
        # "feats": feats,
        "clusters": span_clusters,
        "mentions": clusters,
    }
    return data


def parse_path(path):
    parsed_docs = []
    with open(path, encoding="utf-8") as f:
        grouped_docs = get_grouped_docs(conllu.parse(f.read()))
        for part_id, _doc in enumerate(grouped_docs.values()):
            parsed_docs.append(parse_doc(_doc, part_id=part_id))
    return parsed_docs


if __name__ == "__main__":
    in_path, out_path = sys.argv[1], sys.argv[2]
    with open(in_path, encoding="utf-8") as f:
        grouped_docs = get_grouped_docs(conllu.parse(f.read()))
        filename = in_path.split("/")[-1].replace(".conllu", "")
        out_path = os.path.join(out_path, filename + ".jsonl")

        with jsonlines.open(out_path, mode="w") as writer:
            for part_id, _doc in enumerate(grouped_docs.values()):
                parsed = parse_doc(_doc, part_id=part_id)
                writer.write(parsed)
