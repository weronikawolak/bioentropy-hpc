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


## Source-specific replication semantics

A dedicated replication audit was performed before constructing the
multi-replicate external-battery campaign.

For each source, two configurations were created that differed only in
`experiment.replicate_id` (0 versus 1). The resulting bitstream
SHA-256 fingerprints were compared.

Observed behavior:

| Source | rep0 vs rep1 | Interpretation |
|---|---|---|
| Chen 4D-DCS | SAME | replicate_id alone does not change the explicit dynamical state |
| Logistic Map with explicit x0 | SAME | replicate_id alone does not change the explicit initial state |
| Rule30 | DIFFERENT | replicate seed changes the CA realization |
| Rule90 | DIFFERENT | replicate seed changes the CA realization |
| ChaCha20 reference | DIFFERENT | replicate seed changes derived key/nonce material |
| DNA sequence | SAME | replicate_id does not change the selected biological sequence |

This audit prevents pseudoreplication.

### Chen 4D-DCS

The primary Chen profile uses explicitly configured dynamical parameters
and an explicit four-dimensional initial state.

Changing only `replicate_id` changes experiment metadata and the derived
framework seed but does not alter the generated Chen trajectory.

Therefore independent Chen realizations must be created by explicitly
changing the initial state.

The reference configuration:

`r = 5`

and:

`(x0, y0, z0, w0) = (0.1, 0.2, 0.3, 0.4)`

is retained as the reference realization.

Additional realizations will use deterministic, reproducibly generated
initial-state vectors while keeping the system parameter fixed unless a
separate parameter-sensitivity experiment is explicitly performed.

### Logistic Map

For Logistic configurations using:

`initial_state.mode = explicit`

changing `replicate_id` does not alter the trajectory.

Independent realizations therefore require distinct initial values
`x0`.

For arithmetic-precision comparisons, the same nominal `x0` must be
used for float32, float64, fixed-point Q3.29, and MPFR-256 within each
matched replicate.

This preserves a paired experimental design: arithmetic representation
changes while the nominal dynamical parameters remain fixed.

### Cellular automata

Rule30 and Rule90 produced different streams when only the replicate
identifier changed.

The derived experiment seed therefore provides an appropriate mechanism
for generating distinct CA initial states.

The replicate identifier can consequently be used directly for
independent CA realizations within a fixed rule/width configuration.

### ChaCha20 reference

ChaCha20 also produced different streams for different replicate
identifiers.

This is expected because the deterministic framework seed contributes
to the derived ChaCha20 key/nonce material.

Replicate identifiers can therefore be used directly to generate
independent deterministic reference streams.

### DNA

DNA sequence output was unchanged when only the replicate identifier
changed.

The biological sequence itself is the source.

Consequently, DNA replication is defined through distinct versioned
sequence windows rather than artificial experiment seeds.

The existing DNA campaign uses multiple deterministic windows from
multiple reference assemblies.

Changing only `replicate_id` for a fixed DNA window would constitute
pseudoreplication and is prohibited in the final analysis.

### General principle

An experiment replicate is considered independent only when it changes
the effective source realization.

A changed metadata identifier or derived seed is insufficient when the
configured source does not consume that seed.

This source-specific replication policy will be used by all subsequent
statistical campaigns.


## DNA finite-input policy

A dedicated capacity experiment was performed for one standard DNA
window.

The evaluated DNA window contained:

- 400,000 nucleotides;
- 800,000 mapped bits;
- 100,000 binary bytes.

The same validated Dieharder subset used for 16 MiB digital-source
screening was applied without changing test parameters.

None of the tested Dieharder tests could consume the 100 kB DNA window
without reusing input.

Observed input rewinds included:

- d0: 41 rewinds
- d2: 91 rewinds
- d4: 50 rewinds
- d8: 42 rewinds
- d9: 91 rewinds
- d15: 44 rewinds
- d16: 92 rewinds
- d100: 44 rewinds
- d101: 44 rewinds
- d102: 44 rewinds

Consequently, every p-value produced by this experiment is classified
as INVALID.

Nominal PASS, WEAK, or FAIL labels printed by Dieharder for these runs
must not be interpreted as properties of the DNA sequence.

### Decision

The project will not reduce Dieharder test parameters specifically for
DNA merely to make a single 100 kB window fit the battery.

Such a change would create a different statistical testing regime and
weaken direct comparison with the digital-source screening profile.

Instead, two levels of DNA analysis are distinguished:

1. individual DNA windows remain the primary biological units for
   source statistics and replicate-level analysis;

2. a separately identified concatenated DNA corpus may be used for
   corpus-level external-battery diagnostics when sufficient unique
   biological data are available.

A concatenated DNA corpus is not interpreted as one independent DNA
replicate.

Its results characterize the pooled mapped corpus and are reported
separately from per-window inference.

No DNA window is repeated or looped to satisfy an external battery's
input requirement.


