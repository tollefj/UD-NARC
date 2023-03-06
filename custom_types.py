from enum import Enum


class NARCType(Enum):
    COREF = "Coref"
    BRIDGE = "Bridging"
    SPLIT = "Split_antecedent"


class ConlluType(Enum):
    ENTITY = "Entity"
    SPAN = "MentionSpan"
    COREF = "Coref"
    BRIDGE = "Bridge"
    SPLIT = "SplitAnte"


class FileTypes(Enum):
    ANN = ".ann"
    JSON = ".jsonl"
    CONLL = ".conllu"
