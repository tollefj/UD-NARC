# %%
import spacy
import os
from shutil import copyfile

from ncc_to_heads import get_heads
# %%
import json, jsonlines

# Convert the data into the jsonlines format used in wl-coref
def jsonlines_wl(nlp, source_folder, dest_folder, name_core="narc" ):
    source_filenames = [f for f in os.listdir(source_folder) if ".jsonl" in f]
    wl_formatted = []
    for idx, f_name in enumerate(source_filenames):
        with open (os.path.join(source_folder, f_name), encoding="utf8") as rf:
            # assert len(rf.readlines()) == 1
            # print(f_name)
            doc = json.loads(rf.readline().strip())
        wl_data = {
            "document_id": "nw"+doc["doc_key"], 
            "cased_words" : [t for s in doc["sentences"] for t in s],
            "sent_id" : [i for i, s in enumerate(doc["sentences"] )for t in s], 
            "part_id" : idx,
            "speaker": ["blank" for s in doc["sentences"] for t in s],
            "head": [None for s in doc["sentences"] for t in s],
            # Change this to real head when possible
            "clusters": []
        }
        docs = nlp.pipe([" ".join(wl_data["cased_words"])])
        heads = [token.head.i for token in next(iter(docs))]
        # Spacy gives heads its own index as head. wl-coref wants Null
        heads = [None if n == b else b for n, b in enumerate(heads) ]
        wl_data["head"] = heads
        
        for cluster in doc["clusters"]: # Add 1 to end word-index
            wl_data["clusters"].append( [[s,e+1] for s,e in cluster] ) # wl-coref creates range() with start and end
        wl_formatted.append(wl_data)

        # These should now be similar to the output of convert_to_jsonlines.py in wl-coref
        with jsonlines.open(os.path.join(dest_folder,f'{name_core}_all.jsonl'), 'w') as wf:
            wf.write_all(wl_formatted)
    print(f"Saved {len(wl_formatted)} documents into {dest_folder} ")


# %%

# bokmaal jsonline data:
parent = os.path.join(os.getcwd(), os.pardir)
narc = os.path.join(parent, "output", "narc")
narc_bm = os.path.join(narc, "annotations_jsonlines_bokmaal")
narc_nn = os.path.join(narc, "annotations_jsonlines_nynorsk")

narc_output = os.path.join(os.getcwd(), "data", "narc_jsonl")
os.makedirs(narc_output, exist_ok=True)

# copy if the dir is empty:
if len(os.listdir(narc_output)) == 0:
    for file in os.listdir(narc_bm):
        copyfile(os.path.join(narc_bm, file), os.path.join(narc_output, file))
    for file in os.listdir(narc_nn):
        copyfile(os.path.join(narc_nn, file), os.path.join(narc_output, file))

# %%
narc_wordlevel = os.path.join(os.getcwd(), "data", "narc_wordlevel")
os.makedirs(narc_wordlevel, exist_ok=True)

# %%

nlp = spacy.load("nb_core_news_sm")
# %%
NAME_CORE = "narc"  # First part of wl-formatted filenames
if len(os.listdir(narc_wordlevel)) == 0:
    print(f"Parsing jsonlines for word-level coreference...")
    jsonlines_wl(nlp, narc_output, narc_wordlevel, name_core=NAME_CORE)

# %%
print(f"Splitting data...")
# we have the files containing which documents belong to which split:
# e.g. output/narc/UD_SPLITS_bokmaal/train.txt
doc_to_split = {}
for lang in ["bokmaal", "nynorsk"]:
    splits_dir = os.path.join(parent, "output", "narc", f"UD_SPLITS_{lang}")
    for split in ["train", "dev", "test"]:
        with open(os.path.join(splits_dir, f"{split}.txt"), "r") as f:
            for line in f:
                doc_to_split[line.strip()] = split

# %%

for k, v in doc_to_split.items():
    print(k, v)
    break

# %%
# move jsonlines to the correct split dir:
import jsonlines

# source file:
JSONLINES_WL = os.path.join(narc_wordlevel, "narc_all.jsonl")
jsonl = jsonlines.open(JSONLINES_WL)
not_found = []
for obj in jsonl:
    doc_id = obj["document_id"][2:]
    if doc_id not in doc_to_split:
        print(doc_id, "not found... :(( consider this as a training sample")
        split = "train"
    else:
        split = doc_to_split[doc_id]
    dest_file = os.path.join(narc_wordlevel, f"{NAME_CORE}_{split}.jsonl")

    with jsonlines.open(dest_file, "a") as writer:
        writer.write(obj)
# %%
print("Getting heads for word-level coreference...")
get_heads(os.path.join(narc_wordlevel, "narc_all"), NAME_CORE)
