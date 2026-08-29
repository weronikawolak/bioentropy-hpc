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
## Validated local integration — August 2026

### Software

The local validation environment used:

- Dieharder 3.31.1
- raw binary input generator `file_input_raw`
- generator identifier `201`

External statistical testing is performed on binary files exported
directly by `bioentropy-runner`.

The runner option:

`--dump-bitstream <path>`

writes the same final byte stream that is passed to the internal
statistics accumulator.

For RAW experiments this is the direct source output.

For Ascon-XOF128 experiments this is the conditioned output, not the
pre-conditioning source stream.

### Bitstream identity validation

Before using external batteries, the exported binary files were
validated against the SHA-256 fingerprints stored in the framework's
JSON result files.

For both the Chen 4D-DCS RAW smoke stream and the corresponding
Ascon-XOF128 stream, the independently calculated SHA-256 of the
exported `.bin` file matched the `bitstream_sha256` stored by the
framework.

This establishes the pipeline invariant:

framework statistics input
=
exported binary stream
=
external battery input

and avoids using a second independent stream-generation implementation
for external testing.

### Finite-file safeguards

Dieharder may rewind a finite input file when a test requires more
random numbers than the file contains.

Such results are not interpreted as source-level statistical results.

The BioEntropy-HPC Dieharder parser therefore marks a row as `INVALID`
when:

1. Dieharder reports one or more input-file rewinds; or
2. the returned p-value is not finite, including `nan`.

The classification overrides the textual assessment printed by
Dieharder.

This behavior is necessary because the local validation revealed both
failure modes.

For example, the Byte Distribution test (`d205`) rewound every 16 MiB
input 36 times and consequently produced nominal `FAILED` assessments
even for the ChaCha20 reference.

Those results are classified as `INVALID`.

Likewise, STS Runs applied to the deliberately defective Rule90 stream
returned `p-value = nan` while Dieharder printed `PASSED`.

That row is also classified as `INVALID`.

### 16 MiB capacity probe

A 16 MiB ChaCha20 reference stream was used to determine which tests
can be executed locally without input reuse.

The following tests completed without file rewinding:

- `d0`   Diehard Birthdays
- `d2`   Diehard 32x32 Binary Rank
- `d4`   Diehard Bitstream
- `d8`   Diehard Count the 1s (stream)
- `d9`   Diehard Count the 1s (byte)
- `d15`  Diehard Runs
- `d16`  Diehard Craps
- `d100` STS Monobit
- `d101` STS Runs
- `d102` STS Serial

Tests observed to exceed the 16 MiB local profile include:

- `d17` Marsaglia-Tsang GCD: input rewound 5 times;
- `d205` Byte Distribution: input rewound 36 times;
- `d209` DAB Monobit2: input rewound 15 times.

`d200` RGB Bit Distribution requires an explicit positive `ntuple`
parameter and was therefore not included in the default local subset.

Tests outside the validated local subset may still be used in later
deep-testing campaigns with appropriately sized input streams.

### Screening interpretation

The validated 16 MiB profile currently uses one p-sample per execution.

It is therefore a broad defect-screening and integration-validation
profile, not a final source-ranking procedure.

Individual `WEAK` assessments are retained as follow-up signals but are
not interpreted as evidence of source failure.

Source-level conclusions will require repeated independent experiment
replicates and aggregation across those replicates.

Statistical-test success must also not be interpreted as evidence of:

- cryptographic security;
- secrecy;
- physical entropy;
- high min-entropy;
- unpredictability against an informed adversary.
