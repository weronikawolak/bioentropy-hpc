#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import shutil
from decimal import Decimal, getcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

OUTPUT_ROOT = (
    ROOT / "configs/generated/screening"
)

MANIFEST = (
    OUTPUT_ROOT / "manifest.tsv"
)

MASTER_SEED = (
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
    "0123456789abcdef"
)

OUTPUT_BITS = 1_000_000
CHUNK_BYTES = 65_536

LOGISTIC_R_COUNT = 100
LOGISTIC_REPLICATES = 20

LOGISTIC_R_MIN = Decimal("3.57")
LOGISTIC_R_MAX = Decimal("4.00")

LOGISTIC_BURN_IN = 1000

CA_RULES = (30, 90)
CA_WIDTHS = (256, 1024)
CA_REPLICATES = 20

CHACHA_REPLICATES = 20

LOGISTIC_X0_DOMAIN = (
    b"BIOENTROPY-HPC-LOGISTIC-X0-v1"
)

getcontext().prec = 50


def logistic_x0(
    replicate_id: int,
) -> float:
    material = (
        LOGISTIC_X0_DOMAIN
        + bytes.fromhex(MASTER_SEED)
        + replicate_id.to_bytes(
            4,
            byteorder="big",
            signed=False,
        )
    )

    digest = hashlib.sha256(
        material
    ).digest()

    value64 = int.from_bytes(
        digest[:8],
        byteorder="big",
    )

    value53 = value64 >> 11

    # Open interval (0, 1).
    return (
        value53 + 0.5
    ) / (2 ** 53)


def logistic_r_values():
    if LOGISTIC_R_COUNT == 1:
        return [LOGISTIC_R_MIN]

    step = (
        LOGISTIC_R_MAX
        - LOGISTIC_R_MIN
    ) / Decimal(
        LOGISTIC_R_COUNT - 1
    )

    return [
        LOGISTIC_R_MIN
        + Decimal(index) * step
        for index in range(
            LOGISTIC_R_COUNT
        )
    ]


def write_text(
    path: Path,
    text: str,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )


def logistic_config(
    experiment_id: str,
    replicate_id: int,
    r: Decimal,
    x0: float,
) -> str:
    return f'''experiment:
  id: "{experiment_id}"
  replicate_id: {replicate_id}
  master_seed: "{MASTER_SEED}"

source:
  type: "logistic"
  output_bits: {OUTPUT_BITS}

  parameters:
    r: {format(r, ".15f")}
    burn_in: {LOGISTIC_BURN_IN}
    extraction: "threshold"

    initial_state:
      mode: "explicit"
      x0: {format(x0, ".17g")}

execution:
  chunk_bytes: {CHUNK_BYTES}
'''


def ca_config(
    experiment_id: str,
    replicate_id: int,
    rule: int,
    cells: int,
) -> str:
    return f'''experiment:
  id: "{experiment_id}"
  replicate_id: {replicate_id}
  master_seed: "{MASTER_SEED}"

source:
  type: "cellular_automaton"
  output_bits: {OUTPUT_BITS}

  parameters:
    rule: {rule}
    cells: {cells}

execution:
  chunk_bytes: {CHUNK_BYTES}
'''


def chacha_config(
    experiment_id: str,
    replicate_id: int,
) -> str:
    return f'''experiment:
  id: "{experiment_id}"
  replicate_id: {replicate_id}
  master_seed: "{MASTER_SEED}"

source:
  type: "chacha20_reference"
  output_bits: {OUTPUT_BITS}

  parameters:
    initial_counter: 0

execution:
  chunk_bytes: {CHUNK_BYTES}
'''


