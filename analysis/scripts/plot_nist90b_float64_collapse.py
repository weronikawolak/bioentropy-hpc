#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Plot windowed NIST SP 800-90B "
            "float64 logistic-map entropy "
            "aligned to exact collapse points."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=(
            ROOT
            / "results"
            / "aggregated"
            / "nist90b_logistic-float64_"
            "collapsed_windows.tsv"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            ROOT
            / "results"
            / "figures"
        ),
    )

    parser.add_argument(
        "--focus-mbit",
        type=float,
        default=2.6,
        help=(
            "Show windows whose midpoint is "
            "within this many Mbit of collapse."
        ),
    )

    args = parser.parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(
            args.input
        )

    with args.input.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    grouped = defaultdict(list)

    for row in rows:
        x = float(
            row[
                "relative_midpoint_mbit"
            ]
        )

        if abs(x) > args.focus_mbit:
            continue

        grouped[
            row["replicate_id"]
        ].append(
            {
                "x": x,
                "h": float(
                    row["h_original"]
                ),
                "status": row[
                    "assessment_status"
                ],
                "phase": row["phase"],
            }
        )

    if len(grouped) != 5:
        raise RuntimeError(
            f"Expected 5 replicates; "
            f"got {len(grouped)}."
        )

    fig, ax = plt.subplots(
        figsize=(9.0, 5.6)
    )

    for replicate in sorted(
        grouped,
        key=int,
    ):
        points = sorted(
            grouped[replicate],
            key=lambda p: p["x"],
        )

        xs = [
            p["x"]
            for p in points
        ]

        ys = [
            p["h"]
            for p in points
        ]

        line, = ax.plot(
            xs,
            ys,
            marker="o",
            linewidth=1.7,
            label=f"rep{int(replicate):03d}",
        )

        line_color = (
            line.get_color()
        )

        constant_x = [
            p["x"]
            for p in points
            if p["status"]
            == "degenerate_constant"
        ]

        constant_y = [
            p["h"]
            for p in points
            if p["status"]
            == "degenerate_constant"
        ]

        if constant_x:
            ax.scatter(
                constant_x,
                constant_y,
                marker="x",
                s=70,
                linewidths=1.8,
                color=line_color,
            )

    ax.axvline(
        0.0,
        linestyle="--",
        linewidth=1.3,
    )

    ax.set_xlabel(
        "Window midpoint relative to exact collapse (Mbit)"
    )

    ax.set_ylabel(
        "NIST SP 800-90B H_original (bits/bit)"
    )

    ax.set_title(
        "Float64 logistic-map min-entropy "
        "around finite-precision collapse"
    )

    ax.set_ylim(
        -0.03,
        0.95,
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        title="Frozen replicate",
        frameon=False,
    )

    fig.tight_layout()

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    png = (
        args.output_dir
        / "nist90b_float64_collapse_aligned.png"
    )

    pdf = (
        args.output_dir
        / "nist90b_float64_collapse_aligned.pdf"
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
