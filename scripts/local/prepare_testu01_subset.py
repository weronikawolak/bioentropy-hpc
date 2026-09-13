#!/usr/bin/env python3

from pathlib import Path
import csv
import hashlib

import yaml


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_subset_manifest.tsv"
)

MASTER_SEED = (
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
)


SOURCES = [
    {
        "label":
            "logistic-float32",
        "type":
            "logistic",
        "config":
            "configs/testu01/"
            "logistic-float32.yaml",
        "historical_template":
            "configs/generated/"
            "dieharder-campaign-ascon-smoke/"
            "logistic-float32/rep000.yaml",
    },
    {
        "label":
            "logistic-float64",
        "type":
            "logistic",
        "config":
            "configs/testu01/"
            "logistic-float64.yaml",
        "historical_template":
            "configs/generated/"
            "dieharder-campaign-ascon-smoke/"
            "logistic-float64/rep000.yaml",
    },
    {
        "label":
            "logistic-fixed_q3_29",
        "type":
            "logistic",
        "config":
            "configs/testu01/"
            "logistic-fixed_q3_29.yaml",
        "historical_template":
            "configs/generated/"
            "dieharder-campaign-ascon-smoke/"
            "logistic-fixed_q3_29/rep000.yaml",
    },
    {
        "label":
            "logistic-mpfr_256",
        "type":
            "logistic",
        "config":
            "configs/testu01/"
            "logistic-mpfr_256.yaml",
        "historical_template":
            "configs/generated/"
            "dieharder-campaign-ascon-smoke/"
            "logistic-mpfr_256/rep000.yaml",
    },
    {
        "label":
            "chen-4d-dcs",
        "type":
            "chen_4d_dcs",
        "config":
            "configs/testu01/"
            "chen-4d-dcs.yaml",
        "historical_template":
            "configs/generated/"
            "chen-4d-dcs-smoke/"
            "chen-4d-dcs-ascon.yaml",
    },
    {
        "label":
            "rule30-cells256",
        "type":
            "cellular_automaton",
        "config":
            "configs/testu01/"
            "rule30-cells256.yaml",
        "historical_template":
            "configs/campaigns/"
            "ca_rule30_smoke.yaml",
    },
    {
        "label":
            "rule30-cells1024",
        "type":
            "cellular_automaton",
        "config":
            "configs/testu01/"
            "rule30-cells1024.yaml",
        "historical_template":
            "configs/generated/"
            "conditioning/ascon_xof128/"
            "ca-rule30-cells1024_rep0000.yaml",
    },
    {
        "label":
            "rule90-cells256",
        "type":
            "cellular_automaton",
        "config":
            "configs/testu01/"
            "rule90-cells256.yaml",
        "historical_template":
            "configs/campaigns/"
            "ca_rule90_smoke.yaml",
    },
    {
        "label":
            "rule90-cells1024",
        "type":
            "cellular_automaton",
        "config":
            "configs/testu01/"
            "rule90-cells1024.yaml",
        "historical_template":
            "configs/generated/"
            "conditioning/ascon_xof128/"
            "ca-rule90-cells1024_rep0000.yaml",
    },
    {
        "label":
            "chacha20",
        "type":
            "chacha20_reference",
        "config":
            "configs/testu01/"
            "chacha20.yaml",
        "historical_template":
            "configs/campaigns/"
            "chacha20_reference_smoke.yaml",
    },
    {
        "label":
            "ctr-drbg-aes256",
        "type":
            "ctr_drbg_aes256_reference",
        "config":
            "configs/testu01/"
            "ctr-drbg-aes256.yaml",
        "historical_template":
            "configs/campaigns/"
            "ctr_drbg_aes256_reference_smoke.yaml",
    },
]


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    rows = []

    for item in SOURCES:
        path = (
            ROOT
            / item["config"]
        )

        if not path.is_file():
            raise RuntimeError(
                f"Missing frozen config: {path}"
            )

        doc = yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )

        experiment = doc.get(
            "experiment",
            {}
        )

        source = doc.get(
            "source",
            {}
        )

        conditioning = doc.get(
            "conditioning",
            {}
        )

        if (
            source.get("type")
            != item["type"]
        ):
            raise RuntimeError(
                f"{item['label']}: "
                "unexpected source type"
            )

        if (
            experiment.get(
                "replicate_id"
            )
            != 0
        ):
            raise RuntimeError(
                f"{item['label']}: "
                "replicate_id must be 0"
            )

        if (
            experiment.get(
                "master_seed"
            )
            != MASTER_SEED
        ):
            raise RuntimeError(
                f"{item['label']}: "
                "unexpected master seed"
            )

        if (
            conditioning.get(
                "mode",
                "raw",
            )
            != "raw"
        ):
            raise RuntimeError(
                f"{item['label']}: "
                "TestU01 frozen config "
                "must be raw"
            )

        rows.append(
            {
                "label":
                    item["label"],
                "source_type":
                    item["type"],
                "replicate_id":
                    0,
                "master_seed":
                    MASTER_SEED,
                "template":
                    item[
                        "historical_template"
                    ],
                "config":
                    item["config"],
                "config_sha256":
                    sha256(path),
            }
        )

        print(
            f"PASS: {item['label']}"
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

    print()
    print(
        "PASSED: 11 explicit frozen "
        "TestU01 configs validated"
    )
    print("Manifest:", MANIFEST)


if __name__ == "__main__":
    main()
