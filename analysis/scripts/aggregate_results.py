#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_SCHEMA_VERSION = 1


class ResultValidationError(ValueError):
    """Raised when an experiment result does not match the expected schema."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate BioEntropy HPC experiment JSON results "
            "into a single Apache Parquet dataset."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("results/metrics"),
        help="Directory containing experiment JSON files.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/aggregated/results.parquet"),
        help="Output Parquet file.",
    )

    return parser.parse_args()


def require_key(
    mapping: dict[str, Any],
    key: str,
    context: str,
) -> Any:
    if key not in mapping:
        raise ResultValidationError(
            f"Missing required key '{key}' in {context}"
        )

    return mapping[key]


def load_result(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except json.JSONDecodeError as exc:
        raise ResultValidationError(
            f"Invalid JSON in {path}: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise ResultValidationError(
            f"Top-level JSON value must be an object: {path}"
        )

    schema_version = require_key(
        document,
        "schema_version",
        str(path),
    )

    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ResultValidationError(
            f"Unsupported schema_version={schema_version} "
            f"in {path}; expected {SUPPORTED_SCHEMA_VERSION}"
        )

    experiment = require_key(
        document,
        "experiment",
        str(path),
    )

    source = require_key(
        document,
        "source",
        str(path),
    )

    execution = require_key(
        document,
        "execution",
        str(path),
    )

    reproducibility = require_key(
        document,
        "reproducibility",
        str(path),
    )

    statistics = require_key(
        document,
        "statistics",
        str(path),
    )

    row = {
        "schema_version": schema_version,

        "experiment_id": require_key(
            experiment,
            "id",
            "experiment",
        ),

        "replicate_id": require_key(
            experiment,
            "replicate_id",
            "experiment",
        ),

        "source_name": require_key(
            source,
            "name",
            "source",
        ),

        "output_bits": require_key(
            source,
            "output_bits",
            "source",
        ),

        "chunk_bytes": require_key(
            execution,
            "chunk_bytes",
            "execution",
        ),

        "derived_seed": require_key(
            reproducibility,
            "derived_seed",
            "reproducibility",
        ),

        "bitstream_sha256": require_key(
            reproducibility,
            "bitstream_sha256",
            "reproducibility",
        ),

        "total_bytes": require_key(
            statistics,
            "total_bytes",
            "statistics",
        ),

        "total_bits": require_key(
            statistics,
            "total_bits",
            "statistics",
        ),

        "zeros": require_key(
            statistics,
            "zeros",
            "statistics",
        ),

        "ones": require_key(
            statistics,
            "ones",
            "statistics",
        ),

        "probability_zero": require_key(
            statistics,
            "probability_zero",
            "statistics",
        ),

        "probability_one": require_key(
            statistics,
            "probability_one",
            "statistics",
        ),

        "bias": require_key(
            statistics,
            "bias",
            "statistics",
        ),

        "shannon_entropy": require_key(
            statistics,
            "shannon_entropy",
            "statistics",
        ),

        "result_file": str(path),
    }

    validate_row(row, path)

    return row


def validate_row(
    row: dict[str, Any],
    path: Path,
) -> None:
    if not row["experiment_id"]:
        raise ResultValidationError(
            f"Empty experiment_id in {path}"
        )

    if row["output_bits"] <= 0:
        raise ResultValidationError(
            f"output_bits must be positive in {path}"
        )

    if row["total_bits"] != row["output_bits"]:
        raise ResultValidationError(
            f"total_bits does not match output_bits in {path}"
        )

    if row["zeros"] + row["ones"] != row["total_bits"]:
        raise ResultValidationError(
            f"zeros + ones does not equal total_bits in {path}"
        )

    if not 0.0 <= row["probability_zero"] <= 1.0:
        raise ResultValidationError(
            f"Invalid probability_zero in {path}"
        )

    if not 0.0 <= row["probability_one"] <= 1.0:
        raise ResultValidationError(
            f"Invalid probability_one in {path}"
        )

    if not 0.0 <= row["bias"] <= 0.5:
        raise ResultValidationError(
            f"Invalid bias in {path}"
        )

    if not 0.0 <= row["shannon_entropy"] <= 1.0:
        raise ResultValidationError(
            f"Invalid Shannon entropy in {path}"
        )

    if len(row["derived_seed"]) != 64:
        raise ResultValidationError(
            f"Invalid derived seed length in {path}"
        )

    if len(row["bitstream_sha256"]) != 64:
        raise ResultValidationError(
            f"Invalid SHA-256 length in {path}"
        )


def collect_results(input_dir: Path) -> pd.DataFrame:
    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {input_dir}"
        )

    paths = sorted(input_dir.glob("*.json"))

    if not paths:
        raise FileNotFoundError(
            f"No JSON result files found in: {input_dir}"
        )

    rows = [
        load_result(path)
        for path in paths
    ]

    dataframe = pd.DataFrame(rows)

    duplicate_mask = dataframe.duplicated(
        subset=[
            "experiment_id",
            "replicate_id",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        duplicates = dataframe.loc[
            duplicate_mask,
            [
                "experiment_id",
                "replicate_id",
                "result_file",
            ],
        ]

        raise ResultValidationError(
            "Duplicate experiment/replicate combinations detected:\n"
            + duplicates.to_string(index=False)
        )

    dataframe = dataframe.sort_values(
        by=[
            "source_name",
            "experiment_id",
            "replicate_id",
        ]
    ).reset_index(drop=True)

    return dataframe


def write_parquet(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        output_path,
        engine="pyarrow",
        index=False,
        compression="zstd",
    )


def main() -> int:
    arguments = parse_arguments()

    try:
        dataframe = collect_results(
            arguments.input_dir
        )

        write_parquet(
            dataframe,
            arguments.output,
        )

    except (
        FileNotFoundError,
        ResultValidationError,
        OSError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1

    print("BioEntropy HPC result aggregation")
    print("--------------------------------")
    print(f"Input directory : {arguments.input_dir}")
    print(f"Experiments     : {len(dataframe)}")
    print(f"Sources         : {dataframe['source_name'].nunique()}")
    print(f"Output          : {arguments.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
