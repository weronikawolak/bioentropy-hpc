#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


NUMBER_PATTERN = (
    r"[+-]?"
    r"(?:"
    r"\d+(?:\.\d*)?"
    r"|"
    r"\.\d+"
    r")"
    r"(?:[eE][+-]?\d+)?"
)

H_ORIGINAL_RE = re.compile(
    rf"^\s*H_original:\s*({NUMBER_PATTERN})\s*$",
    re.MULTILINE,
)


def parse_output(text: str) -> dict:
    match = H_ORIGINAL_RE.search(text)

    if match is None:
        raise ValueError(
            "Could not find H_original in NIST SP 800-90B output."
        )

    h_original = float(match.group(1))

    # Normalize IEEE-754 negative zero returned by ea_non_iid
    # for near-degenerate datasets. Preserve the raw NIST
    # output separately; normalized values are used in JSON/TSV.
    if h_original == 0.0:
        h_original = 0.0

    if not 0.0 <= h_original <= 1.0:
        raise ValueError(
            f"Unexpected binary H_original value: {h_original}"
        )

    return {
        "h_original": h_original,
        "bits_per_symbol": 1,
        "assessment": "initial_non_iid",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse NIST SP 800-90B ea_non_iid output "
            "and combine it with sample-adapter metadata."
        )
    )

    parser.add_argument(
        "--nist-output",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--sample-metadata",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--source",
        required=True,
    )

    parser.add_argument(
        "--replicate-id",
        required=True,
    )

    args = parser.parse_args()

    text = args.nist_output.read_text(
        encoding="utf-8",
    )

    parsed = parse_output(text)

    with args.sample_metadata.open(
        encoding="utf-8",
    ) as handle:
        sample_meta = json.load(handle)

    if sample_meta.get("bits_per_symbol") != 1:
        raise ValueError(
            "Expected binary NIST samples "
            "with bits_per_symbol=1."
        )

    result = {
        "source": args.source,
        "replicate_id": args.replicate_id,
        "assessment": parsed["assessment"],
        "h_original": parsed["h_original"],
        "bits_per_symbol": 1,
        "samples": sample_meta["output_samples"],
        "zeros": sample_meta["zeros"],
        "ones": sample_meta["ones"],
        "p1": sample_meta["p1"],
        "source_bit_order": sample_meta["source_bit_order"],
        "raw_input_sha256": sample_meta["input_sha256"],
        "nist_input_sha256": sample_meta["output_sha256"],
        "truncated": sample_meta["truncated"],
        "nist_output_file": str(args.nist_output),
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            result,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    print(
        f"Source       : {result['source']}"
    )
    print(
        f"Replicate    : {result['replicate_id']}"
    )
    print(
        f"Samples      : {result['samples']}"
    )
    print(
        f"P(1)         : {result['p1']:.12f}"
    )
    print(
        f"H_original   : {result['h_original']:.6f}"
    )
    print(
        f"RAW SHA256   : {result['raw_input_sha256']}"
    )
    print(
        f"NIST SHA256  : {result['nist_input_sha256']}"
    )


if __name__ == "__main__":
    main()
