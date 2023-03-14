import json
import os
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

from conllu.models import SentenceList
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm

from alignment.utils_merge import build_cost_matrix, preprocess_text


def build_map(ud_splits: Optional[Dict[str, SentenceList]] = None,
              narc_folder: str = "annotations_bokmaal",
              ud_split_folder: str = "UD_SPLITS",
              doc2sent_folder: str = "UD_SPLITS_DOC2SENT",
              lang: str = "bokmaal",  # used to store language-specific files
              ):
    if not ud_splits:
        raise ValueError("UD splits must be provided!")
    print(f"Building mapping between NARC and UD...")

    # STEP 1: load UD sentences
    # create a sentence-to-sentID map (sent2udsentid)
    # create a sentID-to-split map (udsentid2split)
    sentid2origsent: Dict[str, str] = {}
    sent2udsentid: DefaultDict[str, List[str]] = defaultdict(list)
    udsentid2split: Dict[str, str] = {}
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
    sent2doc_ord: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    doc2sents: Dict[str, List[str]] = {}
    doc2orisents: Dict[str, List[str]] = {}
    narc_folder_path = os.path.join(os.getcwd(), narc_folder)
    for file in sorted(os.listdir(narc_folder_path)):
        if ".txt" not in file:
            continue
        doc_id = file.split(".")[0]
        with open(os.path.join(narc_folder_path, file), "r", encoding="utf-8") as f:
            txt = f.read()
            sents = txt.split("\n")
            nonempty_sents = [s for s in sents if len(s) > 0]
            doc_sents: List[str] = []
            doc_origsents: List[str] = []
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
    doc2sentids: Dict[str, List[int]] = {}
    sents_multiple: Set[str] = set()

    excluded_docs_with_no_sent = []
    multiple_doc_candidates = []

    for doc, sents in doc2sents.items():
        doc_sentids: List[str] = []
        for i, s in enumerate(sents):
            sentids = sent2udsentid[s]
            if not sentids:
                print(
                    f"[WARN] Document {doc} excluded as there is no parse for its {i+1}th sentence: {sents[i]}")
                excluded_docs_with_no_sent.append((doc, i+1, sents[i]))
                break
            elif len(sentids) == 1:
                # print(f"[INFO] {doc}:{i+1} aligned to {sentids[0]}.")
                doc_sentids.append(sentids[0])
            else:
                print(f"[INFO] Multiple alignments possible for {doc}:{i+1}.")
                doc_sentids.append(None)
                sents_multiple.add(s)
                multiple_doc_candidates.append((doc, i+1, s))
        else:
            doc2sentids[doc] = doc_sentids

    with open(f"output/ERROR_NO_SENT_MATCH_{lang}.txt", "w", encoding="utf-8") as f:
        f.writelines("\n".join(
            [f"{doc},{sentord},{sent}" for doc, sentord, sent in excluded_docs_with_no_sent]))
    with open(f"output/ERROR_MULTIPLE_SENT_MATCH_{lang}.txt", "w", encoding="utf-8") as f:
        f.writelines("\n".join(
            [f"{doc},{sentord},{sent}" for doc, sentord, sent in multiple_doc_candidates]))

    # STEP 4: disambiguate NARC sents aligned to multiple UD candidates
    # each UD candidate must be used at most once, minimizing distance of its sentid from neighboring sentids
    # in the end, none of the sent lists in doc2sentids must contain a None value
    non_equal_sents = []

    for sent in sents_multiple:
        narc_ids = sent2doc_ord[sent]
        ud_ids = sent2udsentid[sent]
        m = build_cost_matrix(narc_ids, ud_ids, doc2sentids)
        rows, cols = linear_sum_assignment(m)
        # print(m)
        for k in range(len(rows)):
            doc, sentord = narc_ids[rows[k]]
            sentid = ud_ids[cols[k]]
            doc2sentids[doc][sentord] = sentid
            print(
                f"[INFO] After disambig {doc}:{sentord+1} aligned to {sentid} with score = {m[rows[k]][cols[k]]}.")
            narc_origsent = doc2orisents[doc][sentord]
            ud_origsent = sentid2origsent[sentid]
            if narc_origsent != ud_origsent:
                print(f"[WARN] Aligned origsents are not equal")
                print("[INFO] NARC original:", narc_origsent)
                print("[INFO] UD   original:", ud_origsent)
                non_equal_sents.append(
                    (doc, sentord, sentid, narc_origsent, ud_origsent))
    for doc, sentids in doc2sentids.items():
        for i, sentid in enumerate(sentids):
            assert sentid is not None, "[ERR] Document {doc} contains None at position {i}."

    with open(f"output/ERROR_NON_EQUAL_SENTS_{lang}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join([f"{doc},{sentord},{sentid},{narc_origsent},{ud_origsent}" for doc,
                sentord, sentid, narc_origsent, ud_origsent in non_equal_sents]))

    # STEP 5: checking consistency of documents across splits
    # documents that belong to multiple splits must be deleted
    # creating a doc-to-split mapping
    belongs_to_multiple_splits = []

    doc2split: Dict[str, str] = {}
    for doc, sentids in list(doc2sentids.items()):
        doc_splits = [udsentid2split[sentid] for sentid in sentids]
        uniq_splits = list(set(doc_splits))
        if len(uniq_splits) > 1:
            print(
                f"[WARN] Document {doc} must be removed as it belongs to multiple splits: {' '.join(uniq_splits)}")
            # mapping between sentence and its split
            sentence_to_split = {
                sent: udsentid2split[sentid] for sent, sentid in zip(doc2sents[doc], sentids)}
            belongs_to_multiple_splits.append(
                (doc, uniq_splits, sentence_to_split))
            del doc2sentids[doc]
        else:
            doc2split[doc] = uniq_splits[0]

    with open(f"output/ERROR_MULTIPLE_UD_SPLIT_{lang}.txt", "w", encoding="utf-8", newline="\n") as f:
        f.writelines("\n".join(f"{doc},{uniq_splits},{splitsents}" for doc,
                     uniq_splits, splitsents in belongs_to_multiple_splits))

    # STEP 6: write the split docs to a file
    for ud_split in ud_splits:
        split_folder = os.path.join(os.getcwd(), doc2sent_folder)
        os.makedirs(split_folder, exist_ok=True)
        filename = f"{ud_split}.json"
        filepath = os.path.join(split_folder, filename)
        split_doc2sentids = {doc: sentids for doc, sentids in doc2sentids.items(
        ) if doc2split[doc] == ud_split}

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
