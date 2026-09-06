#!/usr/bin/env python3

import argparse
import shutil
from pathlib import Path


BLOCK = (
    "conditioning:\n"
    "  mode: ascon_xof128\n\n"
)


def transform(text: str) -> str:
    raw_block = (
        "conditioning:\n"
        "  mode: raw\n"
    )

    ascon_block = (
        "conditioning:\n"
        "  mode: ascon_xof128\n"
    )

    if raw_block not in text:
        raise ValueError(
            "Expected conditioning mode raw "
            "was not found"
        )

    if text.count(raw_block) != 1:
        raise ValueError(
            "Expected exactly one raw "
            "conditioning block"
        )

    return text.replace(
        raw_block,
        ascon_block,
        1,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--replicates",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    configs = sorted(
        args.input_dir.glob("*/rep*.yaml")
    )

    if args.replicates is not None:
        configs = [
            p for p in configs
            if int(p.stem.removeprefix("rep"))
            < args.replicates
        ]

    rows = []

    for src in configs:
        relative = src.relative_to(
            args.input_dir
        )

        dst = args.output_dir / relative

        dst.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        raw = src.read_text()

        conditioned = transform(raw)

        dst.write_text(conditioned)

        rows.append(
            (
                relative.parent.name,
                relative.stem,
                str(src),
                str(dst),
            )
        )

    manifest = (
        args.output_dir
        / "manifest.tsv"
    )

    with manifest.open("w") as f:
        f.write(
            "group\treplicate\t"
            "raw_config\tascon_config\n"
        )

        for row in rows:
            f.write(
                "\t".join(row)
                + "\n"
            )

    print(
        "Generated configs:",
        len(rows),
    )

    print(
        "Output:",
        args.output_dir,
    )

    print(
        "Manifest:",
        manifest,
    )


if __name__ == "__main__":
    main()
