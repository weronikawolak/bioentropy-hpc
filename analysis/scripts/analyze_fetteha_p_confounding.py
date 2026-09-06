#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


WIDTH = 256
HEIGHT = 256
PIXELS = WIDTH * HEIGHT
TRIALS = 50

DOMAIN = "BIOENTROPY-FETTEHA-P-CONFOUNDING-v1"


def deterministic_image(
    raw_p: int,
) -> bytearray:
    stream = bytearray()

    counter = 0

    while len(stream) < PIXELS:
        block = hashlib.sha256(
            f"{DOMAIN}:{raw_p}:{counter}".encode()
        ).digest()

        stream.extend(block)
        counter += 1

    image = stream[:PIXELS]

    current_p = sum(image) % 16

    delta = (
        raw_p - current_p
    ) % 16

    # Adjust one byte without overflow.
    if image[0] <= 255 - delta:
        image[0] += delta
    else:
        image[0] -= 16 - delta

    assert sum(image) % 16 == raw_p

    return image


def effective_p(raw_p: int) -> int:
    return 16 if raw_p == 0 else raw_p


def main() -> None:
    rows = []

    for raw_p in range(16):
        image = deterministic_image(raw_p)

        fixture_dir = Path(
            "results/generated/"
            "fetteha_p_fixtures"
        )

        fixture_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        fixture_path = (
            fixture_dir
            / f"p_{raw_p:02d}.bin"
        )

        fixture_path.write_bytes(image)

        rows.append(
            {
                "raw_p": raw_p,
                "effective_p": effective_p(raw_p),
                "pixel_sum_mod16": sum(image) % 16,
                "sha256": hashlib.sha256(image).hexdigest(),
                "fixture": str(fixture_path),
            }
        )

    frame = pd.DataFrame(rows)

    output = Path(
        "results/aggregated/"
        "fetteha_p_fixture_manifest.tsv"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output,
        sep="\t",
        index=False,
    )

    print()
    print("Fetteha P-control fixture manifest")
    print("=" * 90)
    print(frame.to_string(index=False))
    print()
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
