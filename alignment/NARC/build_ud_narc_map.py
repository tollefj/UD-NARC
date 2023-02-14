import json
import os
from collections import defaultdict
from tqdm import tqdm
from scipy.optimize import linear_sum_assignment
import numpy as np
from util import preprocess_text


def context_fit_score(narcid, udid, doc2sentids):
    doc, sentord = narcid
    score = 0

    offset = 1
    while sentord-offset >= 0 and doc2sentids[doc][sentord-offset] is None:
        offset += 1
    if sentord-offset >= 0:
        prev_udid = doc2sentids[doc][sentord-offset]
        if prev_udid:
            score += 100*abs(int(udid) - int(prev_udid) - offset)
            score += 10*(int(udid) <= int(prev_udid))

    offset = 1
    while sentord+offset < len(doc2sentids[doc]) and doc2sentids[doc][sentord+offset] is None:
        offset += 1
    if sentord+offset < len(doc2sentids[doc]):
        next_udid = doc2sentids[doc][sentord+offset]
        if next_udid:
            score += 100*abs(int(next_udid) - int(udid) - offset)
            score += 10*(int(udid) >= int(next_udid))

    return score

def build_map(ud_splits=None,
              narc_folder="annotations_bokmaal",
              ud_split_folder="UD_SPLITS",
              doc2sent_folder="UD_SPLITS_DOC2SENT",
):
    if not ud_splits:
        raise ValueError("UD splits must be provided!")

    # STEP 1: load UD sentences
    # create a sentence-to-sentID map (sent2udsentid)
    # create a sentID-to-split map (udsentid2split)
    sentid2origsent = {}
    sent2udsentid = defaultdict(list)
    udsentid2split = {}
    for ud_split, ud_data in ud_splits.items():
        print(f"Processing {ud_split} split...")
        for sent_obj in tqdm(ud_data):
            tokens = [t["form"] for t in sent_obj]
            origsent = " ".join(tokens)
            sent = preprocess_text(origsent)
            sent_id = sent_obj.metadata['sent_id']
            sent2udsentid[sent].append(sent_id)
            udsentid2split[sent_id] = ud_split
            sentid2origsent[sent_id] = origsent

    # STEP 2: load all NARC sentences
    # create a map from sentence to positions in NARC documents (sent2doc_ord)
    # save sentences in the original order and index such lists by document IDs (doc2sents)
    sent2doc_ord = defaultdict(list)
    doc2sents = {}
    doc2orisents = {}
    narc_folder_path = os.path.join(os.getcwd(), narc_folder)
    for file in sorted(os.listdir(narc_folder_path)):
        if ".txt" not in file:
            continue
        doc_id = file.split(".")[0]
        with open(os.path.join(narc_folder_path, file), "r", encoding="utf-8") as f:
            txt = f.read()
            sents = txt.split("\n")
            nonempty_sents = [s for s in sents if len(s) > 0]
            doc_sents = []
            doc_origsents = []
            for i, s in enumerate(nonempty_sents):
                prep_s = preprocess_text(s)
                sent2doc_ord[prep_s].append((doc_id, i))
                doc_sents.append(prep_s)
                doc_origsents.append(s)
            doc2sents[doc_id] = doc_sents
            doc2orisents[doc_id] = doc_origsents

    # STEP 3: make the easy-first mapping of NARC sents positions to UD sent IDs (doc2sentids)
    # map only if there is a single UD sent ID available
    # if there is no, the whole document must be excluded
    # if there are more, let the processing for the next step
    doc2sentids = {}
    sents_multiple = set()
    for doc, sents in doc2sents.items():
        doc_sentids = []
        for i, s in enumerate(sents):
            sentids = sent2udsentid[s]
            if not sentids:
                print(f"[WARN] Document {doc} excluded as there is no parse for its {i+1}th sentence: {sents[i]}")
                break
            elif len(sentids) == 1:
                # print(f"[INFO] {doc}:{i+1} aligned to {sentids[0]}.")
                doc_sentids.append(sentids[0])
            else:
                print(f"[INFO] Multiple alignments possible for {doc}:{i+1}.")
                doc_sentids.append(None)
                sents_multiple.add(s)
        else:
            doc2sentids[doc] = doc_sentids

    # STEP 4: disambiguate NARC sents aligned to multiple UD candidates
    # each UD candidate must be used at most once, minimizing distance of its sentid from neighboring sentids
    # in the end, none of the sent lists in doc2sentids must contain a None value
    for sent in sents_multiple:
        narc_ids = sent2doc_ord[sent]
        ud_ids = sent2udsentid[sent]
        m = np.zeros((len(narc_ids), len(ud_ids)))
        for i in range(len(narc_ids)):
            for j in range(len(ud_ids)):
                m[i][j] += context_fit_score(narc_ids[i], ud_ids[j], doc2sentids)
        rows, cols = linear_sum_assignment(m)
        # print(m)
        for k in range(len(rows)):
            doc, sentord = narc_ids[rows[k]]
            sentid = ud_ids[cols[k]]
            doc2sentids[doc][sentord] = sentid
            print(f"[INFO] After disambig {doc}:{sentord+1} aligned to {sentid} with score = {m[rows[k]][cols[k]]}.")
            narc_origsent = doc2orisents[doc][sentord]
            ud_origsent = sentid2origsent[sentid]
            if narc_origsent != ud_origsent:
                print(f"[WARN] Aligned origsents are not equal")
                print(narc_origsent)
                print(ud_origsent)
    for doc, sentids in doc2sentids.items():
        for i, sentid in enumerate(sentids):
            assert sentid is not None, "[ERR] Document {doc} contains None at position {i}."

    # STEP 5: checking consistency of documents across splits
    # documents that belong to multiple splits must be deleted
    # creating a doc-to-split mapping
    doc2split = {}
    for doc, sentids in list(doc2sentids.items()):
        doc_splits = [udsentid2split[sentid] for sentid in sentids]
        uniq_splits = list(set(doc_splits))
        if len(uniq_splits) > 1:
            print(f"[WARN] Document {doc} must be removed as it belongs to multiple splits: {' '.join(uniq_splits)}")
            del doc2sentids[doc]
        else:
            doc2split[doc] = uniq_splits[0]

    # STEP 6: write the split docs to a file
    for ud_split in ud_splits:
        split_folder = os.path.join(os.getcwd(), doc2sent_folder)
        os.makedirs(split_folder, exist_ok=True)
        filename = f"{ud_split}.json"
        filepath = os.path.join(split_folder, filename)
        split_doc2sentids = {doc:sentids for doc, sentids in doc2sentids.items() if doc2split[doc] == ud_split}

        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            json.dump(split_doc2sentids, f, ensure_ascii=False, indent=4)

        # also write just the documents to a separate .txt file
        split_folder = os.path.join(os.getcwd(), ud_split_folder)
        os.makedirs(split_folder, exist_ok=True)
        filename = f"{ud_split}.txt"
        filepath = os.path.join(split_folder, filename)
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            # write all doc2sent keys with newlines between them
            f.write("\n".join(split_doc2sentids.keys()))

if __name__ == "__main__":
    from util import get_ud_splits
    #for lang in ["bokmaal"]:
    for lang in ["bokmaal", "nynorsk"]:
        ud_splits = get_ud_splits(lang)
        ANN_FOLDER = os.path.join("NARC", f"annotations_{lang}")
        build_map(
            ud_splits=ud_splits,
            narc_folder=ANN_FOLDER
        )
