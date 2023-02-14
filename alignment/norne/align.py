# %%
from conllu import parse, TokenList
import os

# %%
def get_conll_files(path):
    files = []
    for file in os.listdir(path):
        if file.endswith(".conllu"):
            files.append(os.path.join(path, file))
    return files

def get_paths(path):
    files = get_conll_files(path)
    return {
        "train": [f for f in files if "train" in f][0],
        "test": [f for f in files if "test" in f][0],
        "dev": [f for f in files if "dev" in f][0]
    }

# %%
for lang in ["bokmaal", "nynorsk"]:
    norne_id = "nob" if lang == "bokmaal" else "nno"
    NORNE = get_paths(f"../../norne/ud/{norne_id}")
    UD = get_paths(f"../../UD_Norwegian-{lang.capitalize()}")
    
    for split in ["train", "test", "dev"]:
        norne_path = NORNE[split]
        ud_path = UD[split]
        print(split)
        print(norne_path, ud_path)
        with open(ud_path, "r", encoding="utf-8") as ud_f, open(norne_path, "r", encoding="utf-8") as entity_f:
            ud_data = parse(ud_f.read())
            entity_data = parse(entity_f.read())

        out = f"../../data/ud_norne_{lang}_{split}.conllu"

        def merge_sentences(ud, entity):
            ud_toks = [t for t in ud]
            entity_toks = [t for t in entity]
            for j in range(len(ud_toks)):
                ud_misc = ud_toks[j]["misc"] or {}
                entity_misc = entity_toks[j]["misc"] or {}
                # filter to only include the "name" key of the NorNE data
                entity_misc = {k: v for k, v in entity_misc.items() if k == "name"}

                ud_misc.update(entity_misc)
                ud_toks[j]["misc"] = ud_misc

            return TokenList(ud_toks)


        aligned_data = []  # to be written to file

        # some sentences are split across two sentences in the NorNE data
        # keep track of this index
        entity_extra_idx_iterator = 0
        for i in range(len(ud_data)):
            ud_sent = ud_data[i]
            entity_sent = entity_data[i + entity_extra_idx_iterator]
            
            valid_idx = i + entity_extra_idx_iterator + 1 < len(entity_data)
            if valid_idx:
                entity_sent_nxt = entity_data[i + entity_extra_idx_iterator + 1]
                next_entity_text = entity_sent_nxt.metadata["text"]

            meta = ud_sent.metadata  # we will modify the entire object, so save it
            ud_text = ud_sent.metadata["text"]
            entity_text = entity_sent.metadata["text"]

            if ud_text == entity_text:
                aligned = merge_sentences(ud_sent, entity_sent)
                ud_data[i] = aligned
            elif ud_text == entity_text + next_entity_text and valid_idx:
                # try to match the UD sent with the next NorNE sent
                # such that UD1 = NorNE1 + NorNE2
                entity_tokens = [t for t in entity_sent]
                entity_tokens_nxt = [t for t in entity_sent_nxt]
                merged = TokenList(entity_tokens + entity_tokens_nxt)
                aligned = merge_sentences(ud_sent, merged)
                ud_data[i] = aligned
                entity_extra_idx_iterator += 1
            elif ud_text == entity_text[1:]:
                # we may get:
                # En kampanje for "etnisk renskning" starter med at én nabo vender seg mot en annen.
                # "En kampanje for "etnisk renskning" starter med at én nabo vender seg mot en annen.
                # that is, the norne sentence has an unnecessary token at the beginning. Ignore it!
                entity_tokens = [t for t in entity_sent]
                merged = TokenList(entity_tokens[1:])
                aligned = merge_sentences(ud_sent, merged)
                ud_data[i] = aligned
            else:
                print(f"Mismatched sentences on line {ud_sent.metadata['sent_id']}")
                print(ud_sent.metadata["text"])
                print(entity_sent.metadata["text"])
                print("_"*40)
            
            ud_data[i].metadata = meta
            aligned_data.append(ud_data[i])

        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for sent in aligned_data:
                f.write(sent.serialize())

# %%
