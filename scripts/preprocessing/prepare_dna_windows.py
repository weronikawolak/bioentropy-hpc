#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

GENOME_MANIFEST = (
    ROOT / "datasets/manifests/dna_genomes.tsv"
)

RAW_ROOT = (
    ROOT / "datasets/raw/ncbi"
)

OUTPUT_ROOT = (
    ROOT / "datasets/processed/dna"
)

CONFIG_ROOT = (
    ROOT / "configs/campaigns/dna/reference"
)

WINDOW_MANIFEST_TSV = (
    ROOT / "datasets/manifests/dna_windows.tsv"
)

WINDOW_MANIFEST_JSONL = (
    ROOT / "datasets/manifests/dna_windows.jsonl"
)

WINDOW_LENGTH_NT = 400_000
WINDOWS_PER_GENOME = 10

OUTPUT_BITS = WINDOW_LENGTH_NT * 2

SELECTION_DOMAIN = (
    "BIOENTROPY-HPC-DNA-WINDOW-SELECTION-v1"
)

MASTER_SEED = (
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(
        text.encode("ascii")
    )


def read_fasta(path: Path):
    header = None
    chunks = []

    with path.open(
        "r",
        encoding="ascii",
        errors="strict",
    ) as handle:

        for raw_line in handle:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(">"):
                if header is not None:
                    yield (
                        header.split()[0],
                        "".join(chunks).upper(),
                    )

                header = line[1:].strip()
                chunks = []

            else:
                if header is None:
                    raise RuntimeError(
                        f"Sequence data before FASTA "
                        f"header in {path}"
                    )

                chunks.append(line)

    if header is not None:
        yield (
            header.split()[0],
            "".join(chunks).upper(),
        )


def find_genomic_fasta(
    assembly: str,
) -> Path:

    directory = RAW_ROOT / assembly

    matches = sorted(
        directory.glob(
            "ncbi_dataset/data/**/*_genomic.fna"
        )
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"{assembly}: expected exactly "
            f"one genomic FASTA, found "
            f"{len(matches)}"
        )

    return matches[0]


def candidate_blocks(
    fasta_path: Path,
):
    candidates = []

    for sequence_accession, sequence in read_fasta(
        fasta_path
    ):
        for match in re.finditer(
            r"[ACGT]+",
            sequence,
        ):
            run_start = match.start()
            run_length = (
                match.end() - match.start()
            )

            block_count = (
                run_length //
                WINDOW_LENGTH_NT
            )

            for block_index in range(
                block_count
            ):
                start = (
                    run_start
                    + block_index
                    * WINDOW_LENGTH_NT
                )

                window = sequence[
                    start:
                    start + WINDOW_LENGTH_NT
                ]

                if (
                    len(window)
                    != WINDOW_LENGTH_NT
                ):
                    raise AssertionError(
                        "invalid candidate length"
                    )

                candidates.append(
                    (
                        sequence_accession,
                        start,
                        window,
                    )
                )

    return candidates


def selection_score(
    assembly: str,
    sequence_accession: str,
    start: int,
) -> str:

    material = (
        f"{SELECTION_DOMAIN}\0"
        f"{assembly}\0"
        f"{sequence_accession}\0"
        f"{start}\0"
        f"{WINDOW_LENGTH_NT}"
    )

    return hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()


def write_sequence(
    path: Path,
    sequence: str,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="ascii",
        newline="\n",
    ) as handle:

        for index in range(
            0,
            len(sequence),
            80,
        ):
            handle.write(
                sequence[index:index + 80]
            )
            handle.write("\n")


def write_yaml(
    path: Path,
    experiment_id: str,
    sequence_file: str,
    assembly: str,
    sequence_accession: str,
    window_start: int,
    sequence_sha256: str,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = f'''experiment:
  id: "{experiment_id}"
  replicate_id: 0
  master_seed: "{MASTER_SEED}"

source:
  type: "dna_sequence"
  output_bits: {OUTPUT_BITS}

  parameters:
    sequence_file: "{sequence_file}"
    assembly_accession: "{assembly}"
    sequence_accession: "{sequence_accession}"
    window_start_nt: {window_start}
    window_length_nt: {WINDOW_LENGTH_NT}
    mapping: "acgt_2bit"
    expected_sequence_sha256: "{sequence_sha256}"

execution:
  chunk_bytes: 65536
'''

    path.write_text(
        document,
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return str(
        path.relative_to(ROOT)
    )


def main():
    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    CONFIG_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    with GENOME_MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:

        genomes = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    for genome in genomes:
        slug = genome["slug"]
        organism = genome["organism"]
        assembly = (
            genome["assembly_accession"]
        )

        print()
        print("=" * 70)
        print(organism)
        print(assembly)
        print("=" * 70)

        fasta_path = find_genomic_fasta(
            assembly
        )

        raw_fasta_sha256 = (
            sha256_bytes(
                fasta_path.read_bytes()
            )
        )

        candidates = candidate_blocks(
            fasta_path
        )

        print(
            "Non-overlapping canonical "
            f"candidate blocks: "
            f"{len(candidates)}"
        )

        if (
            len(candidates)
            < WINDOWS_PER_GENOME
        ):
            raise RuntimeError(
                f"{assembly}: only "
                f"{len(candidates)} valid "
                f"{WINDOW_LENGTH_NT}-nt blocks; "
                f"need {WINDOWS_PER_GENOME}"
            )

        ranked = []

        for (
            sequence_accession,
            start,
            sequence,
        ) in candidates:

            score = selection_score(
                assembly,
                sequence_accession,
                start,
            )

            ranked.append(
                (
                    score,
                    sequence_accession,
                    start,
                    sequence,
                )
            )

        ranked.sort(
            key=lambda item: item[0]
        )

        selected = ranked[
            :WINDOWS_PER_GENOME
        ]

        assembly_output = (
            OUTPUT_ROOT / assembly
        )

        assembly_output.mkdir(
            parents=True,
            exist_ok=True,
        )

        for window_index, (
            score,
            sequence_accession,
            start,
            sequence,
        ) in enumerate(selected):

            window_sha256 = (
                sha256_text(sequence)
            )

            window_name = (
                f"window_{window_index:02d}.dna"
            )

            window_path = (
                assembly_output /
                window_name
            )

            write_sequence(
                window_path,
                sequence,
            )

            experiment_id = (
                f"dna-{slug}-w"
                f"{window_index:02d}"
            )

            config_path = (
                CONFIG_ROOT /
                f"{experiment_id}.yaml"
            )

            sequence_file = (
                relative(window_path)
            )

            write_yaml(
                config_path,
                experiment_id,
                sequence_file,
                assembly,
                sequence_accession,
                start,
                window_sha256,
            )

            row = {
                "experiment_id":
                    experiment_id,

                "organism":
                    organism,

                "assembly_accession":
                    assembly,

                "sequence_accession":
                    sequence_accession,

                "window_index":
                    window_index,

                "window_start_nt":
                    start,

                "window_length_nt":
                    WINDOW_LENGTH_NT,

                "output_bits":
                    OUTPUT_BITS,

                "mapping":
                    "acgt_2bit",

                "window_sha256":
                    window_sha256,

                "raw_fasta_sha256":
                    raw_fasta_sha256,

                "selection_score":
                    score,

                "selection_scheme":
                    SELECTION_DOMAIN,

                "sequence_file":
                    sequence_file,

                "config_file":
                    relative(config_path),
            }

            rows.append(row)

            print(
                f"window {window_index:02d}: "
                f"{sequence_accession} "
                f"start={start} "
                f"sha={window_sha256[:12]}..."
            )

    fields = [
        "experiment_id",
        "organism",
        "assembly_accession",
        "sequence_accession",
        "window_index",
        "window_start_nt",
        "window_length_nt",
        "output_bits",
        "mapping",
        "window_sha256",
        "raw_fasta_sha256",
        "selection_score",
        "selection_scheme",
        "sequence_file",
        "config_file",
    ]

    with WINDOW_MANIFEST_TSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    with WINDOW_MANIFEST_JSONL.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for row in rows:
            handle.write(
                json.dumps(
                    row,
                    sort_keys=True,
                )
            )

            handle.write("\n")

    expected = (
        len(genomes)
        * WINDOWS_PER_GENOME
    )

    if len(rows) != expected:
        raise AssertionError(
            f"expected {expected} windows, "
            f"created {len(rows)}"
        )

    print()
    print("=" * 70)
    print(
        f"Prepared {len(rows)} "
        "DNA windows successfully."
    )
    print(
        f"Window length: "
        f"{WINDOW_LENGTH_NT} nt"
    )
    print(
        f"Output per window: "
        f"{OUTPUT_BITS} bits"
    )
    print(
        "Manifest: "
        f"{relative(WINDOW_MANIFEST_TSV)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
