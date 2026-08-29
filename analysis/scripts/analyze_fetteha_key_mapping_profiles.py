#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import math
import statistics
from pathlib import Path

import pandas as pd


NUM_KEYS = 1000
DISCARD = 200
USABLE_STEPS = 1024
MAX_ABS_LIMIT = 1.0e6

H = 1.0 / 128.0
SIGMA = 8.0
RHO = 16.0
BETA = 2.0

DOMAIN = "BIOENTROPY-FETTEHA-KEYMAP-SENSITIVITY-v1"


def deterministic_key(index: int) -> bytes:
    payload = f"{DOMAIN}:{index}".encode()
    return hashlib.sha256(payload).digest()


def split_key_big_endian(key: bytes) -> list[int]:
    assert len(key) == 32

    return [
        int.from_bytes(
            key[i:i + 4],
            byteorder="big",
            signed=False,
        )
        for i in range(0, 32, 4)
    ]


def derive_raw_conditions(
    words: list[int],
) -> tuple[int, int, int]:
    x0 = (
        words[0]
        ^ words[1]
        ^ words[2]
        ^ words[3]
    )

    y0 = (
        words[2]
        ^ words[3]
        ^ words[4]
        ^ words[5]
    )

    z0 = (
        words[4]
        ^ words[5]
        ^ words[6]
        ^ words[7]
    )

    return x0, y0, z0


def signed32(value: int) -> int:
    if value >= (1 << 31):
        return value - (1 << 32)

    return value


def map_profile(
    name: str,
    value: int,
) -> float:
    if name == "u32_unit":
        return value / float(1 << 32)

    if name == "u32_q28":
        return value / float(1 << 28)

    if name == "s32_q28":
        return signed32(value) / float(1 << 28)

    if name == "s32_q27":
        return signed32(value) / float(1 << 27)

    if name == "s32_q26":
        return signed32(value) / float(1 << 26)

    if name == "s32_q24":
        return signed32(value) / float(1 << 24)

    if name == "s32_q16":
        return signed32(value) / float(1 << 16)

    raise ValueError(name)


PROFILES = [
    "u32_unit",
    "u32_q28",
    "s32_q28",
    "s32_q27",
    "s32_q26",
    "s32_q24",
    "s32_q16",
]


def lorenz_step(
    state: tuple[float, float, float],
) -> tuple[float, float, float]:
    x, y, z = state

    next_x = (
        x
        + H * SIGMA * (y - x)
    )

    next_y = (
        y
        + H
        * (
            RHO * x
            - y
            - x * z
        )
    )

    next_z = (
        z
        + H
        * (
            x * y
            - BETA * z
        )
    )

    return next_x, next_y, next_z


def simulate(
    state: tuple[float, float, float],
) -> tuple[bool, float]:
    max_abs = max(
        abs(value)
        for value in state
    )

    total_steps = (
        DISCARD
        + USABLE_STEPS
    )

    for _ in range(total_steps):
        state = lorenz_step(state)

        if not all(
            math.isfinite(value)
            for value in state
        ):
            return False, math.inf

        step_max = max(
            abs(value)
            for value in state
        )

        max_abs = max(
            max_abs,
            step_max,
        )

        if max_abs > MAX_ABS_LIMIT:
            return False, max_abs

    return True, max_abs


def main() -> None:
    raw_conditions = []

    for index in range(NUM_KEYS):
        key = deterministic_key(index)
        words = split_key_big_endian(key)

        raw_conditions.append(
            derive_raw_conditions(words)
        )

    rows = []

    for profile in PROFILES:
        stable_max_abs = []
        initial_abs = []

        for raw in raw_conditions:
            state = tuple(
                map_profile(profile, value)
                for value in raw
            )

            initial_abs.append(
                max(
                    abs(value)
                    for value in state
                )
            )

            stable, max_abs = simulate(state)

            if stable:
                stable_max_abs.append(max_abs)

        stable_count = len(
            stable_max_abs
        )

        divergent_count = (
            NUM_KEYS
            - stable_count
        )

        rows.append(
            {
                "profile": profile,
                "keys": NUM_KEYS,
                "discard": DISCARD,
                "usable_steps": USABLE_STEPS,
                "stable_count": stable_count,
                "divergent_count": divergent_count,
                "stable_fraction": (
                    stable_count / NUM_KEYS
                ),
                "median_initial_max_abs": (
                    statistics.median(
                        initial_abs
                    )
                ),
                "median_trajectory_max_abs": (
                    statistics.median(
                        stable_max_abs
                    )
                    if stable_max_abs
                    else math.nan
                ),
                "max_trajectory_abs": (
                    max(stable_max_abs)
                    if stable_max_abs
                    else math.nan
                ),
            }
        )

    frame = pd.DataFrame(rows)

    output = Path(
        "results/aggregated/"
        "fetteha_key_mapping_sensitivity.tsv"
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
    print("Fetteha 2023 key-mapping sensitivity")
    print("=" * 78)
    print(frame.to_string(index=False))
    print()
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
