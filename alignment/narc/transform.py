import json
import os

from tqdm import tqdm

from ann_to_json import convert as convert_ann
from custom_types import FileTypes, NARCType
from json_to_conll import ConlluParser
from util import NEWLINE, make_conllu_line, make_misc_string


def make_jsonline(_id, sentences, tokens, markables, references, cluster_map, clustered_corefs):
    return {
        "doc_key": _id,
        "sentences": sentences,
        "tokens": tokens,
        "markables": markables,
        "references": references,
        "cluster_map": cluster_map,
        "clusters": clustered_corefs
    }

def convert_ann_to_json(source_path, output_path, verbose=0):
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"No annotation files found in path: {source_path}"
        )
    if not os.path.exists(output_path):
        print("Creating folder for parsed files...")
        os.mkdir(output_path)
        
    parsed_data = []
    for file in tqdm(sorted(os.listdir(source_path))):
        # just use the .ann files and fetch the text
        # during the parsing phase (by id ref)
        if ".txt" in file:
            continue
        file_path = os.path.join(source_path, file)

        if verbose > 0:
            print("Loading ", file_path)

        doc_key = file.split(".")[0]
        parsed_data.append(make_jsonline(doc_key, *convert_ann(from_file=file_path)))

    for jsonline in parsed_data:
        jsonline_path = os.path.join(output_path, jsonline["doc_key"] + FileTypes.JSON.value)
        with open(jsonline_path, "w", encoding="utf-8", newline="\n") as jsonline_file:
            json.dump(jsonline, jsonline_file, ensure_ascii=False)



# pass the invalid ents to the conll parser
# these are mapped to the invalid entities in the UD-NARC merge
invalid_entities = set()
with open("invalid_entities.txt", "r", encoding="utf-8") as f:
    for line in f:
        if "#" not in line:
            invalid_entities.add(line.strip())

def convert_json_to_conll(source_path, output_path, verbose=0):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"No annotation files found in folder: {source_path}")
    os.makedirs(output_path, exist_ok=True)
    jsonlines = [f for f in sorted(os.listdir(source_path)) if FileTypes.JSON.value in f]
    for jsonline in tqdm(jsonlines):
        jsonline_path = os.path.join(source_path, jsonline)
        with open(jsonline_path, "r", encoding="utf-8") as jsonline_file:
            data = json.load(jsonline_file)
            parser = ConlluParser(data, invalid_ents=invalid_entities)
            parser.parse([NARCType.BRIDGE, NARCType.SPLIT])

            filename = jsonline.replace(FileTypes.JSON.value, FileTypes.CONLL.value)
            with open(os.path.join(output_path, filename), "w", encoding="utf-8", newline="\n") as conll_file:
                conll_file.write(f"# filename = {data['doc_key']}{NEWLINE}")
                conll_file.write("# global.Entity = eid-etype-head-other")

                sent_id = 0  # manual control over index due to empty sentences
                tok_id = 0
                
                for sent in data["sentences"]:
                    if len(" ".join(sent)) == 0:
                        tok_id += 1
                        continue
                    conll_file.write(NEWLINE)
                    conll_file.write(f"# sent_id = {sent_id}{NEWLINE}")
                    conll_file.write(f"# text = {' '.join(sent)}{NEWLINE}")
                    for sent_tok_id, tok in enumerate(sent):
                        misc_string = make_misc_string(parser, tok_id)
                        conllu = make_conllu_line(sent_tok_id, tok, misc_string)
                        conll_file.write(conllu)
                        tok_id += 1
                    sent_id += 1


if __name__ == "__main__":
    ANN_FOLDER = "annotations"
    JSON_FOLDER = "annotations_jsonlines"
    CONLL_FOLDER = "annotations_conll"

    convert_ann_to_json(ANN_FOLDER, JSON_FOLDER)
    convert_json_to_conll(JSON_FOLDER, CONLL_FOLDER)

