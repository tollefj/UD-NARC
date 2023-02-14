import os

def combine_into_splits(output, merge_dir, language="bokmaal"):
    output_path = os.path.join(os.getcwd(), output)
    os.makedirs(output_path, exist_ok=True)
    
    for split_folder in ["train", "test", "dev"]:
        out_file = os.path.join(output_path, f"narc_{language}_{split_folder}.conllu")
        with open(out_file, "wb") as output_file:
            split_path = os.path.join(merge_dir, split_folder)
            for file in sorted(os.listdir(split_path)):
                if ".conllu" not in file:
                    print("Skipping file: ", file)
                    continue
                with open(os.path.join(split_path, file), "rb") as tmp:
                    output_file.write(tmp.read())

    print(f"Merging into train/test/dev splits done. The files are found in in {output_path}")
