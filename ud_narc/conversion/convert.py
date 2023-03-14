import os

from conversion.generic_parser import GenericParser
from tqdm import tqdm


def convert(source_path: str, output_path: str, parser: GenericParser):
    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"No annotation files found in path: {source_path}"
        )
    if not os.path.exists(output_path):
        print(f"Creating folder for parsed files: {output_path}")
        os.mkdir(output_path)

    print(f"Converting {source_path} to {output_path}")

    files = [f for f in sorted(os.listdir(
        source_path)) if f.endswith(parser.FROM_FILE)]

    for _file in tqdm(files):
        file_path = os.path.join(source_path, _file)
        _parser = parser(file_path)
        _parser.parse()

        converted = _file.replace(parser.FROM_FILE, parser.TO_FILE)
        out_file = os.path.join(output_path, converted)
        _parser.write(out_file)
