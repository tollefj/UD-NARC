import os

from ann_to_json import Ann2Json
from json_to_conll import Json2Conll
from tqdm import tqdm


def convert(source_path, output_path, parser, verbose=0):
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"No annotation files found in path: {source_path}"
        )
    if not os.path.exists(output_path):
        print(f"Creating folder for parsed files: {output_path}")
        os.mkdir(output_path)

    files = [f for f in sorted(os.listdir(
        source_path)) if f.endswith(parser.FROM_FILE)]

    for _file in tqdm(files):
        if verbose > 0:
            print(f"Loading {_file}...")
        file_path = os.path.join(source_path, _file)
        _parser = parser(file_path)
        _parser.parse()

        converted = _file.replace(parser.FROM_FILE, parser.TO_FILE)
        out_file = os.path.join(output_path, converted)
        _parser.write(out_file)

def convert_ann_to_json(source_path, output_path, verbose=0):
    convert(source_path, output_path, Ann2Json, verbose)


def convert_json_to_conll(source_path, output_path, verbose=0):
    convert(source_path, output_path, Json2Conll, verbose)


if __name__ == "__main__":
    ANN_FOLDER = "annotations"
    JSON_FOLDER = "annotations_jsonlines"
    CONLL_FOLDER = "annotations_conll"

    convert_ann_to_json(ANN_FOLDER, JSON_FOLDER)
    convert_json_to_conll(JSON_FOLDER, CONLL_FOLDER)
