#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNNER = ROOT / "build" / "bioentropy-runner"
ADAPTER = (
    ROOT / "scripts" / "preprocessing"
    / "prepare_nist90b_samples.py"
)
PARSER = (
    ROOT / "analysis" / "scripts"
    / "parse_nist90b.py"
)
EA_NON_IID = (
    ROOT / "external" / "nist-sp800-90b"
    / "cpp" / "ea_non_iid"
)

DEFAULT_CONFIG_ROOT = (
    ROOT / "configs" / "generated"
    / "dieharder-campaign"
)

DEFAULT_OUTPUT_ROOT = (
    ROOT / "results" / "external"
    / "nist90b-prefix1m"
)

DEFAULT_AGGREGATED = (
    ROOT / "results" / "aggregated"
    / "nist90b_prefix1m.tsv"
)

SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
REP_RE = re.compile(r"rep(\d+)\.yaml$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def collect_sha_values(obj) -> set[str]:
    values: set[str] = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            if (
                "sha" in key.lower()
                and isinstance(value, str)
                and SHA_RE.fullmatch(value)
            ):
                values.add(value.lower())

            values.update(
                collect_sha_values(value)
            )

    elif isinstance(obj, list):
        for value in obj:
            values.update(
                collect_sha_values(value)
            )

    return values


def expected_metadata(
    source: str,
    replicate: int,
) -> Path:
    return (
        ROOT
        / "results"
        / "metrics"
        / (
            f"dieharder-{source}"
            f"_rep{replicate:04d}.json"
        )
    )


def check_provenance(
    source: str,
    replicate: int,
    raw_path: Path,
) -> tuple[bool, str]:
    metadata_path = expected_metadata(
        source,
        replicate,
    )

    if not metadata_path.is_file():
        raise FileNotFoundError(
            f"Frozen RAW metadata missing: "
            f"{metadata_path}"
        )

    with metadata_path.open(
        encoding="utf-8",
    ) as handle:
        metadata = json.load(handle)

    expected_shas = collect_sha_values(
        metadata
    )

    if not expected_shas:
        raise RuntimeError(
            f"No SHA-256 value found in "
            f"{metadata_path}"
        )

    actual_sha = sha256_file(raw_path)

    return (
        actual_sha.lower() in expected_shas,
        actual_sha,
    )


def run_command(
    command: list[str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def discover_configs(
    config_root: Path,
    sources: set[str] | None,
    replicates: set[int] | None,
) -> list[tuple[str, int, Path]]:
    configs = []

    for path in sorted(
        config_root.glob("*/rep*.yaml")
    ):
        source = path.parent.name

        match = REP_RE.search(path.name)

        if match is None:
            continue

        replicate = int(match.group(1))

        if (
            sources is not None
            and source not in sources
        ):
            continue

        if (
            replicates is not None
            and replicate not in replicates
        ):
            continue

        configs.append(
            (source, replicate, path)
        )

    return configs


def run_one(
    source: str,
    replicate: int,
    config_path: Path,
    output_root: Path,
    samples: int,
) -> dict:
    print(
        f"\n=== {source} rep{replicate:03d} ===",
        flush=True,
    )

    result_dir = (
        output_root
        / source
        / f"rep{replicate:03d}"
    )

    result_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(
        prefix=(
            f"bioentropy-nist90b-"
            f"{source}-rep{replicate:03d}-"
        )
    ) as temp_name:
        temp = Path(temp_name)

        raw_path = temp / "raw.bin"
        sample_path = temp / "samples.bin"

        runner_result = run_command(
            [
                str(RUNNER),
                "--config",
                str(config_path.resolve()),
                "--dump-bitstream",
                str(raw_path),
            ],
            cwd=temp,
        )

        provenance_ok, raw_sha = (
            check_provenance(
                source,
                replicate,
                raw_path,
            )
        )

        if not provenance_ok:
            raise RuntimeError(
                f"RAW provenance mismatch for "
                f"{source} rep{replicate:03d}: "
                f"{raw_sha}"
            )

        print(
            f"RAW provenance: PASS "
            f"{raw_sha[:12]}..."
        )

        adapter_result = run_command(
            [
                sys.executable,
                str(ADAPTER),
                str(raw_path),
                str(sample_path),
                "--max-samples",
                str(samples),
            ]
        )

        nist_result = run_command(
            [
                str(EA_NON_IID),
                "-i",
                sample_path.name,
                "1",
            ],
            cwd=temp,
        )

        nist_txt = (
            result_dir / "ea_non_iid.txt"
        )

        nist_txt.write_text(
            nist_result.stdout,
            encoding="utf-8",
        )

        sample_metadata = (
            sample_path.with_suffix(
                sample_path.suffix + ".json"
            )
        )

        result_json = (
            result_dir / "result.json"
        )

        parser_result = run_command(
            [
                sys.executable,
                str(PARSER),
                "--nist-output",
                str(nist_txt),
                "--sample-metadata",
                str(sample_metadata),
                "--output",
                str(result_json),
                "--source",
                source,
                "--replicate-id",
                f"{replicate:03d}",
            ]
        )

        with result_json.open(
            encoding="utf-8",
        ) as handle:
            result = json.load(handle)

        result["provenance_ok"] = True
        result["config"] = str(
            config_path.relative_to(ROOT)
        )
        result["frozen_raw_metadata"] = str(
            expected_metadata(
                source,
                replicate,
            ).relative_to(ROOT)
        )

        with result_json.open(
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

        (
            result_dir / "runner.txt"
        ).write_text(
            runner_result.stdout,
            encoding="utf-8",
        )

        (
            result_dir / "adapter.txt"
        ).write_text(
            adapter_result.stdout,
            encoding="utf-8",
        )

        (
            result_dir / "parser.txt"
        ).write_text(
            parser_result.stdout,
            encoding="utf-8",
        )

        print(
            f"H_original: "
            f"{result['h_original']:.6f}"
        )

        return result


def write_aggregate(
    results: list[dict],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "source",
        "replicate_id",
        "assessment",
        "samples",
        "p1",
        "h_original",
        "provenance_ok",
        "raw_input_sha256",
        "nist_input_sha256",
        "truncated",
        "config",
        "frozen_raw_metadata",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()

        for result in results:
            writer.writerow(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run reproducible NIST SP 800-90B "
            "non-IID prefix screening on frozen "
            "BioEntropy source realizations."
        )
    )

    parser.add_argument(
        "--config-root",
        type=Path,
        default=DEFAULT_CONFIG_ROOT,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )

    parser.add_argument(
        "--aggregated",
        type=Path,
        default=DEFAULT_AGGREGATED,
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=1_000_000,
    )

    parser.add_argument(
        "--sources",
        nargs="+",
        default=None,
    )

    parser.add_argument(
        "--replicates",
        nargs="+",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    if args.samples < 1_000_000:
        parser.error(
            "--samples must be at least 1000000"
        )

    required = [
        RUNNER,
        ADAPTER,
        PARSER,
        EA_NON_IID,
    ]

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    sources = (
        set(args.sources)
        if args.sources
        else None
    )

    replicates = (
        set(args.replicates)
        if args.replicates
        else None
    )

    configs = discover_configs(
        args.config_root,
        sources,
        replicates,
    )

    if not configs:
        raise RuntimeError(
            "No matching frozen configs found."
        )

    print(
        f"Configurations: {len(configs)}"
    )
    print(
        f"Samples/config: {args.samples}"
    )

    results = []

    for source, replicate, config in configs:
        result = run_one(
            source,
            replicate,
            config,
            args.output_root,
            args.samples,
        )

        results.append(result)

        write_aggregate(
            results,
            args.aggregated,
        )

    print("\n=== COMPLETE ===")
    print(
        f"Results      : {len(results)}"
    )
    print(
        f"Aggregate TSV: {args.aggregated}"
    )


if __name__ == "__main__":
    main()
