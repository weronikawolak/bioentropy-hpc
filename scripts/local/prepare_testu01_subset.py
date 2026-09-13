#!/usr/bin/env python3

from pathlib import Path
import hashlib
import json

import yaml


ROOT = Path(__file__).resolve().parents[2]

CONFIG_ROOT = ROOT / "configs"
OUTPUT_DIR = CONFIG_ROOT / "testu01"

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
        "label": "logistic-float32",
        "type": "logistic",
        "tokens": ["float32"],
    },
    {
        "label": "logistic-float64",
        "type": "logistic",
        "tokens": ["float64"],
    },
    {
        "label": "logistic-fixed_q3_29",
        "type": "logistic",
        "tokens": ["fixed_q3_29"],
    },
    {
        "label": "logistic-mpfr_256",
        "type": "logistic",
        "tokens": ["mpfr_256"],
    },
    {
        "label": "chen-4d-dcs",
        "type": "chen_4d_dcs",
        "tokens": [],
    },
    {
        "label": "rule30-cells256",
        "type": "cellular_automaton",
        "tokens": ["30", "256"],
    },
    {
        "label": "rule30-cells1024",
        "type": "cellular_automaton",
        "tokens": ["30", "1024"],
    },
    {
        "label": "rule90-cells256",
        "type": "cellular_automaton",
        "tokens": ["90", "256"],
    },
    {
        "label": "rule90-cells1024",
        "type": "cellular_automaton",
        "tokens": ["90", "1024"],
    },
    {
        "label": "chacha20",
        "type": "chacha20_reference",
        "tokens": [],
    },
    {
        "label": "ctr-drbg-aes256",
        "type": "ctr_drbg_aes256_reference",
        "tokens": [],
    },
]


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def flatten_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from flatten_values(item)

    elif isinstance(value, list):
        for item in value:
            yield from flatten_values(item)

    else:
        yield str(value).lower()


def load_yaml(path):
    try:
        value = yaml.safe_load(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None

    if not isinstance(value, dict):
        return None

    return value


def source_type(doc):
    source = doc.get("source")

    if not isinstance(source, dict):
        return None

    return source.get("type")


def candidate_matches(
    path,
    document,
    definition,
):
    if (
        source_type(document)
        != definition["type"]
    ):
        return False

    haystack = " ".join(
        flatten_values(
            document.get(
                "source",
                {},
            )
        )
    )

    return all(
        token.lower() in haystack
        for token
        in definition["tokens"]
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidates = []

    for path in sorted(
        CONFIG_ROOT.rglob("*.yaml")
    ):
        if OUTPUT_DIR in path.parents:
            continue

        lower = str(path).lower()

        if "testu01" in lower:
            continue

        document = load_yaml(path)

        if document is None:
            continue

        candidates.append(
            (path, document)
        )

    rows = []

    for definition in SOURCES:
        matches = [
            (path, doc)
            for path, doc
            in candidates
            if candidate_matches(
                path,
                doc,
                definition,
            )
        ]

        if not matches:
            raise RuntimeError(
                "No configuration candidate for "
                + definition["label"]
            )

        #
        # Frozen deterministic selection rule:
        # lexicographically first matching existing config.
        #
        matches.sort(
            key=lambda x: str(x[0])
        )

        template, document = matches[0]

        document = json.loads(
            json.dumps(document)
        )

        experiment = document.setdefault(
            "experiment",
            {},
        )

        experiment["id"] = (
            "testu01-smallcrush-"
            + definition["label"]
        )

        experiment["replicate_id"] = 0

        experiment["master_seed"] = (
            MASTER_SEED
        )

        source = document["source"]

        #
        # SmallCrush controls consumption itself.
        # This field only needs to remain a valid
        # experiment configuration.
        #
        source["output_bits"] = 1048576

        output = (
            OUTPUT_DIR
            / (
                definition["label"]
                + ".yaml"
            )
        )

        output.write_text(
            yaml.safe_dump(
                document,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        rows.append(
            {
                "label":
                    definition["label"],
                "source_type":
                    definition["type"],
                "replicate_id":
                    0,
                "master_seed":
                    MASTER_SEED,
                "template":
                    str(
                        template.relative_to(
                            ROOT
                        )
                    ),
                "config":
                    str(
                        output.relative_to(
                            ROOT
                        )
                    ),
                "config_sha256":
                    sha256(output),
            }
        )

        print()
        print(
            definition["label"]
        )
        print(
            "  template:",
            template.relative_to(ROOT),
        )
        print(
            "  frozen  :",
            output.relative_to(ROOT),
        )

        if len(matches) > 1:
            print(
                "  candidates:",
                len(matches),
                "(lexicographically first frozen)",
            )

    columns = [
        "label",
        "source_type",
        "replicate_id",
        "master_seed",
        "template",
        "config",
        "config_sha256",
    ]

    with MANIFEST.open(
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "\t".join(columns)
            + "\n"
        )

        for row in rows:
            handle.write(
                "\t".join(
                    str(row[column])
                    for column in columns
                )
                + "\n"
            )

    print()
    print(
        "PASSED: frozen TestU01 subset prepared"
    )
    print(
        "sources:",
        len(rows),
    )
    print(
        "manifest:",
        MANIFEST.relative_to(ROOT),
    )


if __name__ == "__main__":
    main()
