#!/bin/bash

# Base directories
BASE_DATA_DIR="../data"
CONVERTED_DIR="../data_jsonl"

# remove it first:
rm -rf "${CONVERTED_DIR}"

# Create the converted directory if it doesn't exist
mkdir -p "${CONVERTED_DIR}"

# Get list of datasets
DATASETS=($(ls -d ${BASE_DATA_DIR}/*/ | xargs -n1 basename))

for DATASET in "${DATASETS[@]}"; do
    DATA_DIR="${BASE_DATA_DIR}/${DATASET}"

    echo "Processing dataset: ${DATASET}"

    # Create a subdirectory in the converted directory for this dataset
    DATASET_CONVERTED_DIR="${CONVERTED_DIR}/${DATASET}"
    mkdir -p "${DATASET_CONVERTED_DIR}"

    # Find .conllu files
    for FILE_PATH in ${DATA_DIR}/*-{train,dev,dev.blind,test.blind}.conllu; do
        FILE_NAME=$(basename -- "${FILE_PATH}")
        FILE_BASE="${FILE_NAME%.*}"
        
        echo "  - Converting file: ${FILE_NAME}"

        # Convert .conllu to .jsonl
        python conll_to_jsonl.py "${FILE_PATH}" "${DATASET_CONVERTED_DIR}"

        # # Convert to heads
        # python convert_to_heads.py "${DATASET_CONVERTED_DIR}/${FILE_BASE}.jsonl" "${DATASET_CONVERTED_DIR}/${FILE_BASE}_heads.jsonl"

        echo "  - Done processing file: ${FILE_NAME}"
    done

    echo "Done processing dataset: ${DATASET}"
    echo "----------------------------------------"
done

echo "All datasets have been processed."
