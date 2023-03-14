from collections import defaultdict
from copy import deepcopy
from typing import Dict, List, Tuple

import networkx as nx

Mention = Tuple[int, int]               # (start, end)
RawMarkable = List[str]                 # [T1, T2]
MarkableConnection = Tuple[str, str]    # (T1, T2)

Mentions = List[Mention]
Markables = Dict[str, Mentions]

Corefs = List[RawMarkable]
References = Dict[str, Corefs]

ClusterMapping = Dict[str, str]
ClusterList = List[List[str]]


def get_invalid_mention_links():
    # manually controlled invalid mention links
    invalid_mention_links = defaultdict(set)
    with open("ud_narc/conversion/invalid_mentions_links.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "#" not in line:
                doc_id, mlid = line.split()
                invalid_mention_links[doc_id].add(mlid)
    return invalid_mention_links


def get_continuous_spans(refs: List[str]) -> List[List[int]]:
    spans = []
    start = int(refs[0])
    for ref in refs[1:]:
        if ";" in ref:
            discont = ref.split(";")
            end = int(discont[0])
            spans.append([start, end])
            # do not include part of the discontinuity
            start = int(discont[1]) + 1
        else:
            end = int(ref)
            spans.append([start, end])
            start = end

    return spans


def get_references(
        ann_data: List[str],
        invalid_obj: List[str] = [],
        identifier: str = "T") -> Tuple[Markables, References]:

    markables: Markables = {}
    references: References = defaultdict(list)

    for line in ann_data:
        line_parts = line.split("\t")
        if len(line_parts) < 2:
            print(
                f"Line {line} is not a valid annotation -- Ignoring and continuing")
            continue

        _id, ref_data, *_ = line_parts
        if _id in invalid_obj:
            continue
        # markable
        if identifier in _id:
            _, *char_idx = ref_data.split()
            spans = get_continuous_spans(char_idx)
            # spans of the mention T55 in dot~20051126-525 are not in the right order
            spans.sort(key=lambda x: x[0])
            markables[_id] = spans
        # coref
        else:
            _type, arg1, arg2 = ref_data.split()
            arg1 = arg1.split(":")[-1]
            arg2 = arg2.split(":")[-1]
            link: RawMarkable = [arg1, arg2]
            references[_type].append(link)

    return markables, references


def cluster_references(corefs: Corefs) -> List[MarkableConnection]:
    # treat coreference links as edges in a graph
    # clusters are then connected components of the graph
    coref_graph = nx.Graph()
    for arg1, arg2 in corefs:
        coref_graph.add_edge(arg1, arg2)
    return [list(c) for c in nx.connected_components(coref_graph)]


def get_reference_content(
    markables: Markables,
    references: References
) -> Tuple[ClusterMapping, ClusterList]:

    cluster_map: ClusterMapping = {}
    clustered_references: List[MarkableConnection] = cluster_references(
        deepcopy(references["Coref"]))

    for cluster in clustered_references:
        # to identify the cluster in jsonl format
        concatenated_cluster = "_".join(cluster)
        cluster_map.update({mark: concatenated_cluster for mark in cluster})

    parsed_clusters = []
    for cluster in clustered_references:
        tmp_cluster = []
        for markable in cluster:
            if markable not in markables:
                print(f"Markable {markable} not found in markables")
                continue
            markable_spans = markables[markable]
            for span in markable_spans:
                tmp_cluster.append(span)
        parsed_clusters.append(tmp_cluster)

    return cluster_map, parsed_clusters


def extract_token_mapping(
        text: str
) -> Tuple[List[List[str]], List[str], Dict[int, int]]:

    current_word_idx = 0
    tokens = []
    sentences = []

    current_token = ""

    current_sentence = []
    char_to_word_map = {}

    for char_index, char in enumerate(text):
        char_to_word_map[char_index] = current_word_idx
        if char in [" ", "\n"]:
            tokens.append(current_token)
            current_sentence.append(current_token)
            current_token = ""
            current_word_idx += 1
            if char == "\n":
                sentences.append(current_sentence)
                current_sentence = []
        else:
            current_token += char
    return sentences, tokens, char_to_word_map


def markable_char_to_word(
    markables: Markables,
    char_to_word_map: Dict[int, int]
) -> Dict[int, List[Tuple[int, int]]]:

    markable_by_word = {}

    for markable_id, spans in markables.items():
        word_spans = []
        for start, end in spans:
            w_start = char_to_word_map[start]
            w_end = char_to_word_map[end]
            word_spans.append((w_start, w_end))
        markable_by_word[markable_id] = word_spans

    return markable_by_word
