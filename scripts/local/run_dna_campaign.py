#!/usr/bin/env python3

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT / "datasets/manifests/dna_windows.tsv"
)

RUNNER = (
    ROOT / "build/bioentropy-runner"
)


def main() -> int:
    if not RUNNER.exists():
        raise RuntimeError(
            f"Runner not found: {RUNNER}"
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

    if len(rows) != 50:
        raise RuntimeError(
            f"Expected 50 DNA windows, "
            f"found {len(rows)}"
        )

    failures = []

    for index, row in enumerate(
        rows,
        start=1,
    ):
        experiment_id = (
            row["experiment_id"]
        )

        config_path = (
            ROOT / row["config_file"]
        )

        print()
        print("=" * 70)
        print(
            f"[{index:02d}/{len(rows)}] "
            f"{experiment_id}"
        )
        print("=" * 70)

        if not config_path.exists():
            failures.append(
                (
                    experiment_id,
                    "configuration file missing",
                )
            )
            continue

        completed = subprocess.run(
            [
                str(RUNNER),
                "--config",
                str(config_path),
            ],
            cwd=ROOT,
            text=True,
        )

        if completed.returncode != 0:
            failures.append(
                (
                    experiment_id,
                    f"exit code "
                    f"{completed.returncode}",
                )
            )

    print()
    print("=" * 70)

    if failures:
        print(
            f"DNA campaign finished with "
            f"{len(failures)} failure(s)."
        )

        for experiment_id, reason in failures:
            print(
                f"FAIL: {experiment_id}: "
                f"{reason}"
            )

        return 1

    print(
        f"DNA campaign completed: "
        f"{len(rows)}/{len(rows)} successful."
    )
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
