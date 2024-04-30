import os

from align_norne import align_norne
from alignment import build_map, combine_into_splits, merge
from conversion import Ann2Json, Json2Conll, convert
from util import get_ud_splits

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
        ANN_FOLDER = os.path.join(
            os.getcwd(), "data", "narc", "data", VERSION, f"annotation_{lang}"
        )
        JSON_FOLDER = os.path.join(NARC, f"annotations_jsonlines_{lang}")
        CONLL_FOLDER = os.path.join(NARC, f"annotations_conll_{lang}")

        # Step 1: Convert annotations to JSON -> CONLL, if needed
        convert(ANN_FOLDER, JSON_FOLDER, parser=Ann2Json)
        convert(JSON_FOLDER, CONLL_FOLDER, parser=Json2Conll)

        # Step 2: Build map
        ud_splits = get_ud_splits(ud_folder=aligned_norne, language=lang)

        UD_SPLITS_FOLDER = os.path.join(NARC, f"UD_SPLITS_{lang}")
        UD_DOC2SENT = os.path.join(NARC, f"UD_SPLITS_DOC2SENT_{lang}")
        UD_ALIGNED = os.path.join(NARC, f"UD_ALIGNED_{lang}")

        build_map(ud_splits, ANN_FOLDER, UD_SPLITS_FOLDER, UD_DOC2SENT, lang)

        # Step 3: Merge UD and annotations
        merge(ud_splits, CONLL_FOLDER, UD_ALIGNED, UD_SPLITS_FOLDER, UD_DOC2SENT)

        ALIGNED_OUTPUT = os.path.join(output_path, "aligned", f"no-narc_{lang}")
        combine_into_splits(ALIGNED_OUTPUT, UD_ALIGNED, lang)
