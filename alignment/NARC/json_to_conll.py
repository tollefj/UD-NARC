from collections import defaultdict
from typing import Dict, List, Set

from custom_types import ConlluType, NARCType


def make_feature_connection(start: int, end: int, _type :str=None) -> str:
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

class ConlluParser:
    def __init__(self, json_data: Dict, invalid_ents: Set) -> None:
        self.misc_dict = defaultdict(lambda : defaultdict(list))
        # keep start, singletons and ends as separate lists
        self.entity_info = defaultdict(list)

        # all clusters, including features such as coref, split and bridge
        self.data = json_data
        self.tokens = json_data["tokens"]
        self.filename = json_data["doc_key"]
        self.clusters = json_data["references"]
        self.markables = json_data["markables"]
        self.cluster_map = json_data["cluster_map"]  # the mapping of coreference clusters to markables

        self.invalid_entities = invalid_ents


    def enrich_markable(self, markable):
        # there's two options here:
        # 1. the markable is a coreference cluster, with multiple markables
        # 2. the markable (T1) is a singleton
        filename = self.filename.replace("-", "_").lower()
        # filename = ""
        mark_id = f"{filename}__{markable}"
        if markable in self.cluster_map:
            _map = self.cluster_map[markable]
            cluster_values = [int(t[1:]) for t in _map.split("_")]
            mark_id = f"{filename}__{len(cluster_values)}{sum(cluster_values)}"

        if mark_id in self.invalid_entities:
            return None
        return mark_id

    def parse(self, features):
        self.populate_entities()
        self.add_feature(*features)

    def populate_entities(self):
        etype_head_other = "--1-"
        # iterate singletons first! we reorder later
        # this is done to check if the entity exists.
        added_spans = set()

        for markable, span in self.markables.items():
            # adjust span...
            # we then skip the pipe character
            for span_idx, (start, end) in enumerate(span):
                # or check the pipe condition. if so,
                # check if end - 1 is in added spans
                error_span_chars = ["|", ".", "...", ":", ";", "!", "?"]
                if self.tokens[end] in error_span_chars:
                    # there are cases of the pipe character
                    # appearing in discont. spans in NARC
                    # e.g. "T2	Markable 0 11;29 30	Mer frukt , |"
                    # (doc: db~20081118-3754590)
                    # this results in "|" as the entity
                    # ...which does not exist in UD
                    if start == end:
                        start -= 1
                    end -= 1

                if (start, end) in added_spans:
                    continue

                m_id = self.enrich_markable(markable)
                if not m_id:  # skip invalid entities
                    continue

                # add the part of the markable span if the length > 1
                # e.g. [1/4], [2/4], [3/4], [4/4]
                if len(span) > 1:
                    m_id = f"{m_id}[{span_idx + 1}/{len(span)}]"

                e_id_start = f"({m_id}{etype_head_other}"
                e_id_end = f"{m_id})"

                if start == end:  # fully closed entity
                    e_id = f"({m_id}{etype_head_other})"
                    self.entity_info[start].append(make_markable(e_id, m_id, "S", start, end, ))

                elif self.tokens[end] in error_span_chars:
                    # correct for end markables sometimes occurring at a pipe
                    # e.g. "Stolte spillere |", which does not occur for UD
                    # we simply adjust to the previous token...
                    if end - start == 1:
                        e_id_start = f"{e_id_start})"  # close the entity
                        self.entity_info[start].append(make_markable(e_id_start, m_id, "S", start, start))
                    else:
                        self.entity_info[start].append(make_markable(e_id_start, m_id, "B", start, start))
                        self.entity_info[end-1].append(make_markable(e_id_end, m_id, "E", start, end - 1))
                        added_spans.add((start, end - 1))

                else:
                    self.entity_info[start].append(make_markable(e_id_start, m_id, "B", start, end))
                    self.entity_info[end].append(make_markable(e_id_end, m_id, "E", start, end))
                added_spans.add((start, end))

    def add_span(self, start: int, end: int):
        span_name = ConlluType.SPAN.value
        if (end - start) > 0:
            self.misc_dict[start][span_name].append(f"{span_name}={start}-{end}")

    def append_feature_pair(self, link, feature_key):
        feature_name = ConlluType[feature_key.name].value
        feature_type = "default" if feature_key == NARCType.BRIDGE else None
        t_start, t_end = link
        referring_index = 0 
        # https://github.com/ufal/corefUD/issues/68
        # from the spans, select the last part of the span
        # e.g. if the span is [1/4], [2/4], [3/4], [4/4]
        # place the bridge at the first mention of the span [1/4]
        referring_markable = self.markables[t_start][0][referring_index]
        entity_start = self.enrich_markable(t_start)
        entity_end = self.enrich_markable(t_end)

        if not entity_start or not entity_end:
            return

        if entity_start != entity_end:
            self.misc_dict[referring_markable][feature_name].append(
                make_feature_connection(entity_start, entity_end, _type=feature_type)
            )
                
    def add_feature(self, *feature_keys: List[NARCType]):
        # add additional coref-like clusters,
        # following the same format as coref-clusters
        # in this case, Bridging and Split_antecedent
        for feature_key in feature_keys:
            if feature_key.value not in self.clusters:
                continue
            for link in self.clusters[feature_key.value]:
                self.append_feature_pair(link, feature_key)
