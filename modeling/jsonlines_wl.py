import os, random
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
