#!/usr/bin/env bash

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

MANIFEST="datasets/manifests/dna_genomes.tsv"
RAW_ROOT="datasets/raw/ncbi"

if [ -x "tools/ncbi/datasets" ]; then
    DATASETS="tools/ncbi/datasets"
elif command -v datasets >/dev/null 2>&1; then
    DATASETS="$(command -v datasets)"
else
    echo "ERROR: NCBI datasets CLI not found."
    exit 1
fi

mkdir -p "${RAW_ROOT}"

tail -n +2 "${MANIFEST}" |
while IFS=$'\t' read -r slug organism assembly; do

    echo
    echo "========================================"
    echo "${organism}"
    echo "${assembly}"
    echo "========================================"

    target="${RAW_ROOT}/${assembly}"
    zipfile="${RAW_ROOT}/${assembly}.zip"

    existing="$(
        find "${target}" \
            -type f \
            -name '*_genomic.fna' \
            -print -quit \
            2>/dev/null || true
    )"

    if [ -n "${existing}" ]; then
        echo "Already downloaded:"
        echo "${existing}"
        continue
    fi

    rm -rf "${target}"
    mkdir -p "${target}"

    "${DATASETS}" download genome accession \
        "${assembly}" \
        --include genome \
        --filename "${zipfile}" \
        --no-progressbar

    unzip -q \
        "${zipfile}" \
        -d "${target}"

    rm -f "${zipfile}"

    mapfile -t fasta_files < <(
        find "${target}/ncbi_dataset/data" \
            -type f \
            -name '*_genomic.fna'
    )

    if [ "${#fasta_files[@]}" -ne 1 ]; then
        echo "ERROR: expected exactly one genomic FASTA."
        printf '%s\n' "${fasta_files[@]}"
        exit 1
    fi

    echo "Downloaded:"
    echo "${fasta_files[0]}"
done

echo
echo "All genome downloads completed."
