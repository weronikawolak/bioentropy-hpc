#!/usr/bin/env python3

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from run_nist90b_campaign import (
    ROOT,
    RUNNER,
    ADAPTER,
    PARSER,
    EA_NON_IID,
    check_provenance,
    run_command,
)


CONFIG_ROOT = (
    ROOT
    / "configs"
    / "generated"
    / "dieharder-campaign"
)

DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "results"
    / "external"
    / "nist90b-windows"
)


FLOAT64_COLLAPSE_REFERENCE = {
    1: 5_919_555,
    5: 16_181_612,
    7: 21_156_926,
    8: 10_996_001,
    12: 9_423_224,
}


def write_tsv(
    rows: list[dict],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "source",
        "replicate_id",
        "window_start",
        "window_end_exclusive",
        "window_samples",
        "p1",
        "h_original",
        "assessment_status",
        "h_original_origin",
        "nist_exit_code",
        "provenance_ok",
        "raw_input_sha256",
        "nist_input_sha256",
        "collapse_index_reference",
        "window_contains_collapse_reference",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run windowed NIST SP 800-90B "
            "non-IID assessments on one frozen "
            "BioEntropy realization."
        )
    )

    parser.add_argument(
        "--source",
        default="logistic-float64",
    )

    parser.add_argument(
        "--replicate",
        required=True,
        type=int,
    )

    parser.add_argument(
        "--start",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--stop",
        required=True,
        type=int,
        help=(
            "Exclusive start-position limit "
            "for generated windows."
        ),
    )

    parser.add_argument(
        "--step",
        type=int,
        default=1_000_000,
    )

    parser.add_argument(
        "--window-samples",
        type=int,
        default=1_000_000,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )

    args = parser.parse_args()

    if args.start < 0:
        parser.error("--start must be non-negative")

    if args.stop <= args.start:
        parser.error("--stop must be greater than --start")

    if args.step <= 0:
        parser.error("--step must be positive")

    if args.window_samples < 1_000_000:
        parser.error(
            "--window-samples must be at least 1000000"
        )

    source = args.source
    replicate = args.replicate

    config = (
        CONFIG_ROOT
        / source
        / f"rep{replicate:03d}.yaml"
    )

    if not config.is_file():
        raise FileNotFoundError(
            f"Frozen config missing: {config}"
        )

    result_root = (
        args.output_root
        / source
        / f"rep{replicate:03d}"
    )

    result_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    aggregate_path = (
        ROOT
        / "results"
        / "aggregated"
        / (
            f"nist90b_{source}"
            f"_rep{replicate:03d}_windows.tsv"
        )
    )

    collapse_reference = None

    if source == "logistic-float64":
        collapse_reference = (
            FLOAT64_COLLAPSE_REFERENCE.get(
                replicate
            )
        )

    starts = list(
        range(
            args.start,
            args.stop,
            args.step,
        )
    )

    print(
        f"Source       : {source}"
    )
    print(
        f"Replicate    : {replicate:03d}"
    )
    print(
        f"Windows      : {len(starts)}"
    )
    print(
        f"Window size  : {args.window_samples}"
    )

    if collapse_reference is not None:
        print(
            "Collapse ref : "
            f"{collapse_reference}"
        )

    rows = []

    with tempfile.TemporaryDirectory(
        prefix=(
            "bioentropy-nist90b-window-"
            f"{source}-rep{replicate:03d}-"
        )
    ) as temp_name:
        temp = Path(temp_name)

        raw = temp / "raw.bin"

        runner_result = run_command(
            [
                str(RUNNER),
                "--config",
                str(config.resolve()),
                "--dump-bitstream",
                str(raw),
            ],
            cwd=temp,
        )

        provenance_ok, raw_sha = (
            check_provenance(
                source,
                replicate,
                raw,
            )
        )

        if not provenance_ok:
            raise RuntimeError(
                "Frozen RAW provenance mismatch."
            )

        print(
            "RAW provenance: PASS "
            f"{raw_sha[:12]}..."
        )

        (
            result_root / "runner.txt"
        ).write_text(
            runner_result.stdout,
            encoding="utf-8",
        )

        for start in starts:
            end = (
                start
                + args.window_samples
            )

            print(
                f"\nWindow "
                f"{start:,} .. {end:,}"
            )

            samples = (
                temp
                / f"samples-{start:09d}.bin"
            )

            run_command(
                [
                    sys.executable,
                    str(ADAPTER),
                    str(raw),
                    str(samples),
                    "--start-sample",
                    str(start),
                    "--max-samples",
                    str(args.window_samples),
                ]
            )

            sample_meta_path = (
                samples.with_suffix(
                    samples.suffix + ".json"
                )
            )

            with sample_meta_path.open(
                encoding="utf-8",
            ) as handle:
                sample_meta = json.load(
                    handle
                )

            window_dir = (
                result_root
                / (
                    f"window-"
                    f"{start:09d}-"
                    f"{end:09d}"
                )
            )

            window_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            nist = subprocess.run(
                [
                    str(EA_NON_IID),
                    "-i",
                    samples.name,
                    "1",
                ],
                cwd=temp,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            nist_txt = (
                window_dir
                / "ea_non_iid.txt"
            )

            nist_txt.write_text(
                nist.stdout,
                encoding="utf-8",
            )

            result_json = (
                window_dir
                / "result.json"
            )

            is_constant = (
                sample_meta["zeros"]
                == sample_meta["output_samples"]
                or sample_meta["ones"]
                == sample_meta["output_samples"]
            )

            if nist.returncode == 0:
                run_command(
                    [
                        sys.executable,
                        str(PARSER),
                        "--nist-output",
                        str(nist_txt),
                        "--sample-metadata",
                        str(sample_meta_path),
                        "--output",
                        str(result_json),
                        "--source",
                        source,
                        "--replicate-id",
                        f"{replicate:03d}",
                    ]
                )

                with result_json.open(
                    encoding="utf-8",
                ) as handle:
                    result = json.load(
                        handle
                    )

                result[
                    "assessment_status"
                ] = "nist_estimated"

                result[
                    "h_original_origin"
                ] = "nist_sp800_90b_ea_non_iid"

            elif is_constant:
                result = {
                    "source": source,
                    "replicate_id": (
                        f"{replicate:03d}"
                    ),
                    "assessment": (
                        "initial_non_iid"
                    ),
                    "h_original": 0.0,
                    "bits_per_symbol": 1,
                    "samples": sample_meta[
                        "output_samples"
                    ],
                    "zeros": sample_meta[
                        "zeros"
                    ],
                    "ones": sample_meta[
                        "ones"
                    ],
                    "p1": sample_meta["p1"],
                    "source_bit_order": (
                        sample_meta[
                            "source_bit_order"
                        ]
                    ),
                    "raw_input_sha256": (
                        sample_meta[
                            "input_sha256"
                        ]
                    ),
                    "nist_input_sha256": (
                        sample_meta[
                            "output_sha256"
                        ]
                    ),
                    "truncated": sample_meta[
                        "truncated"
                    ],
                    "nist_output_file": str(
                        nist_txt
                    ),
                    "assessment_status": (
                        "degenerate_constant"
                    ),
                    "h_original_origin": (
                        "empirical_constant_distribution"
                    ),
                }

            else:
                raise RuntimeError(
                    "ea_non_iid failed for a "
                    "non-constant window "
                    f"(exit={nist.returncode}):\n"
                    f"{nist.stdout}"
                )

            result[
                "nist_exit_code"
            ] = nist.returncode

            contains_collapse = False

            if collapse_reference is not None:
                contains_collapse = (
                    start
                    <= collapse_reference
                    < end
                )

            result.update(
                {
                    "window_start": start,
                    "window_end_exclusive": end,
                    "window_samples": (
                        sample_meta[
                            "output_samples"
                        ]
                    ),
                    "provenance_ok": True,
                    "collapse_index_reference": (
                        collapse_reference
                    ),
                    "window_contains_collapse_reference": (
                        contains_collapse
                    ),
                }
            )

            with result_json.open(
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    result,
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")

            rows.append(result)

            write_tsv(
                rows,
                aggregate_path,
            )

            marker = (
                "  <== collapse reference"
                if contains_collapse
                else ""
            )

            print(
                f"H_original = "
                f"{result['h_original']:.6f}"
                f"{marker}"
            )

            samples.unlink(
                missing_ok=True
            )

            sample_meta_path.unlink(
                missing_ok=True
            )

    print("\n=== COMPLETE ===")
    print(
        f"Windows: {len(rows)}"
    )
    print(
        f"TSV    : {aggregate_path}"
    )


if __name__ == "__main__":
    main()
