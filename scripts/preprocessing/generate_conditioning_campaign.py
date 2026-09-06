#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SCREENING_MANIFEST = (
    ROOT
    / "configs/generated/screening"
    / "manifest.tsv"
)

SCREENING_GENERATOR = (
    ROOT
    / "scripts/preprocessing"
    / "generate_screening_campaign.py"
)

LOGISTIC_CANDIDATES = (
    ROOT
    / "results/aggregated"
    / "logistic_candidates.tsv"
)

DNA_CONFIG_DIR = (
    ROOT
    / "configs/campaigns/dna/reference"
)

OUTPUT_ROOT = (
    ROOT
    / "configs/generated/conditioning"
)

MANIFEST_OUT = (
    OUTPUT_ROOT
    / "manifest.tsv"
)


def ensure_screening_campaign():
    if SCREENING_MANIFEST.exists():
        return

    print(
        "Screening manifest not found; "
        "generating screening configs..."
    )

    subprocess.run(
        [
            sys.executable,
            str(SCREENING_GENERATOR),
        ],
        cwd=ROOT,
        check=True,
    )

    if not SCREENING_MANIFEST.exists():
        raise RuntimeError(
            "screening manifest was not generated"
        )


def read_tsv(path: Path):
    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def extract_scalar(
    text: str,
    key: str,
):
    pattern = re.compile(
        rf"(?m)^\s+{re.escape(key)}:\s*(.+?)\s*$"
    )

    match = pattern.search(text)

    if match is None:
        raise RuntimeError(
            f"could not find YAML key: {key}"
        )

    value = match.group(1).strip()

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        value = value[1:-1]

    return value


def add_conditioning(
    source_text: str,
    mode: str,
):
    if re.search(
        r"(?m)^conditioning:\s*$",
        source_text,
    ):
        raise RuntimeError(
            "base config already contains "
            "a conditioning section"
        )

    text = source_text.rstrip()

    return (
        text
        + "\n\n"
        + "conditioning:\n"
        + f"  mode: {mode}\n"
    )


def selected_logistic_ids():
    if not LOGISTIC_CANDIDATES.exists():
        return set()

    rows = read_tsv(
        LOGISTIC_CANDIDATES
    )

    selected = {
        row["experiment_id"].strip()
        for row in rows
        if row.get("experiment_id", "").strip()
    }

    return selected


def collect_screening_bases():
    rows = read_tsv(
        SCREENING_MANIFEST
    )

    selected_logistic = (
        selected_logistic_ids()
    )

    bases = []

    seen = set()

    for row in rows:
        source = row["source"].strip()
        experiment_id = (
            row["experiment_id"].strip()
        )
        replicate_id = int(
            row["replicate_id"]
        )

        include = False

        if source in {
            "cellular_automaton",
            "chacha20_reference",
        }:
            include = True

        elif (
            source == "logistic"
            and experiment_id
            in selected_logistic
        ):
            include = True

        if not include:
            continue

        identity = (
            experiment_id,
            replicate_id,
        )

        if identity in seen:
            raise RuntimeError(
                "duplicate screening identity: "
                f"{identity}"
            )

        seen.add(identity)

        config_path = (
            ROOT
            / row["config_file"].strip()
        )

        if not config_path.exists():
            raise RuntimeError(
                "screening config missing: "
                f"{config_path}"
            )

        bases.append(
            {
                "source_family": source,
                "experiment_id":
                    experiment_id,
                "replicate_id":
                    replicate_id,
                "base_config":
                    config_path,
            }
        )

    return bases


def collect_dna_bases():
    if not DNA_CONFIG_DIR.exists():
        raise RuntimeError(
            f"DNA config directory missing: "
            f"{DNA_CONFIG_DIR}"
        )

    configs = sorted(
        DNA_CONFIG_DIR.glob("*.yaml")
    )

    if len(configs) != 50:
        raise RuntimeError(
            "expected 50 DNA configs, "
            f"found {len(configs)}"
        )

    bases = []

    for path in configs:
        text = path.read_text(
            encoding="utf-8"
        )

        experiment_id = extract_scalar(
            text,
            "id",
        )

        replicate_id = int(
            extract_scalar(
                text,
                "replicate_id",
            )
        )

        bases.append(
            {
                "source_family":
                    "dna_sequence",

                "experiment_id":
                    experiment_id,

                "replicate_id":
                    replicate_id,

                "base_config":
                    path,
            }
        )

    return bases


def main():
    ensure_screening_campaign()

    bases = (
        collect_screening_bases()
        + collect_dna_bases()
    )

    identities = [
        (
            item["experiment_id"],
            item["replicate_id"],
        )
        for item in bases
    ]

    if len(identities) != len(
        set(identities)
    ):
        raise RuntimeError(
            "duplicate base experiment identity"
        )

    raw_dir = OUTPUT_ROOT / "raw"
    ascon_dir = (
        OUTPUT_ROOT / "ascon_xof128"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    ascon_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove old generated YAML files so reruns
    # reflect the current candidate selection.
    for directory in (
        raw_dir,
        ascon_dir,
    ):
        for path in directory.glob(
            "*.yaml"
        ):
            path.unlink()

    manifest_rows = []

    for item in bases:
        source_text = (
            item["base_config"]
            .read_text(
                encoding="utf-8"
            )
        )

        filename = (
            f"{item['experiment_id']}"
            f"_rep"
            f"{item['replicate_id']:04d}"
            f".yaml"
        )

        for mode, directory in (
            ("raw", raw_dir),
            (
                "ascon_xof128",
                ascon_dir,
            ),
        ):
            output_path = (
                directory / filename
            )

            output_path.write_text(
                add_conditioning(
                    source_text,
                    mode,
                ),
                encoding="utf-8",
            )

            manifest_rows.append(
                {
                    "source_family":
                        item[
                            "source_family"
                        ],

                    "experiment_id":
                        item[
                            "experiment_id"
                        ],

                    "replicate_id":
                        item[
                            "replicate_id"
                        ],

                    "conditioning_mode":
                        mode,

                    "base_config":
                        item[
                            "base_config"
                        ].relative_to(
                            ROOT
                        ),

                    "config_file":
                        output_path
                        .relative_to(ROOT),
                }
            )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "source_family",
        "experiment_id",
        "replicate_id",
        "conditioning_mode",
        "base_config",
        "config_file",
    ]

    with MANIFEST_OUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(
            manifest_rows
        )

    counts = Counter(
        item["source_family"]
        for item in bases
    )

    logistic_ids = (
        selected_logistic_ids()
    )

    print(
        "Conditioning campaign generated"
    )
    print(
        "-------------------------------"
    )

    print(
        f"Base streams      : {len(bases)}"
    )

    print(
        f"Paired configs    : "
        f"{len(manifest_rows)}"
    )

    print()
    print("Base-stream breakdown:")

    for source in sorted(counts):
        print(
            f"  {source:<24} "
            f"{counts[source]}"
        )

    print()
    print(
        "Selected Logistic r groups : "
        f"{len(logistic_ids)}"
    )

    if not logistic_ids:
        print(
            "  none yet — expected before "
            "full screening is complete"
        )

    print()
    print(
        "Manifest:"
    )
    print(
        "  "
        + str(
            MANIFEST_OUT.relative_to(
                ROOT
            )
        )
    )


if __name__ == "__main__":
    main()
