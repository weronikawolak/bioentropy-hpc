#!/usr/bin/env python3

from pathlib import Path
import argparse
import copy
import csv
import hashlib

import yaml


ROOT = Path(__file__).resolve().parents[2]

CONFIG_ROOT = ROOT / "configs/hpc"
MANIFEST_ROOT = ROOT / "results/hpc/manifests"


PROFILES = {
    "ctr-drbg": (
        ROOT
        / "configs/campaigns/"
        "ctr_drbg_aes256_reference_smoke.yaml"
    ),
    "logistic-mpfr": (
        ROOT
        / "configs/testu01/"
        "logistic-mpfr_256.yaml"
    ),
}


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        required=True,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "smoke",
            "strong",
            "weak",
        ],
        required=True,
    )

    parser.add_argument(
        "--items",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--output-bits",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    if args.items < 1:
        raise ValueError(
            "--items must be positive"
        )

    if (
        args.output_bits < 8
        or args.output_bits % 8 != 0
    ):
        raise ValueError(
            "--output-bits must be "
            "positive and divisible by 8"
        )

    template_path = (
        PROFILES[args.profile]
    )

    if not template_path.is_file():
        raise FileNotFoundError(
            template_path
        )

    template = yaml.safe_load(
        template_path.read_text(
            encoding="utf-8"
        )
    )

    output_dir = (
        CONFIG_ROOT
        / args.profile
        / args.mode
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    #
    # The directory is generated from one frozen invocation.
    # Remove only prior generated workload configs.
    #
    for old in output_dir.glob(
        "workload_*.yaml"
    ):
        old.unlink()

    rows = []

    for index in range(args.items):
        document = copy.deepcopy(
            template
        )

        experiment = document.setdefault(
            "experiment",
            {},
        )

        experiment["id"] = (
            f"hpc-{args.profile}-"
            f"{args.mode}-"
            f"w{index:04d}"
        )

        experiment[
            "replicate_id"
        ] = index

        source = document["source"]

        source["output_bits"] = (
            args.output_bits
        )

        #
        # Scaling benchmark is intentionally RAW.
        # Conditioning has its own performance evidence.
        #
        conditioning = document.setdefault(
            "conditioning",
            {},
        )

        conditioning["mode"] = "raw"

        path = (
            output_dir
            / f"workload_{index:04d}.yaml"
        )

        path.write_text(
            yaml.safe_dump(
                document,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        rows.append(
            {
                "workload_index":
                    index,
                "profile":
                    args.profile,
                "mode":
                    args.mode,
                "output_bits":
                    args.output_bits,
                "config":
                    str(
                        path.relative_to(
                            ROOT
                        )
                    ),
                "config_sha256":
                    sha256(path),
            }
        )

    MANIFEST_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = (
        MANIFEST_ROOT
        / (
            f"{args.profile}_"
            f"{args.mode}.tsv"
        )
    )

    columns = list(
        rows[0].keys()
    )

    with manifest.open(
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

    print(
        "profile     :",
        args.profile,
    )
    print(
        "mode        :",
        args.mode,
    )
    print(
        "items       :",
        args.items,
    )
    print(
        "output bits :",
        args.output_bits,
    )
    print(
        "manifest    :",
        manifest.relative_to(ROOT),
    )
    print()
    print(
        "PASSED: frozen scaling workload prepared"
    )


if __name__ == "__main__":
    main()
