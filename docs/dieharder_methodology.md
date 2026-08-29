# Dieharder testing methodology

## Purpose

Dieharder is used as an additional statistical-randomness battery.

Passing Dieharder does not establish cryptographic security,
source secrecy, or physical entropy.

## Tool

Validated local version:

- Dieharder 3.31.1
- input generator: `file_input_raw`
- generator number: 201

The binary input is produced directly by `bioentropy-runner`
using `--dump-bitstream`.

The SHA-256 of the exported file is verified against the
`bitstream_sha256` recorded by the experiment result JSON.

Therefore external batteries evaluate the same bytes as the
internal BioEntropy-HPC statistics.

## Input-reuse policy

A Dieharder result is considered invalid when the tool reports
that the input file was rewound.

Reusing the same finite input inside one statistical test can
invalidate interpretation of the resulting p-value.

The project parser therefore converts any result with:

- `rewinds > 0`

to:

- `INVALID`

regardless of the assessment printed by Dieharder.

## Non-finite p-values

A result with a non-finite p-value, including `nan`, is also
classified as `INVALID`.

This rule is required because Dieharder can print `PASSED` for
a row whose p-value is `nan`.

## Local 16 MiB screening profile

The validated no-rewind local screening subset is:

- 0  Diehard Birthdays
- 2  Diehard 32x32 Binary Rank
- 4  Diehard Bitstream
- 8  Diehard Count the 1s (stream)
- 9  Diehard Count the 1s (byte)
- 15 Diehard Runs
- 16 Diehard Craps
- 100 STS Monobit
- 101 STS Runs
- 102 STS Serial

The local screening profile uses one p-sample and is intended
for integration validation and broad defect screening.

It is not the final statistical campaign.

## Interpretation

Individual `WEAK` assessments are not treated as evidence that
a source is unsuitable.

The final analysis will use repeated independent experiment
replicates and deeper batteries for selected configurations.

Rule90 is retained as a negative control.
ChaCha20 is retained as a deterministic cryptographic reference.
