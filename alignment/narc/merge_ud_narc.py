# %%
"""
We now already have the splits needed to merge everything.

We have a document_id -> sentence_id mapping
+
split [train/dev/test] -> document_ids mapping
"""
import json
import os
from collections import defaultdict

from conllu import parse
from tqdm import tqdm


def merge(
    ud_splits=None,
    narc_conll="annotations_conll",
    merged_narc_ud="UD_NARC_MERGED",
    ud_split_folder="UD_SPLITS",
    doc2sent_folder="UD_SPLITS_DOC2SENT",
):

    if not ud_splits:
        raise ValueError("UD splits must be provided!")

    split_documents = {}

    for file in sorted(os.listdir(ud_split_folder)):
        if ".txt" not in file:
            continue
        split_name = file.split(".")[0]
        with open(os.path.join(ud_split_folder, file), "r", encoding="utf-8") as f:
            split_documents[split_name] = set(f.read().splitlines())

    doc_to_split = {}
    for split, documents in split_documents.items():
        for doc in documents:
            doc_to_split[doc] = split

    doc2sent = {}

    for file in tqdm(sorted(os.listdir(doc2sent_folder))):
        if ".json" not in file:
            continue
        split_name = file.split(".")[0]
        with open(os.path.join(doc2sent_folder, file), "r", encoding="utf-8") as jsonfile:
            doc2sent[split_name] = json.load(jsonfile)


    sent2doc = {}
    for split, docs in doc2sent.items():
        for doc, sents in docs.items():
            for sent in sents:
                sent2doc[sent] = doc

    def get_ud_data_by_sent_id(ud_split, sent_id):
        data = ud_splits[ud_split]
        for sent in data:
            if sent.metadata['sent_id'] == sent_id:
                return sent


    os.makedirs(merged_narc_ud, exist_ok=True)


    added_splits = defaultdict(list)

    for file in tqdm(sorted(os.listdir(narc_conll))):
        if not file.endswith(".conllu"):
            continue

        doc_id = file.split(".")[0]
        data = parse(open(os.path.join(narc_conll, file), "r", encoding="utf-8", newline="\n").read())

        if doc_id not in doc_to_split:
            added_splits["missing"].append(doc_id)
            continue

        UD_doc_split = doc_to_split[doc_id]
        added_splits[UD_doc_split].append(doc_id)

        sent_ids = doc2sent[UD_doc_split][doc_id]
        UD_sents = [get_ud_data_by_sent_id(UD_doc_split, sent_id) for sent_id in sent_ids]

        conll_str = f"# newdoc id = {doc_id}\n"
        conll_str += "# global.Entity = eid-etype-head-other\n"

        valid_doc = False
        seen_sentences = set()

        for ud_sent in UD_sents:
            ud_tokens = [t["form"] for t in ud_sent]
            for i, narc_sent in enumerate(data):
                if i in seen_sentences:
                    continue
                sent_tokens = [t["form"] for t in narc_sent]
                if sent_tokens[-1] == "|":
                    sent_tokens = sent_tokens[:-1]
                    narc_sent = narc_sent[:-1]

                if sent_tokens == ud_tokens:
                    seen_sentences.add(i)

                    narc_misc = [t["misc"] or {} for t in narc_sent]
                    for i, t in enumerate(ud_sent):
                        this_misc = t["misc"] or {}
                        t["misc"] = {**this_misc, **narc_misc[i]}

                    # if the last token is a punctuation mark, we want to remove the "SpaceAfter=No" annotation
                    if ud_sent[-1]["form"] in [".", "...", ":", ";", "?", "!"]:
                        ud_sent[-1]["misc"] = {k: v for k, v in ud_sent[-1]["misc"].items() if k != "SpaceAfter"}
                    conll_str += ud_sent.serialize()
                    valid_doc = True

                    break

        if not valid_doc:
            added_splits["missing"].append(doc_id)
            continue
        # save to a train/dev/test folder within the merged_narc_ud
        save_folder = os.path.join(merged_narc_ud, UD_doc_split)
        os.makedirs(save_folder, exist_ok=True)

        with open(os.path.join(save_folder, file), "w", encoding="utf-8", newline="\n") as parsed_file:
            parsed_file.write(conll_str)

    for split, docs in added_splits.items():
        print(f"{split}: {len(docs)} docs")
