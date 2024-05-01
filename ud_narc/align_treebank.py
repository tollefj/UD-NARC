import argparse
import os
from typing import List

from conllu import TokenList, parse
from tqdm import tqdm
from util import Language, get_paths


def align_treebank(
    source: str,
    ud: str,
    output: str,
    train_key="train",
    test_key="test",
    dev_key="dev",
) -> None:
    """
    Aligns the source + UD and writes the aligned data to CoNLL-U

    Args:
        source (str): The path to the source directory.
        ud (str): The path to the UD directory.
        output (str): The path to the output directory.
        train_key (str): The key for the training data.
        test_key (str): The key for the testing data.
        dev_key (str): The key for the development data.

    Returns:
        None
    """
    os.makedirs(output, exist_ok=True)

    ud = get_paths(ud)
    source = get_paths(source)

    for split in [train_key, test_key, dev_key]:
        source_path = getattr(source, split)
        ud_path = getattr(ud, split)
        print(f"Processing {source_path.split('/')[-1]} and {ud_path.split('/')[-1]}")

        with open(ud_path, "r", encoding="utf-8") as ud_f, open(
            source_path, "r", encoding="utf-8"
        ) as entity_f:
            ud_data = parse(ud_f.read())
            entity_data = parse(entity_f.read())

        out_filename = f"aligned-ud-{split}.conllu"
        out = os.path.join(output, out_filename)

        aligned_data = align_sentences(ud_data, entity_data)

        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for sent in aligned_data:
                f.write(sent.serialize())


def align_sentences(
    ud_data: List[TokenList], entity_data: List[TokenList]
) -> List[TokenList]:
    """
    Aligns the sentences in the UD and source corpora.

    Args:
        ud_data (List[TokenList]): The UD corpus.
        entity_data (List[TokenList]): The source data.

    Returns:
        List[TokenList]: The aligned data.
    """
    aligned_data = []

    # some sentences are split across two sentences in the source data
    # keep track of this index
    entity_extra_idx_iterator = 0

    for i in tqdm(range(len(ud_data))):
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
            # try to match the UD sent with the next source sent
            # such that UD1 = source1 + source2
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
            # that is, the source sentence has an unnecessary token at the beginning. Ignore it!
            entity_tokens = [t for t in entity_sent]
            merged = TokenList(entity_tokens[1:])
            aligned = merge_sentences(ud_sent, merged)
            ud_data[i] = aligned
        else:
            print(f"Mismatched sentences on line {ud_sent.metadata['sent_id']}")
            print(ud_sent.metadata["text"])
            print(entity_sent.metadata["text"])
            print("_" * 40)

        ud_data[i].metadata = meta
        aligned_data.append(ud_data[i])

    return aligned_data


def merge_sentences(ud: TokenList, entity: TokenList) -> TokenList:
    """
    Merges UD and source corpus data for a single sentence.

    Args:
        ud (TokenList): The UD Norwegian corpus data for the sentence.
        entity (TokenList): The source corpus data for the sentence.

    Returns:
        TokenList: The merged data.
    """
    ud_toks = [t for t in ud]
    entity_toks = [t for t in entity]
    for j, ud_tok in enumerate(ud_toks):
        ud_misc = ud_tok["misc"] or {}
        entity_misc = entity_toks[j]["misc"] or {}
        entity_misc = {k: v for k, v in entity_misc.items() if k == "name"}
        ud_misc.update(entity_misc)
        ud_tok["misc"] = ud_misc

    return TokenList(ud_toks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", "-n", type=str, help="source data", default="data/source/ud"
    )
    parser.add_argument("--ud", "-u", type=str, help="Source for UD data", default="UD")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Merged files location",
        default="data/source-aligned",
    )
    args = parser.parse_args()

    align_treebank(args.source, args.ud, args.output)
