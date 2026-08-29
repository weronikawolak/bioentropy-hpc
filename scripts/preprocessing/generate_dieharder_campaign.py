#!/usr/bin/env python3

from pathlib import Path
import argparse
import copy
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[2]

MASTER_SEED = (
    "0123456789abcdef0123456789abcdef"
    "0123456789abcdef0123456789abcdef"
)

OUTPUT_BITS = 16 * 1024 * 1024 * 8


def load_config(relative):
    path = ROOT / relative

    if not path.exists():
        raise SystemExit(f"Missing base config: {path}")

    return yaml.safe_load(path.read_text())


def derive_value(domain, replicate, coordinate=0):
    payload = (
        f"{MASTER_SEED}|{domain}|"
        f"{replicate}|{coordinate}"
    ).encode()

    digest = hashlib.sha256(payload).digest()

    integer = int.from_bytes(
        digest[:8],
        "big",
    )

    return (
        integer + 0.5
    ) / float(1 << 64)


def literal(value):
    return format(value, ".17g")


def prepare(base, group, replicate):
    document = copy.deepcopy(base)

    document["experiment"]["id"] = (
        f"dieharder-{group}"
    )

    document["experiment"]["replicate_id"] = (
        replicate
    )

    document["experiment"]["master_seed"] = (
        MASTER_SEED
    )

    document["source"]["output_bits"] = (
        OUTPUT_BITS
    )

    document["conditioning"] = {
        "mode": "raw"
    }

    document["execution"] = {
        "chunk_bytes": 65536
    }

    return document


def save(document, output_dir, group, replicate):
    path = (
        output_dir
        / group
        / f"rep{replicate:03d}.yaml"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        yaml.safe_dump(
            document,
            sort_keys=False,
        )
    )

    return path


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--replicates",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    output_dir = args.output_dir

    logistic_base = load_config(
        "configs/generated/logistic-precision-smoke/"
        "logistic-float64.yaml"
    )

    chen_base = load_config(
        "configs/generated/chen-4d-dcs-smoke/"
        "chen-4d-dcs-raw.yaml"
    )

    rule30_base = load_config(
        "configs/generated/conditioning-final-smoke/"
        "rule30-raw.yaml"
    )

    rule90_base = load_config(
        "configs/generated/conditioning-final-smoke/"
        "rule90-raw.yaml"
    )

    chacha_base = load_config(
        "configs/generated/conditioning-final-smoke/"
        "chacha20-raw.yaml"
    )

    rows = []

    logistic_modes = (
        "float32",
        "float64",
        "fixed_q3_29",
        "mpfr_256",
    )

    for replicate in range(args.replicates):
        x0 = literal(
            derive_value(
                "logistic-x0",
                replicate,
            )
        )

        for mode in logistic_modes:
            group = f"logistic-{mode}"

            document = prepare(
                logistic_base,
                group,
                replicate,
            )

            parameters = (
                document["source"]["parameters"]
            )

            parameters["arithmetic"] = {
                "mode": mode,
            }

            parameters["initial_state"] = {
                "mode": "explicit",
                "x0": x0,
            }

            path = save(
                document,
                output_dir,
                group,
                replicate,
            )

            rows.append({
                "group": group,
                "replicate_id": replicate,
                "config": str(path),
                "logistic_x0": x0,
                "chen_x0": "",
                "chen_y0": "",
                "chen_z0": "",
                "chen_w0": "",
            })

        state = [
            literal(
                derive_value(
                    "chen-state",
                    replicate,
                    coordinate,
                )
            )
            for coordinate in range(4)
        ]

        group = "chen-4d-dcs"

        document = prepare(
            chen_base,
            group,
            replicate,
        )

        document["source"]["parameters"][
            "initial_state"
        ] = {
            "x0": state[0],
            "y0": state[1],
            "z0": state[2],
            "w0": state[3],
        }

        path = save(
            document,
            output_dir,
            group,
            replicate,
        )

        rows.append({
            "group": group,
            "replicate_id": replicate,
            "config": str(path),
            "logistic_x0": "",
            "chen_x0": state[0],
            "chen_y0": state[1],
            "chen_z0": state[2],
            "chen_w0": state[3],
        })

        for name, base in (
            ("rule30", rule30_base),
            ("rule90", rule90_base),
        ):
            for cells in (256, 1024):
                group = f"{name}-cells{cells}"

                document = prepare(
                    base,
                    group,
                    replicate,
                )

                document["source"]["parameters"][
                    "cells"
                ] = cells

                path = save(
                    document,
                    output_dir,
                    group,
                    replicate,
                )

                rows.append({
                    "group": group,
                    "replicate_id": replicate,
                    "config": str(path),
                    "logistic_x0": "",
                    "chen_x0": "",
                    "chen_y0": "",
                    "chen_z0": "",
                    "chen_w0": "",
                })

        group = "chacha20"

        document = prepare(
            chacha_base,
            group,
            replicate,
        )

        path = save(
            document,
            output_dir,
            group,
            replicate,
        )

        rows.append({
            "group": group,
            "replicate_id": replicate,
            "config": str(path),
            "logistic_x0": "",
            "chen_x0": "",
            "chen_y0": "",
            "chen_z0": "",
            "chen_w0": "",
        })

    columns = (
        "group",
        "replicate_id",
        "config",
        "logistic_x0",
        "chen_x0",
        "chen_y0",
        "chen_z0",
        "chen_w0",
    )

    manifest = output_dir / "manifest.tsv"

    manifest.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with manifest.open("w") as handle:
        handle.write(
            "\t".join(columns) + "\n"
        )

        for row in rows:
            handle.write(
                "\t".join(
                    str(row[column])
                    for column in columns
                )
                + "\n"
            )

    expected = args.replicates * 10

    if len(rows) != expected:
        raise RuntimeError(
            f"Expected {expected} configs, "
            f"generated {len(rows)}"
        )

    print("Campaign generated successfully.")
    print("Replicates:", args.replicates)
    print("Groups    : 10")
    print("Configs   :", len(rows))
    print("Manifest  :", manifest)


if __name__ == "__main__":
    main()
