import re
from typing import Dict, List, Optional, Tuple

from numpy import zeros


def sent_to_UD_dist_score(narcid: Tuple[str, int], udid: str, doc2sentids: Dict[str, List[str]]) -> int:
    doc, sentord = narcid
    score = 0

    prev_udid = _get_prev_udid(doc, sentord, doc2sentids)
    if prev_udid:
        score += 100 * abs(int(udid) - int(prev_udid) - 1)
        score += 10 * (int(udid) <= int(prev_udid))

    next_udid = _get_next_udid(doc, sentord, doc2sentids)
    if next_udid:
        score += 100 * abs(int(next_udid) - int(udid) - 1)
        score += 10 * (int(udid) >= int(next_udid))

    return score


def _get_prev_udid(doc: str, sentord: int, doc2sentids: Dict[str, List[str]]) -> Optional[str]:
    offset = 1
    while sentord - offset >= 0 and doc2sentids[doc][sentord - offset] is None:
        offset += 1
    if sentord - offset >= 0:
        return doc2sentids[doc][sentord - offset]


def _get_next_udid(doc: str, sentord: int, doc2sentids: Dict[str, List[str]]) -> Optional[str]:
    offset = 1
    while sentord + offset < len(doc2sentids[doc]) and doc2sentids[doc][sentord + offset] is None:
        offset += 1
    if sentord + offset < len(doc2sentids[doc]):
        return doc2sentids[doc][sentord + offset]


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zæøåA-ZÆØÅ0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_cost_matrix(narc_ids: List[Tuple[str, int]], ud_ids: List[str], doc2sentids: Dict[str, List[str]]):
    m = zeros((len(narc_ids), len(ud_ids)))
    for i in range(len(narc_ids)):
        for j in range(len(ud_ids)):
            m[i][j] += sent_to_UD_dist_score(narc_ids[i], ud_ids[j], doc2sentids)
    return m
