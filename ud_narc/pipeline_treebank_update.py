import os

from align_treebank import align_treebank

ud_treebanks = {
    "bokmål": os.path.join(os.getcwd(), "data", "UD", "UD_Norwegian-Bokmaal"),
    "nynorsk": os.path.join(os.getcwd(), "data", "UD", "UD_Norwegian-Nynorsk"),
}

other_treebanks = {
    "norne": {
        "bokmål": os.path.join(os.getcwd(), "data", "norne", "ud", "nob"),
        "nynorsk": os.path.join(os.getcwd(), "data", "norne", "ud", "nno"),
    }
}

if __name__ == "__main__":
    output_path = os.path.join(os.getcwd(), "output")
    aligned_path = os.path.join(output_path, "aligned")

    lang = "bokmål"
    corpus = "norne"

    ud_path = ud_treebanks[lang]
    outdated_treebank_path = other_treebanks[corpus][lang]

    if os.path.exists(aligned_path) and len(os.listdir(aligned_path)) == 0:
        print(f"Removing {os.path.basename(aligned_path)}...")
    if not os.path.exists(aligned_path):
        align_treebank(outdated_treebank_path, ud_path, aligned_path)
