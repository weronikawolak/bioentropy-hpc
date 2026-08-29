#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "configs/generated/conditioning"
    / "manifest.tsv"
)

RUNNER = ROOT / "build/bioentropy-runner"
RESULTS = ROOT / "results/metrics"


def result_path(
    experiment_id: str,
    replicate_id: int,
    mode: str,
) -> Path:
    suffix = (
        "_ascon-xof128"
        if mode == "ascon_xof128"
        else ""
    )

    return (
        RESULTS
        / (
            f"{experiment_id}_"
            f"rep{replicate_id:04d}"
            f"{suffix}.json"
        )
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit-pairs",
        type=int,
        default=None,
        help="Run only the first N experiment pairs",
    )

    parser.add_argument(
        "--source-family",
        default=None,
        help="Optional source family filter",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Rerun results that already exist",
    )

    args = parser.parse_args()

    if not MANIFEST.exists():
        raise SystemExit(
            f"Missing manifest: {MANIFEST}"
        )

    if not RUNNER.exists():
        raise SystemExit(
            f"Missing runner: {RUNNER}"
        )

    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    pairs = defaultdict(dict)

    metadata = {}

    for row in rows:
        source_family = (
            row["source_family"].strip()
        )

        if (
            args.source_family
            and source_family
            != args.source_family
        ):
            continue

        experiment_id = (
            row["experiment_id"].strip()
        )

        replicate_id = int(
            row["replicate_id"]
        )

        mode = (
            row["conditioning_mode"]
            .strip()
        )

        identity = (
            experiment_id,
            replicate_id,
        )

        pairs[identity][mode] = (
            ROOT
            / row["config_file"].strip()
        )

        metadata[identity] = (
            source_family
        )

    identities = sorted(
        pairs.keys()
    )

    if args.limit_pairs is not None:
        identities = identities[
            :args.limit_pairs
        ]

    RESULTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Conditioning campaign runner"
    )
    print(
        "----------------------------"
    )
    print(
        f"Pairs selected : "
        f"{len(identities)}"
    )
    print()

    for index, identity in enumerate(
        identities,
        start=1,
    ):
        experiment_id, replicate_id = (
            identity
        )

        modes = pairs[identity]

        if set(modes) != {
            "raw",
            "ascon_xof128",
        }:
            raise RuntimeError(
                "Incomplete config pair for "
                f"{identity}: {set(modes)}"
            )

        print(
            f"[{index}/{len(identities)}] "
            f"{metadata[identity]} "
            f"{experiment_id} "
            f"rep={replicate_id}"
        )

        for mode in (
            "raw",
            "ascon_xof128",
        ):
            output = result_path(
                experiment_id,
                replicate_id,
                mode,
            )

            if (
                output.exists()
                and not args.force
            ):
                print(
                    f"  {mode:<14} SKIP"
                )
                continue

            config = modes[mode]

            print(
                f"  {mode:<14} RUN"
            )

            subprocess.run(
                [
                    str(RUNNER),
                    "--config",
                    str(config),
                ],
                cwd=ROOT,
                check=True,
            )

    print()
    print("Campaign run finished.")


if __name__ == "__main__":
    main()
