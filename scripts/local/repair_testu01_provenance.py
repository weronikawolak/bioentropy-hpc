#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib
import json
import re

import yaml


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_subset_manifest.tsv"
)

REPAIR = (
    ROOT
    / "results/aggregated"
    / "testu01_provenance_repair.tsv"
)

LOG_ROOT = (
    ROOT
    / "results/raw"
    / "testu01"
)


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def normalize_conditioning_to_raw(path):
    original = path.read_text(
        encoding="utf-8"
    )

    doc = yaml.safe_load(original)

    conditioning = doc.get(
        "conditioning"
    )

    old_mode = (
        conditioning.get(
            "mode",
            "raw",
        )
        if isinstance(
            conditioning,
            dict,
        )
        else "raw"
    )

    if old_mode == "raw":
        return (
            old_mode,
            False,
        )

    if old_mode != "ascon_xof128":
        raise RuntimeError(
            f"{path}: unexpected conditioning "
            f"mode {old_mode!r}"
        )

    lines = original.splitlines(
        keepends=True
    )

    start = None

    for i, line in enumerate(lines):
        if line.strip() == "conditioning:":
            if (
                len(line)
                - len(
                    line.lstrip()
                )
                == 0
            ):
                start = i
                break

    if start is None:
        raise RuntimeError(
            f"{path}: conditioning block "
            "not found"
        )

    changed = False

    for i in range(
        start + 1,
        len(lines),
    ):
        line = lines[i]

        if (
            line.strip()
            and not line[0].isspace()
        ):
            break

        if re.match(
            r"^\s+mode\s*:",
            line,
        ):
            newline = (
                "\n"
                if line.endswith("\n")
                else ""
            )

            indent = line[
                :len(line)
                - len(line.lstrip())
            ]

            lines[i] = (
                f"{indent}mode: raw"
                f"{newline}"
            )

            changed = True
            break

    if not changed:
        raise RuntimeError(
            f"{path}: conditioning.mode "
            "not found"
        )

    path.write_text(
        "".join(lines),
        encoding="utf-8",
    )

    return (
        old_mode,
        True,
    )


def main():
    if not MANIFEST.is_file():
        raise RuntimeError(
            "Missing frozen TestU01 manifest"
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
            f"Expected 11 sources, "
            f"got {len(rows)}"
        )

    repair_rows = []

    for row in rows:
        label = row["label"]

        path = (
            ROOT
            / row["config"]
        )

        old_sha = sha256(path)

        recorded_sha = (
            row["config_sha256"]
        )

        if old_sha != recorded_sha:
            raise RuntimeError(
                f"{label}: current config SHA "
                "does not match frozen manifest"
            )

        (
            old_mode,
            changed,
        ) = (
            normalize_conditioning_to_raw(
                path
            )
        )

        new_sha = sha256(path)

        #
        # Keep the frozen historical hash
        # explicitly. Do not silently replace
        # provenance.
        #
        repair_rows.append(
            {
                "source":
                    label,
                "old_conditioning_mode":
                    old_mode,
                "new_conditioning_mode":
                    "raw",
                "config_changed":
                    int(changed),
                "original_config_sha256":
                    old_sha,
                "repaired_config_sha256":
                    new_sha,
                "reason":
                    (
                        "TestU01 adapter consumed "
                        "RandomnessSource directly; "
                        "conditioning pipeline was "
                        "not executed"
                    ),
            }
        )

        row["config_sha256"] = (
            new_sha
        )

        #
        # Repair local execution metadata only.
        # Preserve original SHA separately.
        #
        metadata_path = (
            LOG_ROOT
            / (
                "smallcrush_"
                f"{label}_rep000.json"
            )
        )

        if metadata_path.is_file():
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            previous = metadata.get(
                "config_sha256"
            )

            if previous not in (
                old_sha,
                new_sha,
            ):
                raise RuntimeError(
                    f"{label}: result metadata "
                    "references an unexpected SHA"
                )

            if old_sha != new_sha:
                metadata[
                    "original_config_sha256"
                ] = old_sha

            metadata[
                "config_sha256"
            ] = new_sha

            metadata[
                "provenance_repair"
            ] = (
                "conditioning metadata normalized "
                "to raw; SmallCrush execution was "
                "unchanged because the adapter "
                "consumes RandomnessSource output "
                "directly"
            )

            metadata_path.write_text(
                json.dumps(
                    metadata,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

        print(
            f"{label:28s} "
            f"{old_mode:12s} -> raw "
            f"changed={changed}"
        )

    columns = list(
        rows[0].keys()
    )

    with MANIFEST.open(
        "w",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(rows)

    repair_columns = list(
        repair_rows[0].keys()
    )

    with REPAIR.open(
        "w",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=repair_columns,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            repair_rows
        )

    print()
    print(
        "PASSED: TestU01 provenance "
        "repair complete"
    )
    print("Saved:", REPAIR)


if __name__ == "__main__":
    main()
