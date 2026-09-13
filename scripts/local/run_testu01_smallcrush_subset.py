#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_subset_manifest.tsv"
)

BINARY = (
    ROOT
    / "build"
    / "testu01-smallcrush-source"
)

LOG_DIR = (
    ROOT
    / "results/raw/testu01"
)


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    if not BINARY.is_file():
        raise RuntimeError(
            "Missing TestU01 adapter: "
            + str(BINARY)
        )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(rows) != 11:
        raise RuntimeError(
            f"Expected 11 sources, got {len(rows)}"
        )

    for index, row in enumerate(
        rows,
        start=1,
    ):
        label = row["label"]

        config = (
            ROOT
            / row["config"]
        )

        if sha256(config) != row[
            "config_sha256"
        ]:
            raise RuntimeError(
                f"{label}: frozen config SHA mismatch"
            )

        log = (
            LOG_DIR
            / f"smallcrush_{label}_rep000.log"
        )

        meta = (
            LOG_DIR
            / f"smallcrush_{label}_rep000.json"
        )

        if (
            log.is_file()
            and meta.is_file()
        ):
            metadata = json.loads(
                meta.read_text()
            )

            if (
                metadata.get(
                    "returncode"
                ) == 0
                and metadata.get(
                    "config_sha256"
                )
                == row["config_sha256"]
            ):
                print(
                    f"[{index:02d}/"
                    f"{len(rows):02d}] "
                    f"{label}: RESUME"
                )
                continue

        print(
            f"[{index:02d}/"
            f"{len(rows):02d}] "
            f"{label}: RUN",
            flush=True,
        )

        command = [
            str(BINARY),
            "--config",
            str(config),
        ]

        started = (
            time.time()
        )

        with log.open(
            "w",
            encoding="utf-8",
        ) as output:
            process = subprocess.run(
                command,
                cwd=ROOT,
                stdout=output,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

        elapsed = (
            time.time()
            - started
        )

        metadata = {
            "label":
                label,
            "config":
                row["config"],
            "config_sha256":
                row["config_sha256"],
            "returncode":
                process.returncode,
            "elapsed_seconds":
                elapsed,
            "log":
                str(
                    log.relative_to(ROOT)
                ),
        }

        meta.write_text(
            json.dumps(
                metadata,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        if process.returncode != 0:
            print(
                f"FAILED: {label}"
            )
            print(
                f"See: {log}"
            )

            return (
                process.returncode
            )

        print(
            f"       {label}: PASS execution"
        )

    print()
    print(
        "PASSED: all SmallCrush executions completed"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
