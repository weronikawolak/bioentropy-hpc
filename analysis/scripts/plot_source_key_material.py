#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "source_key_material_summary.tsv"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
)


def main():
    with INPUT.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    raw = {
        row["source"]: row
        for row in rows
        if row["mode"] == "raw"
    }

    conditioned = {
        row["source"]: row
        for row in rows
        if row["mode"]
        == "ascon_xof128"
    }

    sources = sorted(raw)

    x = list(
        range(len(sources))
    )

    width = 0.36

    raw_values = [
        int(
            raw[source][
                "material_collisions"
            ]
        )
        for source in sources
    ]

    conditioned_values = [
        int(
            conditioned[source][
                "material_collisions"
            ]
        )
        for source in sources
    ]

    fig, ax = plt.subplots(
        figsize=(11, 5.8)
    )

    ax.bar(
        [
            value - width / 2
            for value in x
        ],
        raw_values,
        width,
        label="RAW",
    )

    ax.bar(
        [
            value + width / 2
            for value in x
        ],
        conditioned_values,
        width,
        label="Ascon-XOF128",
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        sources,
        rotation=38,
        ha="right",
    )

    ax.set_ylabel(
        "Duplicate realizations "
        "among 20 prefixes"
    )

    ax.set_xlabel(
        "Frozen source group"
    )

    ax.set_title(
        "Source-derived 76-byte "
        "key-material collisions"
    )

    ax.set_ylim(
        0,
        20,
    )

    ax.legend()

    fig.tight_layout()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    png = (
        OUTPUT_DIR
        / "source_key_material_collisions.png"
    )

    pdf = (
        OUTPUT_DIR
        / "source_key_material_collisions.pdf"
    )

    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("PNG:", png)
    print("PDF:", pdf)


if __name__ == "__main__":
    main()
