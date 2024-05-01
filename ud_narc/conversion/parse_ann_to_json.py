import json
import os
from typing import Dict, List, Set

from conversion.generic_parser import GenericParser
from conversion.utils_ann import (
    extract_token_mapping,
    get_invalid_mention_links,
    get_reference_content,
    get_references,
    markable_char_to_word,
)
from custom_types import FileTypes

invalid_mention_links = get_invalid_mention_links()


class Ann2Json(GenericParser):
    FROM_FILE = FileTypes.ANN.value
    TO_FILE = FileTypes.JSON.value

    def __init__(self, in_file):
        self.data: List[str] = None
        self.text: str = None
        self.load(in_file)

        self._id = os.path.basename(in_file).split(self.FROM_FILE)[0]
        # replace any weird chars in the id, this could be helpful for visulization later, and to clean up entity names.
        # replace_map = {
        #     "~": "_",
        #     " ": "_",
        #     "-": "_",
        # }
        # for k, v in replace_map.items():
        #     self._id = self._id.replace(k, v)

        self.invalid: Set[str] = invalid_mention_links[self._id]
        self.json: Dict[str, str] = None

    def load(self, in_file):
        with open(in_file, "r", encoding="utf-8") as f:
            self.data = f.readlines()
        # txt:
        txt_path = in_file.split(self.FROM_FILE)[0] + ".txt"
        with open(txt_path, "r", encoding="utf-8") as f:
            self.text = "".join(f.readlines())

    def parse(self):
        markables, references = get_references(self.data, self.invalid)

        cluster_map, clustered_corefs = get_reference_content(markables, references)

        sorted_clusters = []
        for cluster in clustered_corefs:
            sorted_cluster = []
            for span in cluster:
                sorted_cluster.append(tuple(sorted(span)))
            sorted_cluster.sort(key=lambda x: x[0])
            sorted_clusters.append(sorted_cluster)

        clustered_corefs = sorted_clusters

        sents, tokens, char_to_word_map = extract_token_mapping(self.text)
        markable_by_word = markable_char_to_word(markables, char_to_word_map)

        self.json = {
            "doc_key": self._id,
            "sentences": sents,
            "tokens": tokens,
            "markables": markable_by_word,
            "references": references,
            "cluster_map": cluster_map,
            "clusters": clustered_corefs,
        }

    def write(self, out_file: str):
        with open(out_file, "w", encoding="utf-8", newline="\n") as json_file:
            json.dump(self.json, json_file, ensure_ascii=False)
