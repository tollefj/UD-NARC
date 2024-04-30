import numpy as np


def stanford_data_adapter(data):
    sents = []
    for sent in data["sentences"]:
        sents.append([])
        for token in sent["tokens"]:
            sents[-1].append(token["originalText"])

    clusters = []
    if data["corefs"] is not None:
        for num, mentions in data["corefs"].items():
            clusters.append([])
            for mention in mentions:
                start = (
                    np.cumsum([0] + list(map(len, sents)))[mention["sentNum"] - 1]
                    + mention["startIndex"]
                    - 1
                )
                end = (
                    np.cumsum([0] + list(map(len, sents)))[mention["sentNum"] - 1]
                    + mention["endIndex"]
                    - 2
                )
                clusters[-1].append([start, end])

    return sum(sents, []), clusters


# tollef jørgensen, 12.05.2020
def corenlp_data_adapter(data):
    tokens = []
    for sent in data.sentence:
        # print(sent.token)
        tokens.extend([t.value for t in sent.token])

    corefs = data.corefChain
    clusters = []

    for coref in corefs:
        mentions = list(coref.mention)
        mentionclusters = []
        for m in mentions:
            start = m.beginIndex
            end = m.endIndex
            head = m.headIndex
            sentidx = m.sentenceIndex
            sent_by_idx = data.sentence[sentidx]
            offset = sent_by_idx.tokenOffsetBegin
            sent_toks = [tok.value for tok in sent_by_idx.token]
            mentionclusters.append([offset + start, offset + end - 1])
        clusters.append(mentionclusters)
    return tokens, clusters


def allen_data_adapter(data):
    return data["document"], data["clusters"]


def huggingface_data_adapter(doc):
    tokens = [token.text for token in doc]

    clusters = []
    if doc._.coref_clusters is not None:
        for cluster in doc._.coref_clusters:
            clusters.append([])
            for mention in cluster.mentions:
                clusters[-1].append([mention.start, mention.end - 1])

    return tokens, clusters
