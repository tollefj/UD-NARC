from collections import defaultdict
from copy import deepcopy
import networkx as nx

from typing import Dict, List, Tuple

def get_continuous_spans(refs):
    spans = []
    start = int(refs[0])
    for ref in refs[1:]:
        if ";" in ref:
            discont = ref.split(";")
            end = int(discont[0])
            spans.append([start, end])
            start = int(discont[1]) + 1  # do not include part of the discontinuity
        else:
            end = int(ref)
            spans.append([start, end])
            start = end

    return spans

def get_references(ann_data, invalid_obj=[], identifier="T"):
    markables: Dict[str, List[Tuple[int, int]]] = {}
    references: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    for line in ann_data:
        line_parts = line.split("\t")
        if len(line_parts) < 2:
            print(f"Line {line} is not a valid annotation -- Ignoring and continuing")
            continue

        _id, ref_data, *_ = line_parts
        if _id in invalid_obj:
            continue
        if identifier in _id:
            _, *char_idx = ref_data.split()
            spans = get_continuous_spans(char_idx)
            # spans of the mention T55 in dot~20051126-525 are not in the right order
            spans.sort(key=lambda x: x[0])
            markables[_id] = spans
        else:
            _type, arg1, arg2 = ref_data.split()
            arg1 = arg1.split(":")[-1]
            arg2 = arg2.split(":")[-1]
            references[_type].append([arg1, arg2])
    return markables, references

def cluster_references(corefs):
    # treat coreference links as edges in a graph
    # clusters are then connected components of the graph
    coref_graph = nx.Graph()
    for arg1, arg2 in corefs:
        coref_graph.add_edge(arg1, arg2)
    return [list(c) for c in nx.connected_components(coref_graph)]

def get_reference_content(from_file, invalid_obj):
    if ".ann" not in from_file:
        raise FileNotFoundError("No .ann file provided")

    with open(from_file, "r", encoding="utf-8") as ann:
        markables, references = get_references(ann.readlines(), invalid_obj)

    cluster_map = {}
    clustered_references = cluster_references(deepcopy(references["Coref"]))
    for cluster in clustered_references:
        concatenated_cluster = "_".join(cluster)  # to identify the cluster in jsonl format
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

    return markables, references, cluster_map, parsed_clusters

def extract_token_mapping(text):
    current_word_idx = 0
    tokens = []
    sentences = []

    current_token = ""

    current_sentence = []
    char_to_word_map = {}

    for char_index, char in enumerate(text):
        char_to_word_map[char_index] = current_word_idx
        if char == " ":
            tokens.append(current_token)
            current_sentence.append(current_token)
            current_token = ""
            current_word_idx += 1
        elif char == "\n":
            tokens.append(current_token)
            current_sentence.append(current_token)
            current_token = ""
            current_word_idx += 1

            sentences.append(current_sentence)
            current_sentence = []
        else:
            current_token += char
    return sentences, tokens, char_to_word_map

def markable_char_to_word(markables, char_to_word_map):
    markable_by_word = {}

    # rewrite to handle the continuous spans of a markable:
    for markable_id, spans in markables.items():
        w_spans = []
        for start, end in spans:
            w_start = char_to_word_map[start]
            w_end = char_to_word_map[end]
            w_spans.append((w_start, w_end))
        markable_by_word[markable_id] = w_spans

    return markable_by_word

def convert(from_file: str, invalid_obj):
    """ given a .ann file, output the required data for producing a json line
    """
    markables, references, cluster_map, clustered_corefs = get_reference_content(from_file, invalid_obj)
    txt_path = from_file.split(".ann")[0] + ".txt"
    with open(txt_path, "r", encoding="utf-8") as txt:
        text = "".join(txt.readlines())

    sents, tokens, char_to_word_map = extract_token_mapping(text)
    markable_by_word = markable_char_to_word(markables, char_to_word_map)

    return sents, tokens, markable_by_word, references, cluster_map, clustered_corefs
