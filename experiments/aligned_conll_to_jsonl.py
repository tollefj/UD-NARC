from typing import Tuple, List
import jsonlines
import conllu
import re
from collections import defaultdict
import os


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
CONLL_MENTION_PATTERN = re.compile(
    r'(?:\((?P<mono>\d+)\)|\((?P<start>\d+)|(?P<end>\d+)\))')

def compute_mentions(columns):
    # Use a dictionary to keep track of pending mentions waiting for an "end" tag
    pending = defaultdict(list)
    mentions = []

    # Iterate over each column in the input
    for i, col in enumerate(columns):
        # Find all CoNLL-style mention annotations in the column using the regex pattern
        for m in CONLL_MENTION_PATTERN.finditer(col):
            # If the annotation is a singleton mention, add it to the mentions list
            if m.lastgroup == 'mono':
                pos = (i, i+1)
                chain = int(m.group(m.lastgroup))
                mentions.append((pos, chain))
            # If the annotation is a start tag, add it to the pending list
            elif m.lastgroup == 'start':
                chain = int(m.group(m.lastgroup))
                if chain not in pending:
                    pending[chain] = []
                pending[chain].append(i)
            # If the annotation is an end tag, retrieve the corresponding start tag
            # from the pending list and add the mention to the mentions list
            elif m.lastgroup == 'end':
                chain = int(m.group(m.lastgroup))
                pos = (pending[chain].pop(), i+1)
                mentions.append((pos, chain))
            else:
                # This should never happen
                assert False

    return mentions


def compute_chains(columns):
    # Use a dictionary to keep track of chains, where the key is the chain ID
    # and the value is a list of (start, end) tuples representing the spans of
    # the mentions in the chain
    chains = dict()

    # Iterate over each mention in the input and add it to the appropriate chain
    for (start, stop), chain_id in compute_mentions(columns):
        end = stop - 1
        if chain_id not in chains:
            chains[chain_id] = []
        chains[chain_id].append((start, end))

    # Return the list of chains (i.e., the values of the chains dictionary)
    return list(chains.values())

def get_coref_clusters_from_doc(doc):
    misc = []
    for s_id, sent in enumerate(doc):
        sent_misc = []
        for token in sent:
            _misc = token.get("misc", None)
            entity = _misc.get("Entity", None)
            sent_misc.append(entity if entity else "*")
        misc.extend(sent_misc)

    clusters = compute_chains(misc)
    return clusters

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
        _type_: jsonlines formatted data
    """
    doc_id = doc[0].metadata["newdoc id"]
    cased_words = [word["form"] for sent in doc for word in sent]

    sent_id = []  # create a sentence mapping starting from 0
    current_sent = 0
    for sent in doc:
        sent_id.extend([current_sent] * len(sent))
        current_sent += 1

    speaker = ["blank"] * len(cased_words)

    pos = [word["upos"] for sent in doc for word in sent]
    deprel = [word["deprel"] for sent in doc for word in sent]
    
    heads = []
    # we need to build the proper heads, as they are...
    # 1) indexed on token ID (1-indexed, not 0)
    # 2) grounded per sentence
    token_count = 0
    for sent in doc:
        for word in sent:
            word_head = word["head"]
            if word_head == 0:
                # this is a root, append None
                heads.append(None)
            else:
                heads.append(token_count + word_head - 1)
        token_count += len(sent)

    # now we need to group all coreference clusters...
    clusters = get_coref_clusters_from_doc(doc)
    span_clusters = []
    singletons = []
    for cl in clusters:
        if len(cl) == 1:
            singletons.append(cl)
        else:
            span_clusters.append(cl)

    ###############
    # this is the "to_heads" functionality from wl-coref
    ###############
    head_clusters = [
        [get_head(mention, heads) for mention in cluster]
        for cluster in clusters
    ]
    # check for duplicates
    head2spans = defaultdict(list)
    for cluster, head_cluster in zip(clusters, head_clusters):
        for span, span_head in zip(cluster, head_cluster):
            head2spans[span_head].append((span, head_cluster))

    filtered_head2spans = []
    for head, spans in head2spans.items():
        spans.sort(key=lambda x: x[0][1] - x[0][0])  # shortest spans first
        filtered_head2spans.append((head, *spans[0][0]))
        if len(spans) > 1:
            for _, cluster in spans[1:]:
                cluster.remove(head)

    filtered_head_clusters = [
        cluster for cluster in head_clusters if len(cluster) > 1]

    data = {
        "document_id":      doc_id,
        "cased_words":      cased_words,
        "sent_id":          sent_id,
        "part_id":          part_id,
        # "speaker":          speaker,
        "pos":              pos,
        "deprel":           deprel,
        "head":             heads,
        "clusters":         clusters,  # all clusters, both singleton + spans
        "mentions":         singletons,
        "span_clusters":    span_clusters,
        "word_clusters":    filtered_head_clusters,
        "head2span":        filtered_head2spans,
    }
    return data


langs = ["bokmaal", "nynorsk"]
part_id = 0

for lang in langs:
    for split in ["train", "dev", "test"]:
        new_path = f"../output/aligned_jsonl/no-narc_{lang}"
        os.makedirs(new_path, exist_ok=True)

        conll_path = f"../output/aligned/no-narc_{lang}/narc_{lang}_{split}.conllu"
        data = conllu.parse(open(conll_path, encoding="utf-8").read())
        grouped_docs = get_grouped_docs(data)

        with jsonlines.open(os.path.join(new_path, f"{split}.jsonl"), mode="a") as writer:
            for _doc in grouped_docs.values():
                part_str = str(part_id).zfill(3)
                part_id += 1
                parsed = parse_doc(_doc, part_str)
                writer.write(parsed)