#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNNER = (
    ROOT / "build" / "bioentropy-runner"
)

ADAPTER = (
    ROOT
    / "scripts"
    / "preprocessing"
    / "prepare_nist90b_samples.py"
)

PARSER = (
    ROOT
    / "analysis"
    / "scripts"
    / "parse_nist90b.py"
)

EA_NON_IID = (
    ROOT
    / "external"
    / "nist-sp800-90b"
    / "cpp"
    / "ea_non_iid"
)

MANIFEST = (
    ROOT
    / "datasets"
    / "manifests"
    / "dna_nist90b_pairs.jsonl"
)

OUTPUT_ROOT = (
    ROOT
    / "results"
    / "external"
    / "nist90b-dna-pairs"
)

AGGREGATED = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_dna_pairs.tsv"
)


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(
            1024 * 1024
        ):
            digest.update(chunk)

    return digest.hexdigest()


def run(command, cwd=None):
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{result.returncode}:\n"
            f"{' '.join(str(x) for x in command)}\n\n"
            f"{result.stdout}"
        )

    return result


def metric_for(experiment_id):
    return (
        ROOT
        / "results"
        / "metrics"
        / f"{experiment_id}_rep0000.json"
    )


def verify_member(
    member,
    raw_path,
):
    metric_path = metric_for(
        member["experiment_id"]
    )

    if not metric_path.is_file():
        raise FileNotFoundError(
            metric_path
        )

    metric = json.loads(
        metric_path.read_text()
    )

    expected_raw = metric[
        "reproducibility"
    ]["bitstream_sha256"]

    actual_raw = sha256_file(
        raw_path
    )

    if actual_raw != expected_raw:
        raise RuntimeError(
            "RAW provenance mismatch for "
            f"{member['experiment_id']}"
        )

    metric_window_sha = metric[
        "source"
    ]["parameters"][
        "expected_sequence_sha256"
    ]

    if (
        metric_window_sha
        != member["window_sha256"]
    ):
        raise RuntimeError(
            "Sequence provenance mismatch for "
            f"{member['experiment_id']}"
        )

    if raw_path.stat().st_size != 100_000:
        raise RuntimeError(
            "Unexpected DNA RAW size for "
            f"{member['experiment_id']}: "
            f"{raw_path.stat().st_size}"
        )

    return actual_raw


def load_pairs():
    pairs = []

    with MANIFEST.open(
        encoding="utf-8",
    ) as handle:
        for line in handle:
            if line.strip():
                pairs.append(
                    json.loads(line)
                )

    return pairs


