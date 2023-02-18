import json
import os
from collections import defaultdict

from custom_types import ConlluType, FileTypes, NARCType
from util import NEWLINE, make_conllu_line, make_misc_string


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


class Json2Conll:
    ERROR_SPAN_CHARS = ["|", ".", "...", ":", ";", "!", "?"]
    FROM_FILE = FileTypes.JSON.value
    TO_FILE = FileTypes.CONLL.value
    FEATURES = [NARCType.BRIDGE, NARCType.SPLIT]

    def __init__(self, in_file: str) -> None:
        self.load(in_file)

        self.misc_dict = defaultdict(lambda: defaultdict(list))
        # keep start, singletons and ends as separate lists
        self.entity_info = defaultdict(list)

        # all clusters, including features such as coref, split and bridge
    def load(self, in_file):
        with open(in_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

            self._id = json_data["doc_key"]
            self.tokens = json_data["tokens"]
            self.sentences = json_data["sentences"]
            self.clusters = json_data["references"]
            self.markables = json_data["markables"]
            self.cluster_map = json_data["cluster_map"]
            # the mapping of coreference clusters to markables

    def enrich_markable(self, markable):
        # there's two options here:
        # 1. the markable is a coreference cluster, with multiple markables
        # 2. the markable (T1) is a singleton
        filename = self._id.replace("-", "_").lower()
        # filename = ""
        mark_id = f"{filename}__{markable}"
        if markable in self.cluster_map:
            _map = self.cluster_map[markable]
            cluster_values = [int(t[1:]) for t in _map.split("_")]
            mark_id = f"{filename}__{len(cluster_values)}{sum(cluster_values)}"

        return mark_id

    def parse(self):
        self.strip_trailing_punct()
        self.populate_entities()
        for feature in self.FEATURES:
            self.add_feature(feature)

    def strip_trailing_punct(self):
        mentions_to_remove = set()
        for markable in self.markables:
            # adjust span...
            # we then skip the pipe character
            span = self.markables[markable]
            span_to_remove = set()
            for i in range(len(span)):
                # get rid of the punctuation that ends the mention span or its any continuous part
                if self.tokens[span[i][1]] in self.ERROR_SPAN_CHARS:
                    # there are cases of the pipe character
                    # appearing in discont. spans in NARC
                    # e.g. "T2	Markable 0 11;29 30	Mer frukt , |"
                    # (doc: db~20081118-3754590)
                    # this results in "|" as the entity
                    # ...which does not exist in UD
                    span[i][1] -= 1
                # if the mention end precedes the its start, label the span part to be removed
                if span[i][1] < span[i][0]:
                    span_to_remove.add(i)
            if len(span_to_remove) == len(span):
                mentions_to_remove.add(markable)
            else:
                self.markables[markable] = [
                    part for i, part in enumerate(span) if i not in span_to_remove]
        self.markables = {
            k: v for k, v in self.markables.items() if k not in mentions_to_remove}

    def populate_entities(self):
        etype_head_other = "--1-"
        # iterate singletons first! we reorder later
        # this is done to check if the entity exists.
        added_spans = set()

        for markable, span in self.markables.items():
            m_base_id = self.enrich_markable(markable)

            frozenspan = tuple(tuple(s) for s in span)
            if frozenspan in added_spans:
                print(
                    f"[WARN] Skipping mention spanning {frozenspan} of the cluster {m_base_id}.")
                continue

            if not m_base_id:  # skip invalid entities
                continue

            added_spans.add(frozenspan)

            for span_idx, (start, end) in enumerate(span):
                m_id = m_base_id

                # add the part of the markable span if the length > 1
                # e.g. [1/4], [2/4], [3/4], [4/4]
                if len(span) > 1:
                    m_id = f"{m_id}[{span_idx + 1}/{len(span)}]"

                e_id_start = f"({m_id}{etype_head_other}"
                e_id_end = f"{m_id})"

                if start == end:  # fully closed entity
                    e_id = f"({m_id}{etype_head_other})"
                    self.entity_info[start].append(
                        make_markable(e_id, m_id, "S", start, end, ))
                else:
                    self.entity_info[start].append(
                        make_markable(e_id_start, m_id, "B", start, end))
                    self.entity_info[end].append(
                        make_markable(e_id_end, m_id, "E", start, end))

    def add_span(self, start: int, end: int):
        span_name = ConlluType.SPAN.value
        if (end - start) > 0:
            self.misc_dict[start][span_name].append(
                f"{span_name}={start}-{end}")

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
                make_feature_connection(
                    entity_start, entity_end, _type=feature_type)
            )

    def add_feature(self, feature_key):
        # add additional coref-like clusters,
        # following the same format as coref-clusters
        # in this case, Bridging and Split_antecedent
        if feature_key.value not in self.clusters:
            return 
        for link in self.clusters[feature_key.value]:
            self.append_feature_pair(link, feature_key)

    def write(self, out_file):
        with open(os.path.join(out_file), "w", encoding="utf-8") as conll_file:
            conll_file.write(f"# newdoc id = {self._id}{NEWLINE}")
            conll_file.write("# global.Entity = eid-etype-head-other")

            sent_id = 0  # manual control over index due to empty sentences
            tok_id = 0

            writer = []

            for sent in self.sentences:
                if len(" ".join(sent)) == 0:
                    tok_id += 1
                    continue
                writer.append(NEWLINE)
                writer.append(f"# sent_id = {sent_id}{NEWLINE}")
                writer.append(f"# text = {' '.join(sent)}{NEWLINE}")
                for sent_tok_id, tok in enumerate(sent):
                    misc_string = make_misc_string(
                        misc=self.misc_dict[tok_id],
                        ents=self.entity_info[tok_id]
                    )
                    conllu = make_conllu_line(sent_tok_id, tok, misc_string)
                    # conll_file.write(conllu)
                    writer.append(conllu)
                    writer.append(NEWLINE)
                    tok_id += 1
                sent_id += 1
            writer.pop()  # remove last newline
            for writable in writer:
                conll_file.write(writable)
