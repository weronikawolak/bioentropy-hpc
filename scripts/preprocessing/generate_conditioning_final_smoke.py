#!/usr/bin/env python3

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SOURCES = {
    "logistic": (
        ROOT
        / "configs/generated/screening/logistic/"
          "logistic-r099_rep0000.yaml"
    ),
    "rule30": (
        ROOT
        / "configs/campaigns/ca_rule30_smoke.yaml"
    ),
    "rule90": (
        ROOT
        / "configs/campaigns/ca_rule90_smoke.yaml"
    ),
    "dna": (
        ROOT
        / "configs/campaigns/dna/reference/"
          "dna-ecoli_k12-w01.yaml"
    ),
    "chacha20": (
        ROOT
        / "configs/campaigns/"
          "chacha20_reference_smoke.yaml"
    ),
}

OUTPUT_DIR = (
    ROOT
    / "configs/generated/"
      "conditioning-final-smoke"
)


def replace_experiment_id(
    text: str,
    new_id: str,
) -> str:
    lines = text.splitlines()

    in_experiment = False
    replaced = False

    for index, line in enumerate(lines):
        if line == "experiment:":
            in_experiment = True
            continue

        if (
            in_experiment
            and line
            and not line.startswith(" ")
        ):
            in_experiment = False

        if (
            in_experiment
            and line.startswith("  id:")
        ):
            lines[index] = (
                f"  id: {new_id}"
            )
            replaced = True
            break

    if not replaced:
        raise RuntimeError(
            "experiment.id not found"
        )

    return "\n".join(lines) + "\n"


def replace_conditioning(
    text: str,
    mode: str,
) -> str:
    lines = text.splitlines()

    cleaned = []

    index = 0

    while index < len(lines):
        line = lines[index]

        if line == "conditioning:":
            index += 1

            while (
                index < len(lines)
                and (
                    not lines[index]
                    or lines[index].startswith(" ")
                )
            ):
                index += 1

            continue

        cleaned.append(line)
        index += 1

    block = [
        "conditioning:",
        f"  mode: {mode}",
        "",
    ]

    insertion_index = None

    for index, line in enumerate(cleaned):
        if line == "execution:":
            insertion_index = index
            break

    if insertion_index is None:
        if (
            cleaned
            and cleaned[-1] != ""
        ):
            cleaned.append("")

        cleaned.extend(block)
    else:
        cleaned[
            insertion_index:insertion_index
        ] = block

    return "\n".join(cleaned).rstrip() + "\n"


def top_level_block(
    text: str,
    name: str,
) -> str:
    lines = text.splitlines()

    marker = f"{name}:"

    try:
        start = lines.index(marker)
    except ValueError as exc:
        raise RuntimeError(
            f"{marker} not found"
        ) from exc

    result = [lines[start]]

    for line in lines[start + 1:]:
        if (
            line
            and not line.startswith(" ")
        ):
            break

        result.append(line)

    return "\n".join(result).rstrip()


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_rows = [
        "pair_id\tsource\tmode\t"
        "base_config\tgenerated_config"
    ]

    for source_name, base_path in SOURCES.items():
        if not base_path.exists():
            raise FileNotFoundError(
                base_path
            )

        original = base_path.read_text()

        generated = {}

        for mode in [
            "raw",
            "ascon_xof128",
        ]:
            suffix = (
                "raw"
                if mode == "raw"
                else "ascon"
            )

            experiment_id = (
                "conditioning-final-smoke-"
                f"{source_name}"
            )

            text = replace_experiment_id(
                original,
                experiment_id,
            )

            text = replace_conditioning(
                text,
                mode,
            )

            output_path = (
                OUTPUT_DIR
                / f"{source_name}-{suffix}.yaml"
            )

            output_path.write_text(text)

            generated[mode] = text

            manifest_rows.append(
                "\t".join(
                    [
                        source_name,
                        source_name,
                        mode,
                        str(
                            base_path.relative_to(
                                ROOT
                            )
                        ),
                        str(
                            output_path.relative_to(
                                ROOT
                            )
                        ),
                    ]
                )
            )

        # RAW and XOF MUST receive the
        # exact same source configuration.
        raw_source = top_level_block(
            generated["raw"],
            "source",
        )

        xof_source = top_level_block(
            generated["ascon_xof128"],
            "source",
        )

        if raw_source != xof_source:
            raise RuntimeError(
                "RAW/XOF source mismatch: "
                + source_name
            )

        print(
            f"{source_name}: "
            "paired source config OK"
        )

    manifest = (
        OUTPUT_DIR
        / "manifest.tsv"
    )

    manifest.write_text(
        "\n".join(manifest_rows)
        + "\n"
    )

    print()
    print(
        "Generated conditioning smoke:"
    )
    print(OUTPUT_DIR)
    print()
    print("Pairs: 5")
    print("Executions: 10")


if __name__ == "__main__":
    main()