def write_aggregate(rows):
    AGGREGATED.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "pair_id",
        "corpus",
        "organism",
        "pair_index",
        "samples",
        "p1",
        "h_original",
        "assessment_status",
        "provenance_ok",
        "member_0",
        "member_1",
        "member_0_raw_sha256",
        "member_1_raw_sha256",
        "pair_raw_sha256",
        "nist_input_sha256",
    ]

    with AGGREGATED.open(
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
        writer.writerows(rows)


def run_pair(pair):
    pair_id = pair["pair_id"]

    print(
        f"\n=== {pair_id} ===",
        flush=True,
    )

    result_dir = (
        OUTPUT_ROOT / pair_id
    )

    result_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    members = []

    for i in range(2):
        members.append(
            {
                "experiment_id": (
                    pair[
                        "member_experiment_ids"
                    ][i]
                ),
                "config_file": (
                    pair[
                        "member_config_files"
                    ][i]
                ),
                "window_sha256": (
                    pair[
                        "member_window_sha256"
                    ][i]
                ),
            }
        )

    with tempfile.TemporaryDirectory(
        prefix=f"{pair_id}-"
    ) as temp_name:
        temp = Path(temp_name)

        raw_paths = []
        member_raw_shas = []

        for i, member in enumerate(
            members
        ):
            member_dir = (
                temp / f"member{i}"
            )

            member_dir.mkdir()

            # DNA configs use repository-relative paths such as
            # datasets/processed/dna/... . Keep execution in the
            # temporary directory so normal metrics are isolated,
            # while exposing the frozen dataset through a symlink.
            datasets_link = (
                member_dir / "datasets"
            )

            datasets_link.symlink_to(
                ROOT / "datasets",
                target_is_directory=True,
            )

            raw_path = (
                member_dir / "raw.bin"
            )

            config = (
                ROOT
                / member["config_file"]
            )

            if not config.is_file():
                raise FileNotFoundError(
                    config
                )

            runner = run(
                [
                    str(RUNNER),
                    "--config",
                    str(config),
                    "--dump-bitstream",
                    str(raw_path),
                ],
                cwd=member_dir,
            )

            (
                result_dir
                / f"runner-member{i}.txt"
            ).write_text(
                runner.stdout,
                encoding="utf-8",
            )

            raw_sha = verify_member(
                member,
                raw_path,
            )

            raw_paths.append(raw_path)
            member_raw_shas.append(
                raw_sha
            )

            print(
                f"{member['experiment_id']}: "
                f"provenance PASS "
                f"{raw_sha[:12]}..."
            )

        pair_raw = (
            temp / "pair.raw.bin"
        )

        with pair_raw.open(
            "wb"
        ) as dst:
            for raw_path in raw_paths:
                with raw_path.open(
                    "rb"
                ) as src:
                    shutil.copyfileobj(
                        src,
                        dst,
                    )

        if pair_raw.stat().st_size != 200_000:
            raise RuntimeError(
                "Expected 200000-byte "
                "paired DNA RAW stream."
            )

        pair_raw_sha = sha256_file(
            pair_raw
        )

        samples = (
            temp / "samples.bin"
        )

        adapter = run(
            [
                sys.executable,
                str(ADAPTER),
                str(pair_raw),
                str(samples),
                "--max-samples",
                "1600000",
            ]
        )

        (
            result_dir / "adapter.txt"
        ).write_text(
            adapter.stdout,
            encoding="utf-8",
        )

        sample_meta = (
            samples.with_suffix(
                ".bin.json"
            )
        )

        nist = subprocess.run(
            [
                str(EA_NON_IID),
                "-i",
                samples.name,
                "1",
            ],
            cwd=temp,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        nist_txt = (
            result_dir
            / "ea_non_iid.txt"
        )

        nist_txt.write_text(
            nist.stdout,
            encoding="utf-8",
        )

        if nist.returncode != 0:
            raise RuntimeError(
                f"ea_non_iid failed for "
                f"{pair_id} "
                f"(exit={nist.returncode}):\n"
                f"{nist.stdout}"
            )

        result_json = (
            result_dir / "result.json"
        )

        run(
            [
                sys.executable,
                str(PARSER),
                "--nist-output",
                str(nist_txt),
                "--sample-metadata",
                str(sample_meta),
                "--output",
                str(result_json),
                "--source",
                f"dna-{pair['corpus']}",
                "--replicate-id",
                f"pair{pair['pair_index']:02d}",
            ]
        )

        result = json.loads(
            result_json.read_text()
        )

        result.update(
            {
                "pair_id": pair_id,
                "corpus": pair[
                    "corpus"
                ],
                "organism": pair[
                    "organism"
                ],
                "pair_index": pair[
                    "pair_index"
                ],
                "provenance_ok": True,
                "member_0": members[0][
                    "experiment_id"
                ],
                "member_1": members[1][
                    "experiment_id"
                ],
                "member_0_raw_sha256": (
                    member_raw_shas[0]
                ),
                "member_1_raw_sha256": (
                    member_raw_shas[1]
                ),
                "pair_raw_sha256": (
                    pair_raw_sha
                ),
                "assessment_status": (
                    "nist_estimated"
                ),
                "pairing_scheme": pair[
                    "pairing_scheme"
                ],
            }
        )

        result_json.write_text(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        print(
            f"Samples    : "
            f"{result['samples']}"
        )

        print(
            f"P(1)       : "
            f"{result['p1']:.6f}"
        )

        print(
            f"H_original : "
            f"{result['h_original']:.6f}"
        )

        return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--corpus",
        default=None,
    )

    parser.add_argument(
        "--pair",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    pairs = load_pairs()

    if args.corpus is not None:
        pairs = [
            p
            for p in pairs
            if p["corpus"]
            == args.corpus
        ]

    if args.pair is not None:
        pairs = [
            p
            for p in pairs
            if p["pair_index"]
            == args.pair
        ]

    if not pairs:
        raise RuntimeError(
            "No matching DNA pairs."
        )

    print(
        "DNA pairs:",
        len(pairs),
    )

    results = []

    for pair in pairs:
        results.append(
            run_pair(pair)
        )

        write_aggregate(
            results
        )

    print("\n=== COMPLETE ===")
    print(
        "Results:",
        len(results),
    )
    print(
        "Aggregate:",
        AGGREGATED,
    )


if __name__ == "__main__":
    main()
