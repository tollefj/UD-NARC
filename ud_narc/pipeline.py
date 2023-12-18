import os

from alignment import build_map, merge, combine_into_splits
from conversion import convert, Ann2Json, Json2Conll
from util import get_ud_splits
from align_norne import align_norne

if __name__ == "__main__":
    langs = ["bokmaal", "nynorsk"]

    output_path = os.path.join(os.getcwd(), "output")

    norne_path = os.path.join(os.getcwd(), "data", "norne", "ud")
    ud_path = os.path.join(os.getcwd(), "data", "UD")
    aligned_norne = os.path.join(output_path, "norne")
    if os.path.exists(aligned_norne) and len(os.listdir(aligned_norne)) == 0:
        os.rmdir(aligned_norne)
    if not os.path.exists(aligned_norne):
        align_norne(norne_path, ud_path, aligned_norne)

    NARC = os.path.join(output_path, "narc")
    VERSION = "v1.0"
    os.makedirs(NARC, exist_ok=True)

    for lang in langs:
        ANN_FOLDER = os.path.join(os.getcwd(), "data", "narc", "data", VERSION, f"annotation_{lang}")
        JSON_FOLDER = os.path.join(NARC, f"annotations_jsonlines_{lang}")
        CONLL_FOLDER = os.path.join(NARC, f"annotations_conll_{lang}")

        # Step 1: Convert NARC annotations to JSON -> CONLL
        convert(ANN_FOLDER, JSON_FOLDER, parser=Ann2Json)
        convert(JSON_FOLDER, CONLL_FOLDER, parser=Json2Conll)

        # Step 2: Build UD-NARC map
        ud_splits = get_ud_splits(ud_folder=aligned_norne, language=lang)

        UD_SPLITS_FOLDER = os.path.join(NARC, f"UD_SPLITS_{lang}")
        UD_DOC2SENT = os.path.join(NARC, f"UD_SPLITS_DOC2SENT_{lang}")
        UD_NARC = os.path.join(NARC, f"UD_NARC_MERGED_{lang}")

        build_map(ud_splits, ANN_FOLDER, UD_SPLITS_FOLDER, UD_DOC2SENT, lang)

        # Step 3: Merge UD and NARC
        merge(ud_splits, CONLL_FOLDER, UD_NARC, UD_SPLITS_FOLDER, UD_DOC2SENT)

        ALIGNED_OUTPUT = os.path.join(output_path, "aligned", f"no-narc_{lang}")
        combine_into_splits(ALIGNED_OUTPUT, UD_NARC, lang)
