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
from util import preprocess_text
from conllu import parse
from tqdm import tqdm

def load_split_docs(split_folder):
    doc2split = {}
    for file in sorted(os.listdir(split_folder)):
        if ".txt" not in file:
            continue
        split_name = file.split(".")[0]
        with open(os.path.join(split_folder, file), "r", encoding="utf-8") as f:
            for doc in f:
                doc2split[doc.rstrip()] = split_name
    return doc2split

def load_split2doc2sentids(doc2sentids_folder):
    split2doc2sentids = {}
    for file in tqdm(sorted(os.listdir(doc2sentids_folder))):
        if ".json" not in file:
            continue
        split_name = file.split(".")[0]
        with open(os.path.join(doc2sentids_folder, file), "r", encoding="utf-8") as jsonfile:
            split2doc2sentids[split_name] = json.load(jsonfile)
    return split2doc2sentids

def load_narc_connlu(narc_conll, built_docs):
    doc2conllu = {}
    for file in tqdm(sorted(os.listdir(narc_conll))):
        if not file.endswith(".conllu"):
            continue
        doc_id = file.split(".")[0]
        if doc_id not in built_docs:
            continue
        data = parse(open(os.path.join(narc_conll, file), "r", encoding="utf-8", newline="\n").read())
        doc2conllu[doc_id] = data
    return doc2conllu

# align preprocessed NARC tokens to UD tokens
# the concatenated tokens are guaranteed to agree
def align_tokens(narc_tokens, ud_tokens):
    align = [None] * len(narc_tokens)
    i = 0
    j = 0
    while i < len(narc_tokens) and j < len(ud_tokens):
        if narc_tokens[i] == ud_tokens[j]:
            align[i] = j
            i += 1
            j += 1
        elif ud_tokens[j] == "":
            j += 1
        elif narc_tokens[i] == "":
            align[i] = j-1
            i += 1
        elif narc_tokens[i].startswith(ud_tokens[j]):
            narc_tokens[i] = preprocess_text(narc_tokens[i][len(ud_tokens[j]):])
            j += 1
        else:
            raise NotImplementedError(f"This option in token aligning is not implemented: {narc_tokens}, {ud_tokens}")
    while i < len(narc_tokens):
        align[i] = j-1
        i += 1
    return align

def merge_conllus(narc_conllu, ud_conllu):
    # align non-punctuation first
    ud_preproc_forms = [preprocess_text(t["form"]) for t in ud_conllu]
    narc_preproc_forms = [preprocess_text(t["form"]) for t in narc_conllu]
    align = align_tokens(narc_preproc_forms, ud_preproc_forms)
    assert all(a is not None for a in align)
    # merge misc fields
    narc_miscs = [t["misc"] or {} for t in narc_conllu]
    for i, narc_misc in enumerate(narc_miscs):
        ud_t = ud_conllu[align[i]]
        ud_misc = ud_t["misc"] or {}
        ud_t["misc"] = {**ud_misc, **narc_misc}
    # if the last token is a punctuation mark, we want to remove the "SpaceAfter=No" annotation
    if ud_conllu[-1]["form"] in [".", "...", ":", ";", "?", "!"]:
        ud_conllu[-1]["misc"] = {k: v for k, v in ud_conllu[-1]["misc"].items() if k != "SpaceAfter"}
    return ud_conllu

def merge(
    ud_splits=None,
    narc_conll="annotations_conll",
    merged_narc_ud="UD_NARC_MERGED",
    ud_split_folder="UD_SPLITS",
    doc2sent_folder="UD_SPLITS_DOC2SENT",
):

    if not ud_splits:
        raise ValueError("UD splits must be provided!")

    doc2split = load_split_docs(ud_split_folder)
    split2doc2sentids = load_split2doc2sentids(doc2sent_folder)
    doc2conllu = load_narc_connlu(narc_conll, doc2split.keys())

    os.makedirs(merged_narc_ud, exist_ok=True)

    for split, doc2sentids in split2doc2sentids.items():
        print(f"============ Merging {split} ==============")

        sentid2ud = {s.metadata['sent_id']:s for s in ud_splits[split]}

        save_folder = os.path.join(merged_narc_ud, split)
        os.makedirs(save_folder, exist_ok=True)

        for doc, sentids in doc2sentids.items():
            print(f"[INFO] Processing document {doc}")

            conll_str = f"# newdoc id = {doc}\n"
            conll_str += "# global.Entity = eid-etype-head-other\n"

            narc_conllus = doc2conllu[doc]
            assert len(narc_conllus) == len(sentids)
            for i, (sentid, narc_conllu) in enumerate(zip(sentids, narc_conllus)):
                ud_conllu = sentid2ud[sentid]
                merged_conllu = merge_conllus(narc_conllu, ud_conllu)
                conll_str += ud_conllu.serialize()

            with open(os.path.join(save_folder, f"{doc}.conllu"), "w", encoding="utf-8", newline="\n") as parsed_file:
                parsed_file.write(conll_str)

if __name__ == "__main__":
    from util import get_ud_splits
    #for lang in ["bokmaal"]:
    for lang in ["bokmaal", "nynorsk"]:
        ud_splits = get_ud_splits(lang)
        CONLL_FOLDER = os.path.join("NARC", f"annotations_conll_{lang}")
        UD_SPLITS_FOLDER = os.path.join("NARC", f"UD_SPLITS_{lang}")
        UD_DOC2SENT = os.path.join("NARC", f"UD_SPLITS_DOC2SENT_{lang}")
        UD_NARC = os.path.join("NARC", f"UD_NARC_MERGED_{lang}")
        print(f"============ Merging {lang} ==============")
        merge(
            ud_splits=ud_splits,
            narc_conll=CONLL_FOLDER,
            merged_narc_ud=UD_NARC,
            ud_split_folder=UD_SPLITS_FOLDER,
            doc2sent_folder=UD_DOC2SENT,
        )
