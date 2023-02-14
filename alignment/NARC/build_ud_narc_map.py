import json
import os
import re
from collections import defaultdict
from tqdm import tqdm


# %%
def preprocess_sent(sent):
    sent = sent.lower()
    sent = re.sub(r"[^a-zæøåA-ZÆØÅ0-9\s]", " ", sent)
    sent = re.sub(r"\s+", " ", sent)
    return sent.strip()

def build_map(ud_splits=None,
              brat_folder="annotations_bokmaal",
              ud_split_folder="UD_SPLITS",
              doc2sent_folder="UD_SPLITS_DOC2SENT",
):
    if not ud_splits:
        raise ValueError("UD splits must be provided!")

    brat_annotations = os.path.join(os.getcwd(), brat_folder)
    brat_sents = {}
    for file in sorted(os.listdir(brat_annotations)):
        if ".txt" not in file:
            continue
        doc_id = file.split(".")[0]
        with open(os.path.join(brat_annotations, file), "r", encoding="utf-8") as f:
            txt = f.read()
            sents = txt.split("\n")
            brat_sents[doc_id] = [preprocess_sent(s) for s in sents if len(s) > 0]

    for ud_split, ud_data in ud_splits.items():
        print(f"Processing {ud_split} split...")
        sen2doc = defaultdict(set)
        # STEP 1: match all tokens from the UD corpus to the NARC corpus
        for sent in tqdm(ud_data):
            tokens = [t["form"] for t in sent]
            detokenized = " ".join(tokens)
            sent_id = sent.metadata['sent_id']
            parsed = preprocess_sent(detokenized)

            for doc_id, sents in brat_sents.items():
                if parsed in sents:
                    sen2doc[sent_id].add(doc_id)
            
        # STEP 2: remove invalid matches
        sen2doc = {k: list(v) for k, v in sen2doc.items()}
        for i, (sent_id, doc_ids) in enumerate(sen2doc.items()):
            if len(doc_ids) > 1:
                sen2doc[sent_id] = "MULTIPLE"
            else:  # select the first document
                sen2doc[sent_id] = doc_ids[0]
            
        # STEP 3: fix the MULTIPLE matches by looking at a sliding window
        for i, (sent_id, doc_id) in enumerate(sen2doc.items()):
            if doc_id == "MULTIPLE":
                if i > 0 and i < len(sen2doc) - 1:
                    prev_id = sen2doc[list(sen2doc.keys())[i-1]]
                    next_id = sen2doc[list(sen2doc.keys())[i+1]]
                    if prev_id == next_id:
                        sen2doc[sent_id] = prev_id
            
        # STEP 4: reverse the ordering to doc -> sents
        doc2sent = defaultdict(list)
        for sent_id, doc_id in sen2doc.items():
            doc2sent[doc_id].append(sent_id)

        # STEP 5: apply filtering to remove MULTIPLE items
        doc2sent = {k: v for k, v in doc2sent.items() if k != "MULTIPLE"}
        # sort it
        doc2sent = {k: sorted(v) for k, v in doc2sent.items()}

        # STEP 6: filter invalid sentences with too large gaps (e.g. matches other places)
        # for each document in doc2sent, consider the sentences...
        # e.g. id 014652, then followed by 014842, 014844, 014845, ...
        # we want to find somewhat sequential matches, i.e. max 1 missing sentence between each item
        # for each value, if the gap to the next is larger than 3, then ignore it
        def check_gap(sent1, sent2):
            return (int(sent2) - int(sent1)) <= 3

        for doc, sents in doc2sent.items():
            valid_sents = []
            prev = sents[0]
            for sent in sents[1:]:
                if check_gap(prev, sent):
                    valid_sents.append(prev)
                prev = sent
            # last gap:
            if check_gap(prev, sents[-1]):
                valid_sents.append(prev)
            doc2sent[doc] = valid_sents


        # STEP 7: write the split docs to a file
        split_folder = os.path.join(os.getcwd(), doc2sent_folder)
        os.makedirs(split_folder, exist_ok=True)
        filename = f"{ud_split}.json"
        filepath = os.path.join(split_folder, filename)
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc2sent, f, ensure_ascii=False, indent=4)

        # also write just the documents to a separate .txt file
        split_folder = os.path.join(os.getcwd(), ud_split_folder)
        os.makedirs(split_folder, exist_ok=True)
        filename = f"{ud_split}.txt"
        filepath = os.path.join(split_folder, filename)
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            # write all doc2sent keys with newlines between them
            f.write("\n".join(doc2sent.keys()))

if __name__ == "__main__":
    build_map()