#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = (
    ROOT
    / "configs/campaigns/dna/reference"
)

WINDOW_DIR = (
    ROOT
    / "results/bitstreams/dna-corpus/windows"
)

CORPUS = (
    ROOT
    / "results/bitstreams/dna-corpus/"
      "dna-reference-corpus.bin"
)

MANIFEST = (
    ROOT
    / "results/bitstreams/dna-corpus/"
      "manifest.tsv"
)

RUNNER = (
    ROOT
    / "build/bioentropy-runner"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_record(path: Path):
    document = yaml.safe_load(
        path.read_text()
    )

    experiment = document["experiment"]
    source = document["source"]
    parameters = source["parameters"]

    return {
        "path": path,
        "experiment_id":
            experiment["id"],
        "assembly_accession":
            parameters["assembly_accession"],
        "sequence_accession":
            parameters["sequence_accession"],
        "window_start_nt":
            int(parameters["window_start_nt"]),
        "window_length_nt":
            int(parameters["window_length_nt"]),
        "expected_sequence_sha256":
            parameters["expected_sequence_sha256"],
    }


def main():
    configs = sorted(
        CONFIG_DIR.glob("*.yaml")
    )

    if len(configs) != 50:
        raise SystemExit(
            "Expected exactly 50 DNA reference configs; "
            f"found {len(configs)}."
        )

    records = [
        load_record(path)
        for path in configs
    ]

    records.sort(
        key=lambda row: (
            row["assembly_accession"],
            row["sequence_accession"],
            row["window_start_nt"],
            row["experiment_id"],
        )
    )

    WINDOW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CORPUS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    with CORPUS.open("wb") as corpus:
        for index, record in enumerate(
            records
        ):
            experiment_id = (
                record["experiment_id"]
            )

            output = (
                WINDOW_DIR
                / f"{index:02d}-{experiment_id}.bin"
            )

            print(
                f"[{index + 1:02d}/50] "
                f"{experiment_id}"
            )

            subprocess.run(
                [
                    str(RUNNER),
                    "--config",
                    str(record["path"]),
                    "--dump-bitstream",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
            )

            data = output.read_bytes()

            if len(data) != 100_000:
                raise SystemExit(
                    f"Unexpected DNA stream size: "
                    f"{output} = {len(data)} bytes"
                )

            corpus.write(data)

            rows.append(
                {
                    **record,
                    "order": index,
                    "bitstream_bytes":
                        len(data),
                    "bitstream_sha256":
                        sha256(output),
                }
            )

    corpus_size = CORPUS.stat().st_size
    corpus_sha = sha256(CORPUS)

    if corpus_size != 5_000_000:
        raise SystemExit(
            "Unexpected corpus size: "
            f"{corpus_size}"
        )

    columns = [
        "order",
        "experiment_id",
        "assembly_accession",
        "sequence_accession",
        "window_start_nt",
        "window_length_nt",
        "expected_sequence_sha256",
        "bitstream_bytes",
        "bitstream_sha256",
    ]

    with MANIFEST.open("w") as handle:
        handle.write(
            "\t".join(columns) + "\n"
        )

        for row in rows:
            handle.write(
                "\t".join(
                    str(row[column])
                    for column in columns
                )
                + "\n"
            )

    metadata = {
        "construction":
            "concatenation_without_separators",
        "ordering":
            "assembly_accession, "
            "sequence_accession, "
            "window_start_nt, experiment_id",
        "window_count":
            len(rows),
        "bytes":
            corpus_size,
        "bits":
            corpus_size * 8,
        "sha256":
            corpus_sha,
    }

    metadata_path = (
        CORPUS.parent
        / "dna-reference-corpus.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        )
        + "\n"
    )

    print()
    print("DNA corpus complete")
    print("===================")
    print(
        "windows :",
        len(rows),
    )
    print(
        "bytes   :",
        corpus_size,
    )
    print(
        "bits    :",
        corpus_size * 8,
    )
    print(
        "sha256  :",
        corpus_sha,
    )
    print(
        "corpus  :",
        CORPUS,
    )
    print(
        "manifest:",
        MANIFEST,
    )


if __name__ == "__main__":
    main()