def main():
    if OUTPUT_ROOT.exists():
        shutil.rmtree(
            OUTPUT_ROOT
        )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    # --------------------------------------------------
    # Logistic Map
    # --------------------------------------------------

    r_values = logistic_r_values()

    for r_index, r in enumerate(
        r_values
    ):
        experiment_id = (
            f"logistic-r{r_index:03d}"
        )

        for replicate_id in range(
            LOGISTIC_REPLICATES
        ):
            x0 = logistic_x0(
                replicate_id
            )

            relative_config = Path(
                "logistic"
            ) / (
                f"{experiment_id}_"
                f"rep{replicate_id:04d}.yaml"
            )

            config_path = (
                OUTPUT_ROOT
                / relative_config
            )

            write_text(
                config_path,
                logistic_config(
                    experiment_id,
                    replicate_id,
                    r,
                    x0,
                ),
            )

            rows.append(
                {
                    "source":
                        "logistic",

                    "experiment_id":
                        experiment_id,

                    "replicate_id":
                        replicate_id,

                    "output_bits":
                        OUTPUT_BITS,

                    "r":
                        format(
                            r,
                            ".15f",
                        ),

                    "x0":
                        format(
                            x0,
                            ".17g",
                        ),

                    "burn_in":
                        LOGISTIC_BURN_IN,

                    "rule":
                        "",

                    "cells":
                        "",

                    "initial_counter":
                        "",

                    "config_file":
                        str(
                            config_path.relative_to(
                                ROOT
                            )
                        ),
                }
            )

    # --------------------------------------------------
    # Cellular Automata
    # --------------------------------------------------

    for rule in CA_RULES:
        for cells in CA_WIDTHS:
            experiment_id = (
                f"ca-rule{rule}-"
                f"cells{cells}"
            )

            for replicate_id in range(
                CA_REPLICATES
            ):
                relative_config = Path(
                    "cellular"
                ) / (
                    f"{experiment_id}_"
                    f"rep{replicate_id:04d}.yaml"
                )

                config_path = (
                    OUTPUT_ROOT
                    / relative_config
                )

                write_text(
                    config_path,
                    ca_config(
                        experiment_id,
                        replicate_id,
                        rule,
                        cells,
                    ),
                )

                rows.append(
                    {
                        "source":
                            "cellular_automaton",

                        "experiment_id":
                            experiment_id,

                        "replicate_id":
                            replicate_id,

                        "output_bits":
                            OUTPUT_BITS,

                        "r":
                            "",

                        "x0":
                            "",

                        "burn_in":
                            "",

                        "rule":
                            rule,

                        "cells":
                            cells,

                        "initial_counter":
                            "",

                        "config_file":
                            str(
                                config_path.relative_to(
                                    ROOT
                                )
                            ),
                    }
                )

    # --------------------------------------------------
    # ChaCha20 reference
    # --------------------------------------------------

    experiment_id = (
        "chacha20-reference-screening"
    )

    for replicate_id in range(
        CHACHA_REPLICATES
    ):
        relative_config = Path(
            "chacha20"
        ) / (
            f"{experiment_id}_"
            f"rep{replicate_id:04d}.yaml"
        )

        config_path = (
            OUTPUT_ROOT
            / relative_config
        )

        write_text(
            config_path,
            chacha_config(
                experiment_id,
                replicate_id,
            ),
        )

        rows.append(
            {
                "source":
                    "chacha20_reference",

                "experiment_id":
                    experiment_id,

                "replicate_id":
                    replicate_id,

                "output_bits":
                    OUTPUT_BITS,

                "r":
                    "",

                "x0":
                    "",

                "burn_in":
                    "",

                "rule":
                    "",

                "cells":
                    "",

                "initial_counter":
                    0,

                "config_file":
                    str(
                        config_path.relative_to(
                            ROOT
                        )
                    ),
            }
        )

    fields = [
        "source",
        "experiment_id",
        "replicate_id",
        "output_bits",
        "r",
        "x0",
        "burn_in",
        "rule",
        "cells",
        "initial_counter",
        "config_file",
    ]

    with MANIFEST.open(
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
        writer.writerows(rows)

    expected = (
        LOGISTIC_R_COUNT
        * LOGISTIC_REPLICATES
        +
        len(CA_RULES)
        * len(CA_WIDTHS)
        * CA_REPLICATES
        +
        CHACHA_REPLICATES
    )

    assert len(rows) == expected

    print(
        "Screening campaign generated."
    )

    print(
        f"Logistic : "
        f"{LOGISTIC_R_COUNT * LOGISTIC_REPLICATES}"
    )

    print(
        "CA       : "
        f"{len(CA_RULES) * len(CA_WIDTHS) * CA_REPLICATES}"
    )

    print(
        f"ChaCha20 : {CHACHA_REPLICATES}"
    )

    print(
        f"Total    : {len(rows)}"
    )

    print(
        "Manifest : "
        f"{MANIFEST.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
