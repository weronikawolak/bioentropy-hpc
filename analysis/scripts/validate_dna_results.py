#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT / "datasets/manifests/dna_windows.tsv"
)

RESULT_ROOT = (
    ROOT / "results/metrics"
)

SUMMARY_PATH = (
    ROOT / "results/aggregated/"
    "dna_screening.tsv"
)


def main():
    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        manifest_rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    assert len(manifest_rows) == 50

    summary = []
    bitstream_hashes = set()

    for row in manifest_rows:
        experiment_id = (
            row["experiment_id"]
        )

        result_path = (
            RESULT_ROOT
            / f"{experiment_id}_rep0000.json"
        )

        if not result_path.exists():
            raise RuntimeError(
                f"Missing result: {result_path}"
            )

        with result_path.open(
            encoding="utf-8",
        ) as handle:
            result = json.load(handle)

        assert (
            result["schema_version"]
            == 1
        )

        assert (
            result["experiment"]["id"]
            == experiment_id
        )

        assert (
            result["experiment"]["replicate_id"]
            == 0
        )

        source = result["source"]
        params = source["parameters"]
        stats = result["statistics"]

        assert (
            source["name"]
            == "dna_sequence"
        )

        assert (
            source["output_bits"]
            == int(row["output_bits"])
            == 800_000
        )

        assert (
            params["assembly_accession"]
            == row["assembly_accession"]
        )

        assert (
            params["sequence_accession"]
            == row["sequence_accession"]
        )

        assert (
            params["window_start_nt"]
            == int(row["window_start_nt"])
        )

        assert (
            params["window_length_nt"]
            == int(row["window_length_nt"])
            == 400_000
        )

        assert (
            params["mapping"]
            == row["mapping"]
            == "acgt_2bit"
        )

        assert (
            params[
                "expected_sequence_sha256"
            ]
            == row["window_sha256"]
        )

        assert (
            params["uses_experiment_seed"]
            is False
        )

        assert stats["total_bits"] == 800_000
        assert stats["total_bytes"] == 100_000

        assert (
            stats["zeros"]
            + stats["ones"]
            == stats["total_bits"]
        )

        assert (
            0.0
            <= stats["bias"]
            <= 0.5
        )

        assert (
            0.0
            <= stats["shannon_entropy"]
            <= 1.0
        )

        bitstream_sha = (
            result["reproducibility"]
            ["bitstream_sha256"]
        )

        if bitstream_sha in bitstream_hashes:
            raise RuntimeError(
                "Duplicate DNA bitstream SHA-256 "
                f"detected for {experiment_id}"
            )

        bitstream_hashes.add(
            bitstream_sha
        )

        summary.append(
            {
                "experiment_id":
                    experiment_id,

                "organism":
                    row["organism"],

                "assembly_accession":
                    row["assembly_accession"],

                "sequence_accession":
                    row["sequence_accession"],

                "window_index":
                    row["window_index"],

                "window_start_nt":
                    row["window_start_nt"],

                "bias":
                    stats["bias"],

                "shannon_entropy":
                    stats["shannon_entropy"],

                "zeros":
                    stats["zeros"],

                "ones":
                    stats["ones"],

                "bitstream_sha256":
                    bitstream_sha,
            }
        )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "experiment_id",
        "organism",
        "assembly_accession",
        "sequence_accession",
        "window_index",
        "window_start_nt",
        "bias",
        "shannon_entropy",
        "zeros",
        "ones",
        "bitstream_sha256",
    ]

    with SUMMARY_PATH.open(
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
        writer.writerows(summary)

    print(
        f"Validated {len(summary)} "
        "DNA result files."
    )

    print(
        f"Unique bitstreams: "
        f"{len(bitstream_hashes)}"
    )

    print(
        "Summary written to: "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        "\nDNA campaign validation PASSED"
    )


if __name__ == "__main__":
    main()