## DNA corpus-level Dieharder diagnostic

Because a single 400,000-nucleotide DNA window provides only 100,000
binary bytes and is insufficient for the validated Dieharder profile,
a separate corpus-level diagnostic input was constructed.

### Corpus construction

The corpus contains 50 distinct preselected versioned DNA windows.

Each window contributes:

- 400,000 nucleotides;
- 800,000 mapped bits;
- 100,000 bytes.

Total corpus size:

- 50 windows;
- 20,000,000 nucleotides;
- 40,000,000 mapped bits;
- 5,000,000 bytes.

Corpus SHA-256:

`f2ea67e8a6d33cb7b6aa6bfd95a2eab960d323f87acd77128714e7f4609c2c93`

The windows are concatenated without separators.

Their ordering is deterministic and recorded in a manifest using:

1. assembly accession;
2. sequence accession;
3. window start;
4. experiment identifier.

Each individual window bitstream is also recorded together with its own
SHA-256 fingerprint.

The concatenated corpus is explicitly treated as a pooled diagnostic
object and not as one biological replicate.

### Capacity result

The 5 MB corpus was sufficient for the following tests without input
reuse:

- d0   Diehard Birthdays
- d8   Diehard Count the 1s (stream)
- d15  Diehard Runs
- d100 STS Monobit
- d101 STS Runs
- d102 STS Serial

The following tests still required one file rewind and were therefore
classified as INVALID:

- d2   Diehard 32x32 Binary Rank
- d4   Diehard Bitstream
- d9   Diehard Count the 1s (byte)
- d16  Diehard Craps

No result from those four tests is used for scientific interpretation.

### Valid corpus-level results

Across the 36 rows that did not reuse input:

- PASS: 2
- WEAK: 3
- FAIL: 31

The two PASS rows were the two outputs of Diehard Runs.

The WEAK observations were:

- Diehard Birthdays:
  p = 0.00103340
- STS Monobit:
  p = 0.00010563
- STS Serial, ntuple 1:
  p = 0.00010563

The valid FAILED results included:

- STS Runs:
  p = 1.00000000
- Diehard Count the 1s (stream):
  p = 0.00000000
- STS Serial for essentially all evaluated tuple orders above ntuple 1.

The multiple STS Serial rows are related subtests and must not be
treated as independent experimental replicates.

The appropriate interpretation is therefore not "31 independent
failures", but that the pooled mapped DNA corpus exhibits strong and
consistently detectable serial structure across the STS Serial family.

### Interpretation limits

This corpus-level result does not imply that every individual DNA window
would independently fail the same tests.

It characterizes the pooled mapped corpus.

Likewise, the high Shannon entropy observed for many individual DNA
windows must not be interpreted as absence of serial structure.

The DNA results reinforce a central distinction in this project:

near-maximal first-order Shannon entropy can coexist with substantial
higher-order statistical dependence.

The corpus-level Dieharder result is therefore reported separately from
the per-window biological analysis.


## Frozen digital-source screening profile

Following the replicate-aware validation campaign, the primary
digital-source Dieharder screening profile is frozen as follows.

Input per realization:

- 16 MiB;
- 134,217,728 bits;
- no input reuse permitted.

Tests:

- d0
- d2
- d4
- d8
- d9
- d15
- d16
- d100
- d101
- d102

Dieharder configuration:

- generator 201 (`file_input_raw`);
- `psamples = 1`.

The complete ten-source validation produced zero file rewinds.

Therefore a rewind observed in the final campaign is treated as an
execution anomaly and invalidates the corresponding row.

The final campaign uses multiple explicit source realizations rather
than increasing Dieharder's internal p-sample count.

This makes the experimental unit visible and reproducible in the
BioEntropy-HPC framework and enables source-specific replication
semantics.

The primary analysis will examine repeated p-values and recurring
test-family patterns across realizations.

Raw row counts are retained for traceability but are not interpreted as
independent-test failure rates because some Dieharder invocations,
especially STS Serial, emit multiple related result rows.


## Replicate-level aggregation

Primary campaign interpretation is performed at the test-family
and realization levels rather than by counting raw Dieharder
output rows.

For a given source realization and test family:

- FAILED if any valid row in the family is FAILED;
- otherwise WEAK if any valid row is WEAK;
- otherwise PASSED if at least one valid row is PASSED;
- INVALID if no valid row is available.

For a source realization, the conservative overall screening
outcome is FAILED if any family is FAILED, otherwise WEAK if
any family is WEAK, otherwise PASSED.

This consolidation prevents multi-row families such as STS
Serial from receiving disproportionate weight.

Non-finite p-values remain INVALID and are never converted into
FAILED results. Input reuse or any detected rewind also renders
the affected result invalid.

Replicate-level screening outcomes are descriptive and are not
interpreted as a formal multiple-testing-adjusted hypothesis
test.
