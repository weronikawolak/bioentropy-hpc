#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path


CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def unpack_msb_first(data: bytes, limit: int | None = None) -> bytes:
    output = bytearray()

    for byte in data:
        for shift in range(7, -1, -1):
            output.append((byte >> shift) & 1)

            if limit is not None and len(output) >= limit:
                return bytes(output)

    return bytes(output)


def run_self_test() -> None:
    packed = bytes([0xA2, 0x01])

    expected = bytes([
        1, 0, 1, 0, 0, 0, 1, 0,
        0, 0, 0, 0, 0, 0, 0, 1,
    ])

    actual = unpack_msb_first(packed)

    if actual != expected:
        raise RuntimeError(
            f"MSB-first self-test failed: {list(actual)}"
        )

    truncated = unpack_msb_first(packed, 10)

    if truncated != expected[:10]:
        raise RuntimeError(
            "max-samples self-test failed"
        )

    print("PASSED: MSB-first bit unpacking self-test")


def convert(
    input_path: Path,
    output_path: Path,
    max_samples: int | None,
) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must differ.")

    total_input_bytes = input_path.stat().st_size
    total_available_samples = total_input_bytes * 8

    if max_samples is not None and max_samples <= 0:
        raise ValueError("--max-samples must be positive.")

    target_samples = total_available_samples

    if max_samples is not None:
        target_samples = min(
            target_samples,
            max_samples,
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_sha = hashlib.sha256()
    zeros = 0
    ones = 0
    samples = 0

    with input_path.open("rb") as src, \
            output_path.open("wb") as dst:

        while samples < target_samples:
            remaining_samples = (
                target_samples - samples
            )

            bytes_needed = (
                remaining_samples + 7
            ) // 8

            chunk = src.read(
                min(CHUNK_SIZE, bytes_needed)
            )

            if not chunk:
                break

            expanded = unpack_msb_first(
                chunk,
                remaining_samples,
            )

            dst.write(expanded)
            output_sha.update(expanded)

            ones += sum(expanded)
            zeros += len(expanded) - sum(expanded)
            samples += len(expanded)

    if samples != target_samples:
        raise RuntimeError(
            f"Expected {target_samples} samples, "
            f"wrote {samples}."
        )

    metadata = {
        "format": "nist-sp800-90b-binary-samples",
        "bits_per_symbol": 1,
        "source_bit_order": "msb-first",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_bytes": total_input_bytes,
        "available_input_bits": total_available_samples,
        "output_samples": samples,
        "max_samples": max_samples,
        "truncated": samples < total_available_samples,
        "zeros": zeros,
        "ones": ones,
        "p1": ones / samples if samples else None,
        "input_sha256": sha256_file(input_path),
        "output_sha256": output_sha.hexdigest(),
    }

    metadata_path = output_path.with_suffix(
        output_path.suffix + ".json"
    )

    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            metadata,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert MSB-first packed bioentropy bitstreams "
            "to one-byte binary samples for NIST SP 800-90B."
        )
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    if args.input is None or args.output is None:
        parser.error(
            "input and output are required "
            "unless --self-test is used"
        )

    metadata = convert(
        args.input,
        args.output,
        args.max_samples,
    )

    print(
        f"Samples : {metadata['output_samples']}"
    )
    print(
        f"Zeros   : {metadata['zeros']}"
    )
    print(
        f"Ones    : {metadata['ones']}"
    )
    print(
        f"P(1)    : {metadata['p1']:.12f}"
    )
    print(
        f"Input SHA256 : {metadata['input_sha256']}"
    )
    print(
        f"Output SHA256: {metadata['output_sha256']}"
    )


if __name__ == "__main__":
    main()
