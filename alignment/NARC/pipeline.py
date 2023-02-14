import os

from build_ud_narc_map import build_map
from combine_splits import combine_into_splits
from merge_ud_narc import merge
from transform import convert_ann_to_json, convert_json_to_conll
from util import get_ud_splits

if __name__ == "__main__":
    langs = ["bokmaal", "nynorsk"]

    NARC = "NARC"
    for lang in langs:
        ANN_FOLDER = os.path.join(NARC, f"annotations_{lang}")
        JSON_FOLDER = os.path.join(NARC, f"annotations_jsonlines_{lang}")
        CONLL_FOLDER = os.path.join(NARC, f"annotations_conll_{lang}")

        print(f"Converting {ANN_FOLDER} to {JSON_FOLDER}")
        convert_ann_to_json(ANN_FOLDER, JSON_FOLDER)
        print(f"Converting {JSON_FOLDER} to {CONLL_FOLDER}")
        convert_json_to_conll(JSON_FOLDER, CONLL_FOLDER)

        ud_splits = get_ud_splits(lang)

        UD_SPLITS_FOLDER = os.path.join(NARC, f"UD_SPLITS_{lang}")
        UD_DOC2SENT = os.path.join(NARC, f"UD_SPLITS_DOC2SENT_{lang}")
        UD_NARC = os.path.join(NARC, f"UD_NARC_MERGED_{lang}")

        print(f"Building mapping between NARC and UD {lang}...")
        build_map(
            ud_splits=ud_splits,
            narc_folder=ANN_FOLDER,
            ud_split_folder=UD_SPLITS_FOLDER,
            doc2sent_folder=UD_DOC2SENT,
        )
        print("Merging compatible UD and NARC files...")
        merge(
            ud_splits=ud_splits,
            narc_conll=CONLL_FOLDER,
            merged_narc_ud=UD_NARC,
            ud_split_folder=UD_SPLITS_FOLDER,
            doc2sent_folder=UD_DOC2SENT,
        )
        OUTPUT = f"no-narc_{lang}"
        combine_into_splits(output=OUTPUT, merge_dir=UD_NARC, language=lang)
        print("-" * 50)
