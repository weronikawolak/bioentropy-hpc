# BioEntropy HPC — Research and Implementation Log

## Project title

**HPC-Assisted Evaluation of Bio-Inspired Entropy Sources and Their Impact on Lightweight Cryptographic Mechanisms**

Polish working title:

**Wspomagana obliczeniami HPC ocena bioinspirowanych źródeł entropii oraz ich wpływu na lekkie mechanizmy kryptograficzne**

---

# 1. Purpose of this document

This document records the technical, methodological, experimental,
and reproducibility decisions made during the BioEntropy HPC project.

It is intended to serve as:

- a reproducibility log,
- an implementation history,
- a source for the later Methods section of the scientific paper,
- a record of design decisions and scope reductions,
- a distinction between completed implementation, preliminary local
  results, and experiments that still require final HPC execution.

The document should be updated after every significant implementation
or experimental milestone.

---

# 2. Main research objective

The project investigates whether measurable statistical properties of
candidate randomness sources translate into measurable differences in
the behavior of lightweight cryptographic mechanisms.

The main causal chain studied is:

source
→ statistical / entropy characteristics
→ optional conditioning
→ cryptographic material
→ cryptographic mechanism
→ security-related and performance-related measurements

The main scientific question is therefore not simply:

"Does a source pass randomness tests?"

but rather:

"Do measurable differences in source quality remain relevant after
conditioning and when the resulting material is used in cryptographic
workflows?"

---

# 3. Fundamental methodological principles

Several distinctions are treated as fundamental throughout the project.

## 3.1 Statistical randomness is not cryptographic security

Passing statistical randomness batteries does not constitute proof that
a generator or cryptographic construction is secure.

Statistical tests are treated as diagnostics.

Cryptographic security must not be inferred only from:

- high Shannon entropy,
- low bias,
- low autocorrelation,
- NIST STS test success,
- TestU01 success,
- apparently random ciphertext.

---

## 3.2 Shannon entropy is not min-entropy

Shannon entropy and min-entropy measure different properties.

The project therefore does not interpret high Shannon entropy as
equivalent to strong entropy in the cryptographic sense.

The planned deep-analysis stage includes NIST SP 800-90B-compatible
min-entropy estimation.

---

## 3.3 Public DNA sequences are deterministic data

Public genomic sequences are not treated as physical entropy sources.

When a fixed, versioned public DNA sequence and a deterministic mapping
are used, the resulting bitstream is reproducible and deterministic.

The project therefore uses terminology such as:

- candidate randomness source,
- deterministic candidate source,
- bio-inspired source,

rather than automatically calling public DNA a true entropy source.

---

## 3.4 Digitally evaluated chaotic systems are deterministic

Logistic and related digitally implemented chaotic maps are also
deterministic once:

- parameters,
- floating-point representation,
- initial state,
- extraction method,
- implementation,

are fixed.

They are therefore evaluated as deterministic candidate randomness
sources rather than assumed physical entropy sources.

---

## 3.5 Conditioning does not create missing entropy

Ascon-XOF128 is used as a conditioning mechanism.

The project asks whether conditioning removes or reduces visible
statistical defects.

It does not assume that deterministic conditioning can create physical
entropy that was not present in the original source.

The RAW and conditioned variants are therefore always conceptually
distinguished.

---

# 4. Final narrowed project scope

The original project concept was broader and included:

- Logistic Map,
- hyperchaotic systems,
- cellular automata,
- DNA sequences,
- multiple PRGs,
- NIST SP 800-22,
- Dieharder,
- TestU01,
- NIST SP 800-90B,
- multiple DNA cryptosystems,
- DNA + ECC,
- several standard cryptographic mechanisms,
- MPI,
- GPU / CUDA,
- broad scaling experiments.

The scope was intentionally reduced to retain scientific quality while
keeping the project feasible.

---

# 5. Candidate source set

The current source set is:

1. Logistic Map
2. Cellular Automaton Rule 30
3. Cellular Automaton Rule 90
4. public versioned DNA sequences
5. ChaCha20 deterministic cryptographic reference PRG

---

## 5.1 Logistic Map

Role:

candidate deterministic chaotic source.

Equation:

x[n+1] = r * x[n] * (1 - x[n])

Primary screening parameter range:

r ∈ [3.57, 4.00]

Screening design:

- 100 values of r,
- 20 deterministic replicates,
- total: 2000 experiments.

A separate deterministic x0 is derived for each replicate.

The same replicate-level x0 is used across all tested values of r.

This avoids a full r × x0 factorial design and isolates the effect of r
more cleanly.

Initial-state derivation domain:

BIOENTROPY-HPC-LOGISTIC-X0-v1

Generation details:

- double precision,
- no fast-math,
- no floating-point contraction,
- configurable burn-in,
- threshold extraction,
- threshold: x >= 0.5,
- bits packed MSB-first.

Explicit test vector:

r = 4
x0 = 0.123456789
burn-in = 10

Expected bytes:

15 cd fc 5e

The implementation is deterministic and invariant to generation chunk
size.

---

## 5.2 Cellular Automaton Rule 30

Role:

bio-inspired / cellular deterministic candidate source.

Rule:

Elementary Cellular Automaton Rule 30.

Tested widths:

- 256 cells
- 1024 cells

Replicates:

20 per width.

Total Rule 30 screening configurations:

40.

Boundary conditions:

periodic.

Generation 0 is used as initial state and is not emitted as output.

Initial state is deterministically derived using domain:

BIOENTROPY-HPC-CA-INIT-v1

Reference test vector for seed bytes 00..1f:

Rule 30:

5cfbadcff73e5eb945f018c34c38c829

---

## 5.3 Cellular Automaton Rule 90

Role:

negative control.

Rule 90 is intentionally included because it can exhibit strong
structural behavior and degeneration.

It is not included because it is expected to behave as a strong random
source.

Its purpose is to test whether the experimental framework can correctly
distinguish apparently high bit-level entropy from substantial serial
structure.

Widths:

- 256 cells
- 1024 cells

Replicates:

20 per width.

Total Rule 90 screening configurations:

40.

Reference test vector for seed bytes 00..1f:

d4bfefe6d52f0cfc50d01a426428e8b9

Observed strong degeneration in preliminary experiments is treated as
a meaningful negative-control result, not automatically as an
implementation error.

---

# 6. ChaCha20 reference PRG

ChaCha20 is included as a deterministic cryptographic reference PRG.

It is not treated as an entropy source.

Purpose:

provide a reference stream generated by an established cryptographic
primitive against which candidate sources can be compared statistically.

Implementation:

OpenSSL EVP ChaCha20.

Key derivation domain:

BIOENTROPY-HPC-CHACHA20-KEY-v1

Nonce derivation domain:

BIOENTROPY-HPC-CHACHA20-NONCE-v1

IV layout:

counter64_le || nonce64

Replicates:

20.

The implementation is deterministic and chunk invariant.

---

# 7. DNA source

## 7.1 DNA source role

DNA is evaluated separately as a deterministic biological data source.

This part of the project concerns statistical properties of public,
versioned nucleotide sequences.

It must not be confused with the later DNA-based image cipher
reproduction.

---

## 7.2 Primary DNA-to-bit mapping

For the source-analysis part of the project:

A = 00
C = 01
G = 10
T = 11

Packing:

MSB-first.

A sensitivity analysis using all eight valid DNA mappings may be
performed later on a smaller subset.

The primary campaign uses only the mapping above.

---

## 7.3 DNA dataset

Five reference genomes are used:

### Escherichia coli K-12 MG1655

Assembly:

GCF_000005845.2

### Bacillus subtilis 168

Assembly:

GCF_000009045.1

### Saccharomyces cerevisiae S288C

Assembly:

GCF_000146045.2

### Arabidopsis thaliana TAIR10.1

Assembly:

GCF_000001735.4

### Caenorhabditis elegans WBcel235

Assembly:

GCF_000002985.6

---

## 7.4 DNA window design

For each genome:

- 10 deterministic non-overlapping windows,
- 400,000 nucleotides per window,
- 2 bits per nucleotide,
- 800,000 output bits per stream.

Total:

5 genomes × 10 windows = 50 DNA streams.

Window-selection domain:

BIOENTROPY-HPC-DNA-WINDOW-SELECTION-v1

DNA sequences are validated using:

- expected sequence length,
- canonical A/C/G/T requirement,
- SHA-256 fingerprint.

Fixture:

ACGTTCGATGCATAGC

Expected encoded bytes:

1B D8 E4 C9

---

# 8. DNA preliminary screening results

The complete 50-stream DNA campaign was successfully generated and
validated locally.

Preliminary group medians:

## Arabidopsis thaliana

bias:
0.001276

Shannon entropy:
0.999995

|AC1|:
0.167508

|runs z|:
149.825

longest run:
71.5

---

## Bacillus subtilis

bias:
0.012628

Shannon entropy:
0.999539

|AC1|:
0.103631

|runs z|:
92.692

longest run:
19

---

## Caenorhabditis elegans

bias:
0.001048

Shannon entropy:
0.999997

|AC1|:
0.206790

|runs z|:
184.960

longest run:
32.5

---

## Escherichia coli

bias:
0.001583

Shannon entropy:
0.999993

|AC1|:
0.026899

|runs z|:
24.061

longest run:
19

---

## Saccharomyces cerevisiae

bias:
0.001092

Shannon entropy:
0.999997

|AC1|:
0.138025

|runs z|:
123.455

longest run:
60

---

## 8.1 Important preliminary observation

Several DNA streams exhibit Shannon entropy extremely close to one while
simultaneously exhibiting substantial serial dependence.

This is an important motivation for using multiple statistical metrics
instead of interpreting Shannon entropy alone.

These values are currently descriptive experimental results and do not
constitute claims of cryptographic security.

---

# 9. Screening metrics implemented

The project implements streaming calculation of:

- number of bytes,
- number of bits,
- zeros,
- ones,
- P(0),
- P(1),
- bit bias,
- Shannon entropy,
- lag-1 autocorrelation,
- runs count,
- expected runs,
- runs z-score,
- longest run,
- SHA-256 fingerprint.

The metric implementation is streaming and chunk-size invariant.

Undefined metrics are represented as null in persistent JSON results
when appropriate.

---

# 10. Reproducibility and seed management

Seed derivation is deterministic.

SeedManager domain:

BIOENTROPY-HPC-SEED-v1

A previously validated reference derivation produced:

a2b988dbbd0a0dde17e2124a203c405f5853d1db03547372a547682f38ee8d30

The seed architecture is intended to ensure reproducibility across:

- local runs,
- HPC runs,
- repeated analysis,
- different chunk sizes.

---

# 11. Result persistence

Experiment results are stored as machine-readable JSON.

Stored information includes:

- experiment ID,
- replicate ID,
- source type,
- source parameters,
- output length,
- execution chunk size,
- derived seed,
- statistical metrics,
- SHA-256 fingerprint.

After conditioning support was introduced, result files also store:

- conditioning mode,
- conditioning input length,
- conditioning output length,
- raw pre-conditioning SHA-256 for conditioned runs.

The fingerprint stored as the main bitstream SHA represents the stream
that was actually evaluated statistically.

For RAW:

bitstream_sha256 = raw source output SHA-256

For Ascon-XOF128:

input_sha256 = raw source output SHA-256

bitstream_sha256 = conditioned output SHA-256

---

# 12. Screening campaign

The main screening campaign contains:

## Logistic Map

100 values r × 20 replicates

= 2000 experiments

## Cellular Automata

Rule 30 and Rule 90

2 rules × 2 widths × 20 replicates

= 80 experiments

## ChaCha20

20 replicates

= 20 experiments

Total screening campaign:

2100 experiments.

DNA is handled as its own 50-stream dataset.

---

# 13. Screening campaign infrastructure

Implemented:

scripts/preprocessing/generate_screening_campaign.py

Generated configuration directory:

configs/generated/screening/

Manifest:

configs/generated/screening/manifest.tsv

Manifest source labels:

- logistic
- cellular_automaton
- chacha20_reference

SLURM infrastructure includes:

scripts/slurm/run_screening_array.sh

scripts/slurm/submit_screening_array.sh

scripts/slurm/check_hpc_environment.sh

scripts/slurm/prepare_screening_cluster.sh

SLURM array concurrency is configurable.

Default maximum concurrent jobs:

64

Optional environment-specific values include:

SLURM_PARTITION

SLURM_ACCOUNT

---

# 14. Current screening execution status

The full 2100-experiment screening campaign has NOT yet been executed
on HPC.

Only local development / smoke-test configurations have been executed.

A previous checker state reported:

Expected:
2100

Complete:
6

Missing:
2094

Invalid:
0

Progress:
0.29%

These numbers represent development-stage local execution and are not
final experimental results.

---

# 15. Preliminary source observations

## Logistic Map example

For r = 3.57, replicate 0:

bias approximately:
0.16361

Shannon entropy approximately:
0.921322

lag-1 autocorrelation approximately:
-0.5069

|runs z| approximately:
506.9

This illustrates substantial statistical weakness in some areas of the
parameter space.

---

## Rule 30 example

For a preliminary 1024-cell stream:

bias approximately:
0.000249

Shannon entropy:
approximately 1.0

|AC1| approximately:
0.002299

|runs z| approximately:
2.298

longest run:
21

---

## Rule 90 example

For a preliminary 1024-cell stream:

bias approximately:
0.238714

Shannon entropy:
0.828681

|AC1| approximately:
0.32287

|runs z| approximately:
322.87

longest run:
477760

The large longest-run value is consistent with the purpose of Rule 90
as a negative control.

---

## ChaCha20 example

Preliminary screening values showed approximately:

median bias:
0.000742

Shannon entropy:
0.999998

|AC1|:
0.000351

|runs z|:
0.350

longest run:
21.5

These results are development-stage values.

---

# 16. Analysis infrastructure

Implemented analysis scripts include:

analysis/scripts/aggregate_results.py

analysis/scripts/validate_dna_results.py

analysis/scripts/summarize_serial_metrics.py

analysis/scripts/analyze_logistic_screening.py

analysis/scripts/analyze_ca_chacha_screening.py

analysis/scripts/build_source_comparison.py

The current source-comparison aggregation combines:

- Logistic groups,
- CA groups,
- ChaCha20 reference,
- DNA genome groups.

A previous local intermediate source-comparison table contained:

110 rows

with:

10 rows having available data

and:

5 complete groups

This is not the final experimental table.

---

# 17. Planned statistical treatment

Final analysis is planned to use:

- median,
- interquartile range,
- 95% bootstrap confidence intervals,
- effect sizes,
- Spearman correlation,
- Holm correction for multiple comparisons.

Mixed-effects modelling will only be introduced if the final data
structure requires it.

The project avoids unnecessary statistical complexity.

---

# 18. Deep randomness evaluation

The reduced plan includes:

## NIST SP 800-90B

Purpose:

min-entropy estimation.

Status:

PLANNED.

---

## NIST Statistical Test Suite

Purpose:

diagnostic randomness testing.

Status:

PLANNED.

The test suite will not be interpreted as a standalone cryptographic
security assessment.

---

## TestU01

Planned use:

- SmallCrush for screening,
- selected Crush runs,
- BigCrush only for selected final representative streams.

Running BigCrush across every candidate configuration was intentionally
removed from scope.

---

## Dieharder

Removed from the final reduced experimental scope.

---

# 19. HPC strategy

The project is designed for HPC execution but development is completed
locally first.

Explicit workflow decision:

**All project code should be functionally complete and smoke-tested
locally before large-scale HPC execution.**

Local development covers:

- sources,
- metrics,
- result persistence,
- conditioning,
- campaign generators,
- NIST/TestU01 wrappers,
- cryptographic mechanisms,
- benchmarks,
- analysis scripts,
- statistical scripts,
- figures,
- SLURM scripts.

HPC will later be used for:

- full 2100-stream screening,
- final representative selection,
- deep randomness batteries,
- conditioning campaigns,
- cryptographic campaigns where appropriate,
- scalability experiments.

---

# 20. HPC technologies retained

Retained:

- SLURM arrays,
- CPU parallel execution,
- OpenMP where useful.

Removed from reduced scope:

- MPI,
- GPU,
- CUDA.

---

# 21. HPC scaling plan

Planned worker counts:

1
2
4
8
16
32

Planned measurements:

- campaign wall-clock time,
- aggregate throughput,
- parallel efficiency.

The focus is campaign-level HPC scalability rather than redesigning all
algorithms for distributed-memory execution.

---

# 22. Ascon reference dependency

The official Ascon C implementation is included as a Git submodule:

third_party/ascon-c

Pinned commit:

446347f21b209f3921c65ece70027c366cbe1693

The pinned upstream commit references the final NIST SP 800-232
standard.

This dependency is used for:

- Ascon-XOF128 conditioning,
- Ascon-AEAD128 cryptographic baseline.

---

# 23. Ascon-XOF128 conditioning

## Status

DONE locally.

---

## 23.1 Reference implementation validation

The official reference Ascon-XOF128 implementation was compiled.

Known Answer Test generation was performed using the upstream test
infrastructure.

Generated:

LWC_XOF_KAT_128_512.txt

The generated file was compared bit-for-bit with the upstream
reference file.

Result:

diff exit code = 0

Therefore the pinned upstream reference implementation was reproduced
successfully.

---

## 23.2 Variable-output adapter

The upstream KAT wrapper emits a fixed-size output.

A local adapter was therefore implemented to expose variable-length
Ascon-XOF128 output while preserving the same reference construction.

Function:

bioentropy_ascon_xof128(
    out,
    out_len,
    in,
    in_len
)

The implementation follows:

- ASCON_XOF_IV initialization,
- P12 permutation,
- 8-byte absorption rate,
- final padding,
- P12,
- arbitrary-length squeezing.

---

## 23.3 C++ conditioner

Implemented:

include/bioentropy/conditioning/AsconXof128Conditioner.hpp

src/conditioning/AsconXof128Conditioner.cpp

Tests cover:

- input sizes:
  - 0
  - 1
  - 7
  - 8
  - 9
  - 64
  - 1024
- reference equivalence,
- variable-output prefix consistency,
- deterministic output,
- input sensitivity,
- empty output.

The tests were changed from assert-based validation to explicit
Release-safe checks because Release builds define NDEBUG and would
otherwise disable assert statements.

---

# 24. Conditioning configuration

Experiment configuration supports:

conditioning:
  mode: raw

or:

conditioning:
  mode: ascon_xof128

If the conditioning section is absent, RAW is used for backward
compatibility.

This allows the original screening configurations to continue working
unchanged.

---

# 25. Conditioning implementation semantics

RAW mode preserves the original streaming execution path.

For Ascon-XOF128:

1. the complete deterministic raw stream is generated,
2. the complete raw stream is buffered,
3. SHA-256 of the raw stream is calculated,
4. Ascon-XOF128 absorbs the entire raw stream once,
5. the XOF emits exactly the same number of bytes as the input,
6. statistics are calculated on the conditioned output.

Conditioning is NOT performed independently per execution chunk.

This design prevents conditioning output from depending on arbitrary
chunk size.

For current experiment sizes the required buffering is small enough for
local and HPC execution.

---

# 26. Paired RAW / Ascon experiment design

RAW and conditioned experiments are paired by:

- identical experiment ID,
- identical replicate ID,
- identical master seed,
- identical source configuration.

Conditioned result filenames receive suffix:

_ascon-xof128

This prevents the conditioned run from overwriting the RAW result.

The key reproducibility condition is:

RAW bitstream SHA-256
==
conditioned run input SHA-256

and simultaneously:

RAW bitstream SHA-256
!=
conditioned output SHA-256

This verifies that the source input is identical while the conditioning
transformation changes the evaluated stream.

---

# 27. Conditioning campaign infrastructure

Implemented:

scripts/preprocessing/generate_conditioning_campaign.py

scripts/local/run_conditioning_campaign.py

scripts/local/run_conditioning_smoke.sh

analysis/scripts/check_conditioning_campaign.py

analysis/scripts/analyze_conditioning_effect.py

---

## 27.1 Conditioning campaign composition

Before final Logistic candidate selection, the conditioning campaign
contains:

Cellular Automata:
80 base streams

ChaCha20:
20 base streams

DNA:
50 base streams

Total current base streams:
150

For each base stream:

- RAW configuration,
- Ascon-XOF128 configuration.

Current paired configurations:

300.

Final Logistic representatives will be added only after the full
screening campaign is completed.

This prevents arbitrary pre-selection of Logistic parameters.

---

## 27.2 Conditioning metrics

For each pair the analysis calculates changes in:

- bias,
- Shannon entropy,
- absolute lag-1 autocorrelation,
- absolute runs z-score,
- longest run.

Interpretation:

For bias:
negative delta = improvement

For |AC1|:
negative delta = improvement

For |runs z|:
negative delta = improvement

For Shannon entropy:
positive delta = improvement

These are statistical-quality descriptors, not proof that conditioning
has created cryptographic entropy.

---

# 28. Current conditioning local smoke status

Two Rule 30 pairs have currently been executed locally.

Current checker state:

Expected pairs:
150

Complete:
2

Missing:
148

Invalid:
0

Progress:
1.33%

The initial checker previously reported one invalid pair because an old
RAW result predated the addition of the "conditioning" field.

That pair was re-executed using --force.

After regeneration:

Invalid:
0

The issue is therefore resolved.

These two pairs are technical smoke tests only.

They are not used as final scientific evidence.

---

# 29. Preliminary conditioning smoke observation

For the small two-pair Rule 30 smoke sample:

median raw bias:
approximately 0.000150

median conditioned bias:
approximately 0.0001295

median delta bias:
approximately -0.0000205

median raw |AC1|:
approximately 0.001701

median conditioned |AC1|:
approximately 0.000701

median delta |AC1|:
approximately -0.001000

median raw |runs z|:
approximately 1.700

median conditioned |runs z|:
approximately 0.701

median delta |runs z|:
approximately -0.999

The sample size is only two pairs.

No scientific conclusion should be drawn from these values.

---

# 30. Standard cryptographic baseline

The standard lightweight cryptographic baseline selected for the project
is:

Ascon-AEAD128

Purpose:

provide a standardized lightweight authenticated-encryption mechanism
against which the selected published DNA-based image cipher can be
compared.

---

# 31. Ascon-AEAD128 reference validation

The pinned upstream Ascon reference implementation was compiled from:

third_party/ascon-c/crypto_aead/asconaead128/ref

The upstream interface reports:

CRYPTO_KEYBYTES = 16

CRYPTO_NPUBBYTES = 16

CRYPTO_ABYTES = 16

ASCON_AEAD_RATE = 16

Known Answer Test:

LWC_AEAD_KAT_128_128.txt

The generated KAT output was compared bit-for-bit with the official
reference KAT.

Result:

diff exit code = 0

This validates the exact pinned implementation before using it as the
project's baseline.

---

# 32. Ascon-AEAD128 wrapper

Implemented:

include/bioentropy/crypto/AsconAead128.hpp

src/crypto/AsconAead128.cpp

Interface supports:

encrypt(
    plaintext,
    associated_data,
    key,
    nonce
)

decrypt(
    ciphertext,
    associated_data,
    key,
    nonce
)

Constants:

Key:
16 bytes

Nonce:
16 bytes

Authentication tag:
16 bytes

---

# 33. Ascon-AEAD128 security-functionality tests

Implemented tests include:

- empty plaintext round-trip,
- short plaintext round-trip,
- block-boundary round-trip,
- 64-byte round-trip,
- 1024-byte round-trip,
- deterministic result for identical inputs,
- ciphertext tamper rejection,
- authentication-tag tamper rejection,
- associated-data tamper rejection,
- wrong-key rejection,
- wrong-nonce rejection.

All tests pass.

Current complete project test state after Ascon-AEAD128 integration:

10 / 10 tests passed.

---

# 34. Ascon-AEAD128 performance benchmark

## Status

DONE locally.

Benchmark implementation:

src/benchmark/benchmark_ascon_aead128.cpp

Analysis:

analysis/scripts/analyze_ascon_aead128_benchmark.py

---

## 34.1 Message sizes

Benchmarked plaintext sizes:

64 B

1 KiB

64 KiB

1 MiB

---

## 34.2 Measurement repetitions

For each message size:

20 measurement samples.

Iterations inside each sample are adjusted according to message size to
provide a sufficiently stable timing interval.

Examples:

64 B:
50,000 iterations per sample

1 KiB:
4096 iterations per sample

64 KiB:
64 iterations per sample

1 MiB:
4 iterations per sample

---

## 34.3 Benchmark metrics

Recorded:

- encrypt time per operation,
- decrypt time per operation,
- encrypt throughput,
- decrypt throughput,
- ciphertext bytes,
- ciphertext expansion bytes,
- ciphertext expansion percentage,
- ciphertext bit-level Shannon entropy,
- ciphertext byte-level Shannon entropy,
- plaintext-ciphertext Pearson correlation,
- decryption correctness.

The benchmark output contains:

80 measurements
+
1 header

=
81 TSV lines.

---

# 35. Preliminary Ascon-AEAD128 benchmark results

## 64 B

Median encryption throughput:

137.79 MiB/s

Median decryption throughput:

136.17 MiB/s

Median ciphertext byte entropy:

6.046928 bits/byte

Median plaintext-ciphertext correlation:

0.030217

Ciphertext expansion:

16 B

Relative expansion:

25%

The low byte-level entropy relative to 8 bits/byte is expected to be
strongly affected by the very small 80-byte ciphertext sample.

---

## 1 KiB

Median encryption throughput:

321.57 MiB/s

Median decryption throughput:

331.14 MiB/s

Median ciphertext byte entropy:

7.814298 bits/byte

Median plaintext-ciphertext correlation:

-0.007592

Ciphertext expansion:

16 B

Relative expansion:

1.5625%

---

## 64 KiB

Median encryption throughput:

376.02 MiB/s

Median decryption throughput:

393.29 MiB/s

Median ciphertext byte entropy:

7.997155 bits/byte

Median plaintext-ciphertext correlation:

0.000086

Ciphertext expansion:

16 B

Relative expansion:

0.0244140625%

---

## 1 MiB

Median encryption throughput:

350.52 MiB/s

Median decryption throughput:

374.48 MiB/s

Median ciphertext byte entropy:

7.999832 bits/byte

Median plaintext-ciphertext correlation:

0.000077

Ciphertext expansion:

16 B

Relative expansion:

0.00152587890625%

---

# 36. Interpretation of ciphertext statistics

Ciphertext entropy and plaintext-ciphertext correlation are treated only
as descriptive measurements.

For large samples:

byte entropy approaching 8 bits/byte

and:

plaintext-ciphertext correlation approaching zero

are expected properties of a well-behaved ciphertext stream.

However, neither property is independently sufficient to establish
cryptographic security.

---

# 37. Ascon-AEAD128 avalanche experiment

## Status

DONE locally.

The avalanche experiment has been implemented but has not yet been
committed at the time of writing this log entry.

Implementation:

src/benchmark/benchmark_ascon_aead128_avalanche.cpp

Analysis:

analysis/scripts/analyze_ascon_aead128_avalanche.py

---

## 37.1 Avalanche experiment design

Tested message sizes:

64 B

1 KiB

64 KiB

1 MiB

For each message size:

100 one-bit plaintext perturbation trials.

For every trial:

1. a baseline plaintext is created,
2. one exact plaintext bit is flipped,
3. key remains unchanged,
4. nonce remains unchanged,
5. associated data remains unchanged,
6. plaintext is encrypted again,
7. Hamming distance is calculated.

Hamming distance is calculated separately for:

- ciphertext payload,
- authentication tag,
- complete ciphertext.

---

## 37.2 Why payload and tag are analysed separately

A single plaintext bit change in an authenticated stream-oriented
construction must not be interpreted exactly like the avalanche
criterion of a conventional block cipher.

The authentication tag is a particularly useful diffusion measurement.

Therefore the analysis reports:

- payload change percentage,
- tag change percentage,
- total ciphertext change percentage.

---

# 38. Ascon-AEAD128 avalanche results

The experiment produced:

400 trial rows
+
1 header

=
401 TSV lines.

---

## 64 B

Median complete ciphertext change:

25.3125%

Median payload change:

18.7500%

Median authentication-tag change:

50.00%

Median changed authentication-tag bits:

64 / 128

---

## 1 KiB

Median complete ciphertext change:

25.1322%

Median payload change:

24.7498%

Median authentication-tag change:

50.00%

Median changed authentication-tag bits:

64 / 128

---

## 64 KiB

Median complete ciphertext change:

25.2764%

Median payload change:

25.2706%

Median authentication-tag change:

50.00%

Median changed authentication-tag bits:

64 / 128

---

## 1 MiB

Median complete ciphertext change:

25.2476%

Median payload change:

25.2472%

Median authentication-tag change:

50.00%

Median changed authentication-tag bits:

64 / 128

---

## 38.1 Avalanche interpretation

The authentication-tag behavior is highly consistent across all tested
message sizes:

median changed bits:

64 / 128

median percentage:

50%

The approximately 25% whole-ciphertext change is not interpreted as a
failure of an expected 50% block-cipher avalanche criterion.

The payload and tag are reported separately specifically to avoid that
incorrect interpretation.

---

# 39. Cryptographic comparison design

The reduced crypto comparison consists of:

1. Ascon-AEAD128
2. one published DNA-based cipher

Removed from the reduced crypto scope:

- AES-GCM,
- ChaCha20-Poly1305,
- DNA + ECC variants,
- multiple DNA cipher families.

ChaCha20 remains in the project only as a deterministic PRG reference
for the source-analysis stage.

---

# 40. Published DNA-based cipher comparator

## Status

SELECTED.

Full reproduction has NOT yet been implemented.

The next implementation stage will start from the published algorithm.

---

## 40.1 Selected publication

Qiang Zhang

Xianglian Xue

Xiaopeng Wei

**A Novel Image Encryption Algorithm Based on DNA Subsequence Operation**

The Scientific World Journal

2012

Article ID:

286741

DOI:

10.1100/2012/286741

---

## 40.2 Reason for selecting this publication

The project requires a single published DNA-based cryptographic
mechanism that can be reproduced and compared with Ascon-AEAD128.

This publication was selected because:

- the complete paper is openly accessible,
- it provides an explicit image-encryption algorithm,
- it uses DNA subsequence operations,
- it combines DNA operations with chaotic-map-based control,
- it includes both encryption and decryption,
- it provides cryptographic image-analysis metrics,
- it is sufficiently explicit to attempt reproducible implementation,
- the authors themselves discuss weaknesses against differential attack.

The algorithm is therefore not selected because it is assumed secure.

It is selected because it provides a concrete published DNA-based
comparator.

---

# 41. Important separation between the two DNA uses

The project contains TWO conceptually different uses of DNA.

They must never be confused.

---

## 41.1 DNA as deterministic source data

Used in the entropy / randomness source evaluation.

Mapping:

A = 00

C = 01

G = 10

T = 11

Purpose:

convert genomic sequence data into deterministic bitstreams for
statistical evaluation.

---

## 41.2 DNA encoding inside the Zhang et al. 2012 cipher

The selected publication uses a different DNA encoding.

Published cipher mapping:

00 → G

01 → A

10 → T

11 → C

Purpose:

internal representation used by the published image encryption
algorithm.

This mapping is reproduced because it belongs to the published
construction.

It must not replace the genomic-source mapping used elsewhere in the
project.

---

# 42. Published DNA-cipher example

The paper provides an explicit example:

decimal value:

75

binary:

01001011

DNA representation:

A G T C

Using the paper's mapping:

01 → A

00 → G

10 → T

11 → C

This example will be used as a unit-test anchor in the implementation.

---

# 43. Watson-Crick complement in the published cipher

The reproduction will use:

A ↔ T

C ↔ G

These operations belong specifically to the published DNA-based cipher
implementation.

---

# 44. Chaotic mechanism in the published DNA cipher

The paper uses both:

- a two-dimensional Logistic system,
- four one-dimensional Logistic sequences.

The 2D system is used before deriving parameters used by later stages
of the cipher.

The reported 2D form is:

x[i+1] =
    mu1 * x[i] * (1 - x[i])
    + gamma1 * y[i]^2

y[i+1] =
    mu2 * y[i] * (1 - y[i])
    + gamma2 * (
        x[i]^2
        + x[i] * y[i]
    )

The paper's experimental parameters include:

x0:
0.95

mu1:
3.2

gamma1:
0.17

y0:
0.25

mu2:
3.3

gamma2:
0.14

The publication uses a 1000-step 2D Logistic warm-up before deriving
parameters for four subsequent Logistic sequences.

---

# 45. Published DNA subsequence lengths

The selected algorithm uses four nominal DNA subsequence lengths:

l1 = 128

l2 = 64

l3 = 32

l4 = 8

These will be reproduced explicitly rather than substituted with
different values.

---

# 46. Published DNA-cipher operations

The encryption construction described by the paper includes operations
such as:

- DNA encoding,
- deletion,
- elongation,
- truncation,
- transformation,
- complement,
- DNA decoding,
- bit-plane processing,
- bit-plane recombination.

The inverse decryption process includes the appropriate inverse
operations, including insertion.

---

# 47. Reproduction policy for ambiguous publication details

The selected publication contains notation and description ambiguities.

The project will not silently invent missing details.

Every ambiguity will be recorded explicitly.

Examples already identified include:

- gamma1 and gamma2 appear fixed in some parts of the description but
  participate differently in the key-space discussion,
- one experimental parameter listing appears to repeat the symbol mu1,
  with the second value interpreted from context as mu2,
- extraction of values after the 1000-step 2D Logistic sequence must be
  documented precisely before the full cipher implementation is
  considered reproducible.

Any implementation interpretation introduced because of publication
ambiguity must be documented.

---

# 48. DNA cipher implementation status at this exact point

At the time of this log entry:

DONE:

- publication selected,
- reason for selection established,
- paper-specific DNA encoding identified,
- Watson-Crick complement identified,
- 2D Logistic equations identified,
- experimental parameters identified,
- subsequence lengths identified,
- major algorithmic operations identified.

NOT YET DONE:

- C++ DNA primitive implementation,
- DNA encoding unit tests,
- 2D Logistic unit tests,
- 1000-step warm-up implementation,
- four Logistic sequence derivation,
- DNA subsequence partitioning,
- deletion implementation,
- insertion implementation,
- transformation implementation,
- elongation/truncation implementation,
- full encryption,
- full decryption,
- image workload integration,
- NPCR evaluation,
- UACI evaluation,
- DNA-cipher performance benchmark.

No unimplemented stage should be represented as completed.

---

# 49. Planned image workloads

The reduced project plan uses:

10 natural images

and four synthetic images:

- black,
- white,
- checkerboard,
- gradient.

The synthetic images are included to test behavior on intentionally
low-complexity and highly structured plaintexts.

---

# 50. Planned image metrics

For the DNA-based image cipher:

- encryption time,
- decryption time,
- throughput,
- ciphertext / encrypted-image entropy,
- plaintext-ciphertext correlation,
- avalanche-related behavior,
- NPCR,
- UACI.

NPCR and UACI are intended primarily for the image-cipher comparator.

They are not treated as universal security proofs.

---

# 51. Standard message-size benchmark design

For standard cryptographic benchmarking:

64 B

1 KiB

64 KiB

1 MiB

This has already been implemented for Ascon-AEAD128.

Where scientifically meaningful, the same sizes or directly comparable
workloads will be used for the DNA-based cipher.

---

# 52. Repository and development environment

Primary development environment:

Windows host

with:

WSL2 Ubuntu

and:

Visual Studio Code

Repository:

~/bioentropy-hpc

Windows-visible path:

/home/weronika/bioentropy-hpc

Language:

C++20

Compiler:

GCC 13.3

Build system:

CMake + Ninja

Libraries / dependencies include:

- OpenSSL,
- yaml-cpp,
- nlohmann-json,
- upstream Ascon C reference implementation.

Python environment:

.venv

Important Python packages include:

- pandas,
- pyarrow.

---

# 53. GitHub repository

Repository:

weronikawolak/bioentropy-hpc

Visibility:

private

Remote:

origin

Transport:

HTTPS

Development branch currently used for this work:

feat/ascon-conditioning

---

# 54. Selected Git milestones

Relevant known commits include:

935c9f5

main merge containing source-comparison analysis milestone.

---

ac6add7

build: add reference Ascon implementation

This added the upstream Ascon dependency as a pinned Git submodule.

---

5c565e2

feat: add conditioning experiment pipeline

Added:

- conditioning campaign generator,
- conditioning local runner,
- conditioning smoke test,
- conditioning checker,
- conditioning-effect analysis.

---

df3f8f5

feat: add Ascon-AEAD128 crypto baseline

Added:

- Ascon-AEAD128 wrapper,
- reference implementation integration,
- AEAD tests.

---

7b4e5fe

feat: add Ascon-AEAD128 performance benchmark

Added:

- performance benchmark,
- benchmark analysis.

---

The avalanche benchmark exists locally at the time of this log entry but
has not yet been committed.

---

# 55. Current project test state

Current CTest result:

10 / 10 tests passed

0 failed.

The current tests cover:

- SeedManager,
- Logistic Map source,
- basic bitstream statistics,
- Cellular Automaton source,
- ChaCha20 reference source,
- DNA sequence source,
- serial bitstream metrics,
- Ascon-XOF128 conditioner,
- conditioning experiment configuration,
- Ascon-AEAD128.

The future DNA-cipher primitive test is expected to become test number
11 once implemented.

---

# 56. Removed / intentionally postponed scope

The following items were removed or postponed to preserve quality and
feasibility:

- hyperchaotic source family,
- MPFR implementation,
- broad fixed-point study,
- Dieharder,
- BigCrush on every configuration,
- multiple DNA ciphers,
- DNA + ECC,
- AES-GCM baseline,
- ChaCha20-Poly1305 baseline,
- MPI implementation,
- GPU implementation,
- CUDA implementation,
- exhaustive strong-scaling analysis,
- exhaustive weak-scaling analysis,
- unnecessarily complex statistical models.

A limited float32 vs float64 sensitivity analysis may still be added if
it becomes scientifically useful.

---

# 57. Current conceptual experiment structure

The current project can be summarized as:

SOURCE LAYER

Logistic
Rule 30
Rule 90
DNA
ChaCha20 reference

↓

SOURCE STATISTICS

bias
Shannon entropy
AC1
runs
longest run
SHA-256
later:
SP800-90B
NIST STS
TestU01

↓

CONDITIONING

RAW
vs
Ascon-XOF128

↓

CONDITIONING EFFECT

change in statistical quality

↓

CRYPTOGRAPHIC COMPARISON

Ascon-AEAD128
vs
published Zhang et al. 2012 DNA-based cipher

↓

CRYPTOGRAPHIC / PERFORMANCE METRICS

encrypt time
decrypt time
throughput
ciphertext expansion
ciphertext entropy
plaintext-ciphertext correlation
avalanche / diffusion
NPCR
UACI

↓

HPC

large-scale execution
campaign throughput
parallel scaling

---

# 58. Current scientific contribution target

The intended contribution is not the invention of a new cryptographic
primitive.

The contribution is the systematic evaluation of the relationship
between:

- candidate-source statistical properties,
- conditioning,
- and downstream lightweight cryptographic behavior.

The project is designed to test whether apparently good statistical
source properties are meaningfully reflected in downstream
cryptographic measurements.

A particularly important comparison is expected between:

- raw deterministic candidate sources,
- conditioned versions,
- cryptographic reference streams.

---

# 59. Current project state at the time of this entry

Completed locally:

- deterministic source framework,
- SeedManager,
- Logistic Map implementation,
- CA Rule 30,
- CA Rule 90,
- ChaCha20 reference PRG,
- DNA sequence source,
- source metrics,
- result persistence,
- screening campaign generator,
- SLURM screening infrastructure,
- DNA dataset preparation,
- DNA source campaign,
- source-analysis scripts,
- Ascon upstream dependency,
- Ascon-XOF128 conditioner,
- RAW/Ascon conditioning configuration,
- paired conditioning pipeline,
- conditioning checker,
- conditioning analysis,
- Ascon-AEAD128 wrapper,
- Ascon-AEAD128 KAT validation,
- Ascon-AEAD128 integrity tests,
- Ascon-AEAD128 performance benchmark,
- Ascon-AEAD128 avalanche benchmark.

Partially executed:

- screening campaign,
- conditioning campaign.

Selected but not implemented:

- Zhang et al. 2012 DNA-based image cipher.

Not yet executed at full scale:

- HPC screening,
- full conditioning campaign,
- SP800-90B,
- NIST STS,
- TestU01 campaign,
- final Logistic representative selection,
- final statistical inference,
- crypto comparison with DNA cipher,
- image-cipher NPCR/UACI campaign,
- final HPC scaling experiments.

---

# DNA-based cipher reproduction — primitive implementation

## Status

DONE locally.

The first implementation stage of the selected Zhang, Xue & Wei
(2012) DNA subsequence image cipher has been completed.

This stage intentionally implements only algorithmic primitives that
are explicitly defined by the publication.

The full image encryption and decryption procedures have not yet been
implemented.

## Implemented components

Implemented:

- paper-specific two-bit DNA encoding,
- DNA decoding,
- Watson-Crick complement,
- one-dimensional Logistic Map step,
- two-dimensional Logistic Map step.

Files:

include/bioentropy/crypto/DnaSubsequenceCipher2012.hpp

src/crypto/DnaSubsequenceCipher2012.cpp

tests/test_dna_subsequence_cipher_2012.cpp

## Paper-specific DNA mapping

The reproduced cipher uses:

00 -> G
01 -> A
10 -> T
11 -> C

This mapping is specific to the Zhang et al. 2012 cipher.

It remains separate from the genomic-source mapping used in the
randomness-source experiments:

A = 00
C = 01
G = 10
T = 11

## Published validation example

The publication gives the example:

75 decimal
= 01001011 binary
= A G T C

This example is used directly as a unit-test anchor.

## Exhaustive encoding validation

All possible 8-bit values from 0 through 255 are tested using:

byte
-> DNA encoding
-> DNA decoding
-> original byte

All round trips must reproduce the original byte exactly.

## Watson-Crick complement

The implementation follows:

A <-> T

C <-> G

## Logistic maps

The one-dimensional Logistic step is:

x[n+1] =
    mu * x[n] * (1 - x[n])

The two-dimensional system is implemented using the equations
reported in the selected publication.

The default experimental parameters currently represented by the
reproduction key structure are:

x0 = 0.95
mu1 = 3.2
gamma1 = 0.17

y0 = 0.25
mu2 = 3.3
gamma2 = 0.14

## Validation status

The primitive implementation is tested independently before any
higher-level DNA subsequence operations are added.

The next reproduction stage will implement:

- the 1000-step two-dimensional Logistic warm-up,
- extraction of values used to derive four one-dimensional
  Logistic Maps,
- generation of the four Logistic sequences.

Any ambiguity in the publication's extraction procedure will be
documented explicitly before it is incorporated into the full cipher.

---

# DNA-based cipher reproduction — primitive implementation

## Status

DONE locally.

The first implementation stage of the Zhang, Xue & Wei (2012)
DNA subsequence image cipher has been completed.

Implemented components:

- paper-specific DNA encoding and decoding,
- Watson-Crick complement,
- one-dimensional Logistic Map step,
- two-dimensional Logistic Map step.

The cipher-specific DNA mapping reproduced from the publication is:

- 00 -> G
- 01 -> A
- 10 -> T
- 11 -> C

This mapping remains separate from the genomic-source mapping used
elsewhere in the project.

The publication example:

75 decimal = 01001011 binary = AGTC

is used as a direct unit-test anchor.

BioEntropy HPC additionally verifies exact DNA encode/decode round-trip
for all 256 possible byte values.

The Logistic-map equations are reproduced from the selected
publication, while the C++ class structure and exhaustive unit-testing
approach are project-specific implementation choices.

The full DNA-based image cipher is not yet implemented.

The next stage is:

1000-step 2D Logistic warm-up
-> extraction of x1...x8
-> derivation of four 1D Logistic Maps.

Any ambiguity in the publication's extraction procedure will be
documented before implementing that stage.

---

# DNA-based cipher comparator selection revised

The initial plan to reproduce Zhang, Xue & Wei (2012) was reconsidered
before the complete cipher implementation was committed.

The primary DNA-based lightweight cipher comparator is now:

Marwan A. Fetteha,
Wafaa S. Sayed,
Lobna A. Said,

"A Lightweight Image Encryption Scheme Using DNA Coding and Chaos",

Electronics, 2023, 12(24), 4895.

DOI: 10.3390/electronics12244895

The Zhang et al. 2012 publication remains relevant as earlier Related
Work but is no longer the implementation target.

The change was made because the 2023 construction is substantially
better aligned with the BioEntropy HPC research scope.

In particular, the Fetteha et al. scheme explicitly targets lightweight
image encryption and includes:

- DNA coding,
- deterministic chaos,
- a 256-bit key,
- grayscale-image encryption,
- image-dependent diffusion,
- NPCR/UACI evaluation,
- entropy and correlation evaluation,
- NIST SP 800-22 evaluation,
- hardware-oriented implementation,
- FPGA resource and throughput measurements.

The paper therefore provides a more appropriate contemporary comparator
for Ascon-AEAD128 than the originally selected 2012 construction.

No complete Zhang et al. cipher implementation was committed before
this decision was made.

---

# Fetteha et al. 2023 comparator — core implementation

The first implementation milestone of the selected contemporary
DNA-based lightweight image cipher has been completed.

Implemented:

- image pixel summation,
- P = pixel_sum mod 16,
- deterministic 256-bit key representation,
- split of the key into eight 32-bit words,
- XOR derivation of raw X0, Y0 and Z0 values,
- Euler-discretized Lorenz system step.

The Lorenz implementation uses the parameters reported by
Fetteha et al. 2023:

h = 2^-7
sigma = 8
rho = 16
beta = 2

The implementation has been integrated into the existing C++ test
suite without regression of the previously implemented components.

The next milestone is exact reproduction of the eight DNA encoding
and decoding rules from Table 1 of the publication.

---

# Fetteha 2023 — Lorenz-to-DNA control bridge

The chaotic-control bridge from Fetteha et al. 2023 Algorithm 1 has
been reproduced.

Implemented:

- 200-output Lorenz warm-up/discard,
- extraction of the first usable chaotic state,
- Xbin1...Xbin4,
- Ybin1...Ybin4,
- Zbin,
- MATLAB-compatible fix() and mod() behavior.

This stage connects the Lorenz PRNG with the dynamic DNA rule selection.

The implementation explicitly supports negative Lorenz values when
reproducing MATLAB mod(..., 8) semantics.

The full encryption routine remains intentionally deferred because two
publication-level issues still require an explicit reproduction policy:

- mapping the XOR-derived 32-bit initial-condition words into the
  numerical Lorenz state,
- interpretation of the P decrement / outer encryption iteration.

These ambiguities will be resolved before implementing the complete
encrypt/decrypt pipeline.

---

# Fetteha 2023 — DNA control and pixel pipeline milestone

The software reproduction now includes the unambiguous low-level
components of the Fetteha, Sayed & Said (2023) cipher:

- Lorenz Euler step,
- 200-state chaotic warm-up,
- Xbin1...Xbin4 extraction,
- Ybin1...Ybin4 extraction,
- Zbin extraction,
- all eight DNA coding rules,
- dynamic DNA encode/decode transformation,
- 8-bit pixel split and reconstruction,
- XOR diffusion,
- previous-ciphertext feedback,
- normal and reversed pixel traversal.

The implementation reproduces MATLAB-compatible fix() and mod()
semantics where required by Algorithm 1.

All project tests currently pass.

The remaining distinction is between:

1. the publication-defined cipher logic, and
2. the unspecified numerical interpretation of the 32-bit XOR-derived
   Lorenz initial-condition words.

The second item will remain isolated rather than being silently guessed.

---

# Fetteha 2023 — full-pass orchestration profile

A complete P-controlled image-pass orchestration has been implemented
on top of the previously validated pixel pipeline.

The reproduction profile interprets:

P = sum(original_plaintext_pixels) mod 16

as the number of complete image-encryption passes.

For each pass:

- the Lorenz trajectory starts from the supplied initial state,
- the first 200 chaotic states are discarded,
- one DNA control tuple is generated per pixel,
- even P uses normal pixel order,
- odd P uses reversed pixel order,
- feedback mask starts at zero,
- the pass output becomes the next pass input,
- P is decremented after the complete image pass.

A later consistency check against the publication's reported
all-black and all-white experiments showed that raw P=0 cannot
represent zero effective passes. The reproduction profile was therefore
revised: raw P=0 is interpreted as 16 effective image passes.

This control-flow interpretation is explicitly documented as a
reproduction profile because the prose and pseudocode of the source
publication are not completely consistent.

The remaining unresolved publication detail is the numerical mapping
of the XOR-derived 32-bit X0/Y0/Z0 words into Lorenz coordinates.

---

# Fetteha 2023 — key-to-Lorenz mapping sensitivity

The publication defines the raw 32-bit XOR expressions used to derive
X0, Y0 and Z0, but does not specify their numerical representation as
Lorenz coordinates.

A deterministic sensitivity experiment was performed over 1000
synthetic 256-bit keys.

Each candidate mapping was evaluated for:

- 200 discarded Lorenz states,
- 1024 subsequent states,
- finite numerical behavior,
- maximum trajectory magnitude.

Observed stable fractions:

u32_unit   : 1000 / 1000
u32_q28    : 1000 / 1000
s32_q28    : 1000 / 1000
s32_q27    : 1000 / 1000
s32_q26    : 1000 / 1000
s32_q24    :  211 / 1000
s32_q16    :    0 / 1000

The primary reproduction profile was selected as:

signed 32-bit two's-complement value * 2^-26

giving an initial numerical interval of approximately:

[-32, 32).

This choice is explicitly a BioEntropy HPC reproduction profile and is
not claimed to reproduce an undocumented original FPGA Q-format.

The sensitivity analysis is retained so alternative mappings can be
re-evaluated without changing the publication-derived cipher logic.

---

# Fetteha 2023 — synthetic differential sensitivity probe

A targeted differential experiment was performed on four deterministic
256x256 grayscale workloads:

- black,
- white,
- checkerboard,
- horizontal gradient.

For every workload, 50 deterministic single-pixel modifications were
evaluated under two perturbation modes.

Mode 1:

single_pixel_plus1

changes one pixel by one intensity level and therefore changes:

P = sum(image) mod 16.

Mode 2:

single_pixel_preserve_p

changes one pixel by exactly 16 intensity levels and therefore preserves
P.

All four baseline synthetic images had:

raw P = 0

which corresponds to:

16 effective encryption passes

under the documented reproduction profile.

The +1 perturbation changed raw P to:

1

and therefore changed the effective number of passes from:

16 -> 1.

## Results

Publication-style +1 perturbation:

black:
NPCR = 99.606934%
UACI = 33.500584%

checkerboard:
NPCR = 99.606110%
UACI = 33.526465%

gradient:
NPCR = 99.609894%
UACI = 33.676908%

white:
NPCR = 99.593658%
UACI = 33.636638%

These values are very close to the commonly reported reference values:

NPCR ~ 99.61%
UACI ~ 33.46%.

However, when P was deliberately preserved:

black:
NPCR = 63.944366%
UACI = 7.147815%

checkerboard:
NPCR = 63.944366%
UACI = 7.147815%

gradient:
NPCR = 52.174591%
UACI = 9.554864%

white:
NPCR = 63.944366%
UACI = 7.147815%

## Interpretation

This preliminary experiment indicates that the excellent NPCR/UACI
observed under the conventional one-pixel perturbation may be strongly
confounded by the image-dependent P parameter.

The +1 experiment does not isolate propagation of a one-pixel
difference through an otherwise identical cipher execution.

It simultaneously changes:

1. the plaintext pixel,
2. raw P,
3. the number of complete encryption passes,
4. the sequence of normal/reversed pass orientations.

The P-preserving perturbation keeps the cipher-control path comparable
and produces substantially lower differential metrics.

This is a preliminary diagnostic result and is not yet treated as a
general cryptanalytic conclusion.

A follow-up experiment must cover all raw P values 0...15 before
drawing stronger conclusions.

---

# Fetteha 2023 — P-confounding differential campaign

A systematic follow-up differential campaign evaluated all possible raw
P classes:

P = 0 ... 15.

For every P class:

- one deterministic 256x256 grayscale image was generated,
- the image was adjusted so pixel_sum mod 16 matched the target P,
- 50 deterministic perturbation locations were evaluated,
- two perturbation modes were compared.

Total differential comparisons:

16 P classes
x 50 trials
x 2 perturbation modes
= 1600.

## Change-P condition

A single pixel was changed by +1 modulo 256.

This changes:

raw P -> (raw P + 1) mod 16.

Across all 16 P classes, mean differential metrics were approximately:

NPCR = 99.6160%
UACI = 33.4759%.

These values closely match the conventional reference values:

NPCR ~ 99.61%
UACI ~ 33.46%.

The behavior was highly consistent across P classes.

## Preserve-P condition

A single pixel was changed by +/-16.

This changes the plaintext while preserving:

pixel_sum mod 16

and therefore preserves P and the number of effective image passes.

Across all P classes, mean differential metrics were approximately:

NPCR = 56.3743%
UACI = 10.2036%.

Observed P-preserving NPCR ranged approximately from:

40.61% to 67.71%.

Observed P-preserving UACI ranged approximately from:

8.58% to 12.94%.

## Contrast

Mean change-P minus preserve-P differences were approximately:

NPCR:
+43.24 percentage points

UACI:
+23.27 percentage points.

The direction of the effect was consistent across all 16 P classes.

## Interpretation

The experiment provides strong evidence that the image-dependent P
parameter substantially confounds conventional NPCR/UACI measurements.

Changing one plaintext pixel by one intensity level simultaneously
changes:

- the plaintext,
- raw P,
- the effective pass count and/or pass index,
- the sequence of normal/reversed full-image passes.

Consequently, the conventional perturbation does not isolate diffusion
of the plaintext difference through an otherwise unchanged cipher
execution.

When P was preserved, differential propagation was substantially
weaker.

## Current limitation

The two perturbation modes are not perfectly magnitude-matched.

The change-P condition modifies one pixel by one level.

The current preserve-P condition modifies one pixel by sixteen levels.

Therefore one additional matched-magnitude control experiment is
required before treating the P-confounding result as a final
cryptanalytic conclusion.

The next experiment will preserve P using two small +/-1 pixel changes.

---

# Fetteha 2023 — matched-magnitude P-control experiment

A matched-magnitude differential control experiment was performed to
remove the main limitation of the earlier P-preserving test.

The campaign covered:

- all raw P values from 0 through 15,
- 50 deterministic trials per P class,
- 1600 total differential comparisons.

Two perturbation modes were compared.

## Change-P condition

One plaintext pixel was changed by:

+1

This changes:

raw P -> (raw P + 1) mod 16

and therefore changes the cipher execution path.

Across all trials:

NPCR = 99.616190%
UACI = 33.476177%.

These results closely match conventional reference values:

NPCR ~ 99.61%
UACI ~ 33.46%.

## Matched P-preserving condition

The same primary plaintext pixel was changed by:

+1

and a second plaintext pixel was changed by:

-1.

Therefore:

total pixel-sum change = 0

and raw P remains unchanged.

Each individual plaintext modification has magnitude one.

Across all trials:

NPCR = 66.302910%
UACI = 1.623252%.

## Interpretation

The large differential-security contrast remains after replacing the
earlier +/-16 P-preserving perturbation with minimal +/-1 changes.

The change-P condition produces near-reference NPCR/UACI values across
all P classes.

The P-preserving condition produces substantially lower differential
metrics despite modifying two plaintext pixels rather than one.

This strongly supports the interpretation that the image-dependent P
parameter materially confounds conventional differential sensitivity
measurements.

The conventional one-pixel +1 test changes not only the plaintext but
also the cipher execution path through P.

Therefore its NPCR/UACI results cannot be interpreted purely as
diffusion of a small plaintext difference through an otherwise
identical encryption process.

This is treated as a strong diagnostic finding for the reproduced
Fetteha 2023 construction.

It is not presented as a proof of complete cryptographic insecurity.

---

# Fetteha 2023 — performance dependence on P

The reproduced Fetteha cipher was benchmarked on deterministic
256x256 grayscale images:

65536 bytes per image.

All raw P classes from 0 through 15 were evaluated.

The reproduction profile maps:

raw P = 0 -> 16 effective passes.

For each P class:

- 5 warm-up encrypt/decrypt cycles were executed,
- 31 measured repetitions were collected,
- median encryption and decryption times were reported,
- every measured execution was verified by a successful round trip.

## Main observation

Runtime is strongly dependent on the effective P value.

Encryption:

P=1:
~12.87 ms
~4.86 MiB/s

P=16:
~62.57 ms
~1.00 MiB/s.

Thus the P=16 encryption case is approximately 4.86 times slower than
P=1.

Decryption showed a comparable pattern.

## Linear cost model

A linear regression against effective pass count gave approximately:

encryption:
time_us = 9889.6 + 3172.2 * effective_passes
R^2 = 0.9952

decryption:
time_us = 9807.0 + 3155.2 * effective_passes
R^2 = 0.9938.

This indicates an approximately linear incremental cost per additional
image pass, combined with a substantial fixed per-image cost.

The fixed component includes operations such as key-derived chaotic
state preparation and control-sequence generation.

Therefore total runtime is not proportional to P alone.

The previously reported per-pass values are interpreted only as
amortized total-time-per-pass quantities and not as isolated
measurements of an individual pass.

## Security/performance implication

Because P depends on the plaintext:

P = sum(image) mod 16,

small plaintext modifications may alter both:

- the cipher execution path,
- computational cost.

Under the documented reproduction profile, the most extreme observed
transition is:

raw P 0 -> 1

corresponding to:

16 effective passes -> 1 effective pass.

This connects the previously observed P-dependent differential behavior
with a substantial plaintext-dependent performance variation.

---

# Ascon-AEAD128 vs Fetteha 2023 — common 64 KiB benchmark

A common benchmark harness was implemented to compare Ascon-AEAD128
and the reproduced Fetteha 2023 image cipher under the same timing
environment.

Payload size:

65536 bytes

corresponding to a 256x256 grayscale image.

Both algorithms were measured in the same executable using:

- the same plaintext fixture,
- the same steady clock,
- 5 warm-up iterations,
- 31 measured repetitions,
- median execution time,
- alternating benchmark order,
- verified encrypt/decrypt round trips.

Three representative Fetteha execution paths were evaluated:

raw P=1  -> 1 effective pass
raw P=8  -> 8 effective passes
raw P=0  -> 16 effective passes

## Encryption results

P=1:

Ascon-AEAD128:
~151 us
~413.9 MiB/s

Fetteha:
~13.92 ms
~4.49 MiB/s

Fetteha slowdown:
~92.2x

P=8:

Ascon-AEAD128:
~151 us
~413.6 MiB/s

Fetteha:
~36.05 ms
~1.73 MiB/s

Fetteha slowdown:
~238.6x

P=16:

Ascon-AEAD128:
~143 us
~436.8 MiB/s

Fetteha:
~61.89 ms
~1.01 MiB/s

Fetteha slowdown:
~432.5x

## Decryption

The same overall behavior was observed during decryption.

Approximate Fetteha slowdowns relative to Ascon were:

P=1:
~91.7x

P=8:
~244.6x

P=16:
~421.0x

## Ciphertext expansion

Ascon-AEAD128 produced:

65552 bytes

for a 65536-byte plaintext because the implementation includes the
16-byte authentication tag.

The Fetteha comparator produced:

65536 bytes

and therefore no ciphertext expansion.

This size comparison must not be interpreted as equivalent security
functionality.

Ascon-AEAD128 provides authenticated encryption, including integrity
and authenticity through its authentication tag.

The reproduced Fetteha construction does not provide an equivalent
AEAD authentication property.

## Interpretation

The standardized authenticated-encryption baseline substantially
outperformed the reproduced DNA/chaos comparator even though Ascon
provides a stronger security interface.

The Fetteha runtime additionally depends strongly on the
plaintext-derived P parameter.

Therefore the performance gap is itself plaintext dependent:

approximately 92x at one effective pass

to

approximately 432x at sixteen effective passes.

These measurements are software measurements from the BioEntropy HPC
reference environment and must not be compared directly with the FPGA
throughput reported by Fetteha et al.

---

# Paired RAW vs Ascon-XOF128 local end-to-end smoke

A final local paired-conditioning smoke experiment was completed before
the full HPC campaign.

Five source families were evaluated:

- Logistic Map,
- CA Rule30,
- CA Rule90 negative control,
- public DNA sequence,
- ChaCha20 deterministic cryptographic reference.

Each source was evaluated twice:

- RAW,
- Ascon-XOF128 conditioned.

For every pair, the source configuration, seed, replicate identifier,
parameters and requested source output were identical.

The validator additionally verified:

RAW bitstream SHA-256
==
Ascon-XOF128 pre-conditioning input SHA-256.

Therefore every RAW/XOF comparison used exactly the same source stream.

The conditioned output length was preserved.

## Local smoke results

### Logistic Map

RAW:

- bias: ~0.000391
- Shannon entropy: ~0.99999956 bits/bit
- lag-1 autocorrelation: ~-0.000942
- runs z-score: ~0.941
- longest run: 21

Ascon-XOF128:

- bias: ~0.000538
- Shannon entropy: ~0.99999916 bits/bit
- lag-1 autocorrelation: ~0.000572
- runs z-score: ~-0.573
- longest run: 20

The selected smoke stream already showed near-random basic statistics.
Conditioning therefore produced no systematic improvement visible from
this single smoke replicate.

### CA Rule30

RAW:

- bias: ~0.000427
- Shannon entropy: ~0.99999947 bits/bit
- lag-1 autocorrelation: ~-0.001290
- runs z-score: ~1.289
- longest run: 19

Ascon-XOF128:

- bias: ~0.000442
- Shannon entropy: ~0.99999944 bits/bit
- lag-1 autocorrelation: ~-0.000244
- runs z-score: ~0.243
- longest run: 19

Rule30 also displayed near-random basic statistics before conditioning
in this smoke replicate.

### CA Rule90 negative control

RAW:

- bias: ~0.483612
- Shannon entropy: ~0.120649 bits/bit
- lag-1 autocorrelation: ~0.498447
- runs z-score: ~-498.47
- longest run: 967488

Ascon-XOF128:

- bias: ~0.000650
- Shannon entropy: ~0.999999 bits/bit
- lag-1 autocorrelation: ~-0.000737
- runs z-score: ~0.736
- longest run: 22

This is the most important local conditioning sanity check.

The deterministic Rule90 source has severe visible statistical defects,
yet its Ascon-XOF128 output exhibits near-random values for the basic
metrics considered here.

This demonstrates that post-conditioning statistical quality must not
be interpreted as evidence that additional source entropy has been
created.

### Public DNA sequence

The final DNA smoke used a real 400000-nucleotide reference window,
mapped to 800000 output bits.

RAW:

- bias: ~0.001406
- Shannon entropy: ~0.99999429 bits/bit
- lag-1 autocorrelation: ~0.023226
- runs z-score: ~-20.775
- longest run: 19

Ascon-XOF128:

- bias: ~0.000400
- Shannon entropy: ~0.99999954 bits/bit
- lag-1 autocorrelation: ~0.001078
- runs z-score: ~-0.965
- longest run: 18

The DNA stream is particularly informative because its single-bit
Shannon entropy is already close to the theoretical maximum while its
serial metrics reveal substantial non-random structure.

This directly illustrates why Shannon entropy alone is insufficient for
evaluating candidate randomness sources.

Ascon-XOF128 strongly reduced the visible serial defects.

This improvement must be interpreted as conditioning of observable
statistical structure, not creation of physical entropy.

### ChaCha20 reference

RAW and conditioned ChaCha20 outputs both exhibited near-random basic
statistics.

This behavior is consistent with its role as a deterministic
cryptographic-reference generator rather than an entropy source.

## Interpretation and scope

This experiment is a local end-to-end validation, not the final
statistical campaign.

Only one representative stream per source family was evaluated.

The smoke demonstrates that:

1. paired RAW/XOF execution is reproducible,
2. source provenance is preserved,
3. output length is preserved,
4. basic statistics are computed on the intended stream,
5. strong source defects can be hidden by conditioning,
6. high Shannon entropy alone does not imply absence of serial
   structure.

Final quantitative conclusions will be based on the full replicated
HPC campaign and subsequent deep statistical testing.

## Logistic Map numerical precision and exact digital periodicity

### Motivation

A dedicated numerical-representation study was added for the Logistic Map to test whether the apparent statistical quality of a deterministic digital chaotic source depends on the arithmetic representation used to evaluate the recurrence.

The experiment currently compares four arithmetic backends:

- IEEE-754 binary32 (`float32`)
- IEEE-754 binary64 (`float64`)
- unsigned fixed-point Q3.29 (`fixed_q3_29`)
- MPFR with 256-bit precision (`mpfr_256`)

The existing binary64 implementation remains the default in order to preserve backward compatibility with earlier campaign configurations.

MPFR is treated as a high-precision digital reference, not as a physical or infinite-precision entropy source.

### Controlled arithmetic profiles

All variants evaluate the same Logistic Map

x[n+1] = r * x[n] * (1 - x[n])

and use the same threshold bit extraction rule.

For `float32`, both the map parameter and state are explicitly converted to IEEE-754 binary32 and every recurrence is evaluated using binary32 arithmetic.

For `float64`, the original project implementation is preserved.

For `fixed_q3_29`, the project uses scale

S = 2^29

with

R = floor(r * S)

X = floor(x * S)

and recurrence

X[n+1] = floor(R * X[n] * (S - X[n]) / S^2).

A 128-bit integer intermediate is used to prevent overflow during the exact fixed-point multiplication.

For `mpfr_256`, the recurrence is evaluated using 256-bit MPFR arithmetic with round-to-nearest. Decimal parameter literals from YAML are retained so that MPFR parameters are not first quantized through binary64.

### Local precision smoke

A controlled local smoke experiment used the same Logistic Map configuration and generated 1,000,000 RAW bits for every arithmetic mode.

Observed basic statistics:

| arithmetic | bias | Shannon H | lag-1 autocorrelation | runs z | longest run |
|---|---:|---:|---:|---:|---:|
| float32 | 0.008979 | 0.9997673603 | 0.0208452531 | -20.8462434 | 11 |
| float64 | 0.000391 | 0.9999995589 | -0.0009416115 | 0.9406126 | 21 |
| fixed_q3_29 | 0.005686 | 0.9999067116 | 0.0202783202 | -20.2793103 | 12 |
| mpfr_256 | 0.000431 | 0.9999994640 | -0.0001837434 | 0.1827433 | 21 |

All four arithmetic modes produced distinct SHA-256 fingerprints and therefore distinct deterministic digital trajectories.

The local smoke suggests two qualitatively different groups for this particular configuration: `float32` and Q3.29 show clearly detectable serial structure, whereas `float64` and MPFR-256 remain close to the expected values of the basic statistical diagnostics.

This is a single-configuration smoke result and is not interpreted as evidence that one arithmetic representation is universally superior.

### Exact digital-state periodicity

An exact-state cycle detector based on Brent's algorithm was implemented and independently regression-tested.

The detector compares exact represented digital states rather than using an epsilon-based floating-point comparison.

The smoke configuration used:

- r = 4.000000000000000
- x0 = 0.79740852937250928
- maximum cycle-search bound = 10,000,000 state transitions

Two probes were run: one from the original initial state (`burn_in=0`) and one after the normal screening burn-in of 1000 iterations.

Results from the original x0:

| arithmetic | transient mu | cycle lambda | result |
|---|---:|---:|---|
| float32 | 565 | 4344 | exact cycle detected |
| float64 | NA | NA | no exact recurrence observed within 10^7 transitions |
| fixed_q3_29 | 3173 | 6876 | exact cycle detected |
| mpfr_256 | NA | NA | no exact recurrence observed within 10^7 transitions |

Results after burn-in = 1000:

| arithmetic | post-burn-in mu | cycle lambda | result |
|---|---:|---:|---|
| float32 | 0 | 4344 | exact cycle detected |
| float64 | NA | NA | no exact recurrence observed within 10^7 transitions |
| fixed_q3_29 | 2173 | 6876 | exact cycle detected |
| mpfr_256 | NA | NA | no exact recurrence observed within 10^7 transitions |

The Q3.29 result provides an internal consistency check:

3173 - 1000 = 2173

while the detected cycle length remains unchanged at 6876.

For binary32, the original trajectory enters its cycle after only 565 iterations. Consequently, after the configured 1000-iteration burn-in the source is already on the cycle, producing post-burn-in mu = 0 while preserving lambda = 4344.

Because the output bit is a deterministic function of the internal state, once the state enters a cycle the resulting bit sequence is also periodic, with a bit period that divides the detected state-cycle length. The exact bit period has not yet been measured separately.

The failure to detect a cycle for binary64 or MPFR-256 within 10^7 transitions is treated as a censored search result only. It does not establish aperiodicity or absence of finite-state recurrence.

### Scientific interpretation

These results demonstrate why Shannon entropy alone is insufficient for evaluating digitally implemented chaotic candidate randomness sources.

For example, the binary32 stream has Shannon entropy approximately 0.99977 bits/bit, yet the exact digital trajectory enters a cycle of only 4344 states after 565 iterations. The Q3.29 implementation similarly combines high Shannon entropy with detectable serial structure and a finite exact cycle.

The experiment therefore motivates evaluating numerical representation, finite-state periodicity, serial statistics, and conditioning jointly rather than treating a high Shannon entropy estimate as evidence of cryptographic-quality entropy.

The precision and periodicity results remain preliminary local smoke validation. Final conclusions require the planned multi-parameter and multi-replicate HPC campaign.

### Detailed numerical reproducibility profile

The Logistic Map precision study is a controlled comparison of numerical representations. The underlying map, extraction rule, logical parameters, and output length are held constant while the arithmetic representation is changed.

The evaluated recurrence is:

`x[n+1] = r * x[n] * (1 - x[n])`

The currently implemented arithmetic modes are:

- `float32` — IEEE-754 binary32
- `float64` — IEEE-754 binary64 and the backward-compatible default
- `fixed_q3_29` — project-defined unsigned fixed-point Q3.29 profile
- `mpfr_256` — MPFR with 256-bit precision

MPFR-256 is used as a high-precision digital reference. It is not interpreted as an infinite-precision chaotic system or as a physical entropy source.

#### Binary32 arithmetic profile

For `float32`, both the current state and parameter `r` are explicitly converted to C++ `float` before each recurrence.

The evaluated expression is:

`next = (r * x) * (1.0F - x)`

The resulting binary32 state is stored through the common source interface, but the next iteration again explicitly converts the value to binary32. Therefore the recurrence follows an IEEE-754 binary32 trajectory.

#### Binary64 arithmetic profile

The `float64` backend preserves the original implementation:

`state = (config.r * state) * (1.0 - state)`

The parenthesization is intentional and forms part of the numerical reproduction profile.

Publication builds must not silently use `-ffast-math`, floating-point reassociation, or other transformations that can change the deterministic trajectory.

#### Fixed-point Q3.29 profile

The fixed-point sensitivity profile uses:

`S = 2^29`

Parameter and state quantization are:

`R = floor(r * S)`

`X = floor(x * S)`

The recurrence is:

`X[n+1] = floor(R * X[n] * (S - X[n]) / S^2)`

Integer division defines the truncation rule.

A GCC/Clang unsigned 128-bit integer intermediate is used to evaluate the multiplication without overflow.

This Q3.29 representation is a project-defined numerical-sensitivity profile. It is not claimed to reproduce a specific external hardware implementation.

#### MPFR-256 profile

The MPFR backend uses:

- precision: 256 bits
- rounding mode: `MPFR_RNDN`
- recurrence order corresponding to `(r*x)*(1-x)`

For explicit configurations, the original decimal YAML literals for `r` and `x0` are preserved and passed directly to MPFR.

This prevents the high-precision reference from first inheriting binary64 quantization of those parameters.

### Regression vectors

The arithmetic implementations are protected by deterministic regression vectors.

For the regression configuration:

- `r = 4.0`
- `x0 = 0.123456789`
- `burn_in = 10`
- threshold extraction

the reference prefixes are:

| arithmetic | reference prefix |
|---|---|
| float64 | `15 cd fc 5e` |
| float32 | `15 c4 f7 fe` |
| fixed_q3_29 | `15 cd 6d 57` |
| mpfr_256 | `15 cd fc 5e 5f 1a 00 fb` |

The MPFR and binary64 trajectories share the first four bytes for this regression configuration but diverge afterwards.

Reset reproducibility is tested independently for every arithmetic backend.

### Controlled precision smoke configuration

The local numerical-sensitivity smoke used:

- `r = 4.000000000000000`
- `x0 = 0.79740852937250928`
- `burn_in = 1000`
- `output_bits = 1,000,000`
- extraction = threshold
- conditioning = RAW

Only the numerical representation changes between the four runs.

### Full-stream reproducibility fingerprints

The 1,000,000-bit RAW smoke streams produced:

| arithmetic | SHA-256 |
|---|---|
| float32 | `700d731b840b5c473ee0b9d5714f8a8c8da0f38c49604738bd5b4bdfc4985884` |
| float64 | `246d5c99852d4274881807a3dd58d601e9f00962858b6682861804a1ebdc3979` |
| fixed_q3_29 | `5b6211ec9dd54fdec383eeec97a3e3c97d9bb75c44ca57e49911838fa0a021b9` |
| mpfr_256 | `63f26141c9093230f1f6e9a3f573367e7c14fafd674cb22fb34caca764735b56` |

All four streams are distinct.

### Local precision smoke statistics

| arithmetic | bias | Shannon H | lag-1 autocorrelation | runs z | longest run |
|---|---:|---:|---:|---:|---:|
| float32 | 0.008979 | 0.9997673603 | 0.0208452531 | -20.8462434 | 11 |
| float64 | 0.000391 | 0.9999995589 | -0.0009416115 | 0.9406126 | 21 |
| fixed_q3_29 | 0.005686 | 0.9999067116 | 0.0202783202 | -20.2793103 | 12 |
| mpfr_256 | 0.000431 | 0.9999994640 | -0.0001837434 | 0.1827433 | 21 |

For this configuration, `float32` and Q3.29 show substantially stronger serial defects than binary64 and MPFR-256 despite retaining very high Shannon entropy.

This is a local smoke result and must not yet be generalized to the entire Logistic Map parameter space.

### Exact digital-state periodicity

Exact digital periodicity is evaluated separately from ordinary bitstream statistics.

The implementation uses Brent cycle detection and reports:

- whether an exact recurrence was detected,
- transient length `mu`,
- state-cycle length `lambda`,
- state-transition evaluations.

State equality is exact equality of the represented digital state.

No epsilon or approximate floating-point comparison is used.

### Brent detector validation

The generic detector is regression-tested on synthetic systems with known behavior:

1. a seven-state pure cycle with expected `mu = 0`, `lambda = 7`;
2. a transient followed by a fixed point with expected `mu = 3`, `lambda = 1`;
3. a bounded non-repeating sequence used to verify that a cycle is not falsely reported inside the search horizon.

The Logistic Map experiment additionally compares cycle measurements from the original initial state and after the normal 1000-iteration burn-in.

### Periodicity smoke configuration

The periodicity probe used the same logical parameters as the precision smoke:

- `r = 4.000000000000000`
- `x0 = 0.79740852937250928`
- cycle-search bound = 10,000,000 state transitions

Two probes were performed:

1. from the original `x0`, with `burn_in = 0`;
2. after the standard `burn_in = 1000`.

### Periodicity from the original initial state

| arithmetic | mu | lambda | result |
|---|---:|---:|---|
| float32 | 565 | 4344 | exact cycle detected |
| float64 | NA | NA | no exact recurrence detected within 10^7 transitions |
| fixed_q3_29 | 3173 | 6876 | exact cycle detected |
| mpfr_256 | NA | NA | no exact recurrence detected within 10^7 transitions |

### Periodicity after burn-in 1000

| arithmetic | post-burn-in mu | lambda | result |
|---|---:|---:|---|
| float32 | 0 | 4344 | exact cycle detected |
| float64 | NA | NA | no exact recurrence detected within 10^7 transitions |
| fixed_q3_29 | 2173 | 6876 | exact cycle detected |
| mpfr_256 | NA | NA | no exact recurrence detected within 10^7 transitions |

The Q3.29 measurements provide an internal consistency check:

`3173 - 1000 = 2173`

while the detected state-cycle length remains `6876`.

For binary32, the trajectory reaches its exact cycle after only 565 iterations. Since the standard burn-in is 1000 iterations, the measured post-burn-in stream starts after the state has already entered the cycle. Consequently the second probe reports `mu = 0` while retaining `lambda = 4344`.

### State-cycle length versus output-bit period

The reported `lambda` is the period of the exact internal digital state.

The output bit is a deterministic function of that state. Therefore the eventual output sequence is also periodic after the state enters its cycle.

However, the minimal output-bit period can be a proper divisor of the internal state-cycle length.

Consequently, `lambda = 4344` does not by itself establish that the minimal binary32 bit period is exactly 4344. Likewise, `lambda = 6876` does not establish that the minimal Q3.29 bit period is exactly 6876.

A separate minimal bit-period measurement can be added if required.

### Censored cycle-search interpretation

For binary64 and MPFR-256, no exact recurrence was observed inside the configured search horizon of 10^7 transitions.

These observations are treated as censored search results.

They do not demonstrate:

- aperiodicity,
- absence of a finite digital cycle,
- cryptographic unpredictability,
- cryptographic entropy.

The correct statement is only that no exact recurrence was detected within the tested transition bound.

### Scientific interpretation

The local results demonstrate an important limitation of Shannon entropy as an isolated diagnostic.

The binary32 stream has Shannon entropy of approximately `0.99977 bits/bit`, yet its represented digital state reaches an exact cycle of only 4344 states after a transient of 565 iterations.

Similarly, Q3.29 retains Shannon entropy above `0.9999 bits/bit` while showing strong serial structure and an exact state cycle of 6876 states.

For this configuration, binary64 and MPFR-256 show much weaker defects in the basic statistical diagnostics and no exact recurrence within the 10^7-step search horizon.

The experiment therefore motivates jointly evaluating numerical representation, exact finite-state periodicity, serial statistics, and conditioning rather than treating near-maximal Shannon entropy as evidence of cryptographic-quality entropy.

### Limitations and next precision-study steps

The current results come from a single controlled `r,x0` smoke configuration.

They establish that numerical representation can materially alter the deterministic trajectory and can expose short finite-state cycles, but they do not establish population-level behavior.

The final HPC campaign should extend this analysis to a controlled collection of Logistic Map configurations and evaluate:

- frequency of detected cycles by arithmetic representation;
- distributions of `mu` and `lambda`;
- association between short cycles and serial statistical defects;
- sensitivity across Logistic Map parameters and replicates;
- RAW versus Ascon-XOF128 behavior;
- selected deeper statistical batteries for representative trajectories;
- optionally, the minimal output-bit period;
- optionally, larger cycle-search bounds for selected binary64 and MPFR-256 representatives.


## Chen et al. (2026) 4D-DCS source milestone

A modern high-dimensional chaotic source was added using the
4D discrete chaotic system proposed by Chen et al. in Entropy
28(7), 753 (2026), DOI 10.3390/e28070753.

The source is identified in the framework as:

`chen_4d_dcs`

The dynamical equations follow the published 4D-DCS model.
The image-encryption algorithm from the paper is not reproduced.

### Reference profile

The initial controlled profile uses:

- arithmetic: binary64
- r: 5.0
- x0: 0.1
- y0: 0.2
- z0: 0.3
- w0: 0.4
- burn-in: 1000 iterations

The project-defined extraction profile applies threshold 0.5
independently to x, y, z, and w after every transition.

The bit order is x, y, z, w, producing four bits per dynamical
iteration.

This extraction profile is intentionally simple and contains no
whitening or cryptographic post-processing.

### Implementation reproducibility

An independent Python implementation of the recurrence and the
C++ implementation were compared.

For burn-in 10, the first eight generated bytes were identical:

`7d f6 45 4a 31 8d 88 ef`

The complete 1,000,000-bit reference smoke stream was also
reproduced independently.

C++ and Python produced the same 16-byte preview:

`1a9f010c33f63a0702d8a16199172789`

and the same SHA-256 fingerprint:

`8548bd2b3efb79c20ad1c7ecdc8785011ed635ef08ef88a52a5d6362e0464438`

This validates deterministic reproduction of the implemented
binary64 project profile.

### RAW reference smoke

The 1,000,000-bit RAW stream produced:

- zeros: 499963
- ones: 500037
- bias: 0.000037
- Shannon entropy: 0.999999996049901 bits/bit
- lag-1 autocorrelation: -0.000667006145664817
- runs: 500334
- expected runs: 500000.997262
- runs z-score: 0.6660058126503925
- longest run: 21

The basic screening statistics therefore show no obvious
first-order defect for this single reference configuration.

This is not evidence of cryptographic security or a general
entropy claim.

### RAW versus Ascon-XOF128

The same raw source configuration was evaluated through the
existing Ascon-XOF128 conditioning stage.

RAW:

- bias: 0.00003700
- Shannon entropy: 0.9999999960
- lag-1 autocorrelation: -0.00066701
- runs z-score: 0.66600581
- longest run: 21

Ascon-XOF128:

- bias: 0.00036000
- Shannon entropy: 0.9999996261
- lag-1 autocorrelation: 0.00129248
- runs z-score: -1.29348292
- longest run: 17

The conditioned output remains statistically unremarkable in
these basic metrics, but it is not systematically "better" than
RAW in this individual smoke test.

This is expected when the raw stream already lacks visible
first-order defects. Small differences between RAW and XOF
should not be interpreted as evidence that conditioning either
improves or degrades the underlying source entropy.

### Verification status

After integrating the source, all 13 project tests passed,
including the dedicated Chen 4D-DCS deterministic regression
test and the existing Brent-cycle-detection regression tests.

### Current limitations

This milestone covers only one reference parameter/state
configuration.

It does not yet establish:

- behavior across the parameter space,
- NIST SP 800-22 campaign-level behavior,
- Dieharder behavior,
- TestU01 behavior,
- SP 800-90B estimates,
- resistance to finite-precision periodicity,
- cryptographic unpredictability,
- physical entropy.

Those questions remain for the screening and deep-testing
stages.


### Chen 4D-DCS finite-precision periodicity

An exact-state periodicity probe was performed for the
binary64 Chen 4D-DCS reference profile.

Configuration:

- r = 5.0
- initial state = (0.1, 0.2, 0.3, 0.4)
- arithmetic = IEEE-754 binary64
- exact equality across all four state coordinates
- recurrence-search bound = 10,000,000 transitions

Two starting points were evaluated:

1. the original initial state;
2. the state reached after the standard 1000-transition burn-in.

No exact state recurrence was detected within 10,000,000
transitions in either case.

This result must not be interpreted as proof of aperiodicity.
It establishes only that no exact binary64 state recurrence was
observed within the investigated transition bound.

The result contrasts with the lower-precision Logistic Map
profiles, where exact finite-state cycles were observed within
the same class of finite-precision analysis.



### Dieharder local integration validation

Dieharder 3.31.1 was integrated as an external statistical
randomness battery using raw binary file input (`-g 201`).

A new `--dump-bitstream` runner option exports the exact byte
stream evaluated internally by BioEntropy-HPC. Exported stream
SHA-256 fingerprints were verified against the hashes stored
in the corresponding result JSON files.

A 16 MiB capacity probe was used to identify tests that can be
executed without reusing the finite input file.

The validated local screening subset consists of Dieharder
tests:

0, 2, 4, 8, 9, 15, 16, 100, 101, and 102.

Parser-level safeguards classify results as INVALID when:

- Dieharder reports that the input file was rewound;
- the returned p-value is non-finite.

The first four-source screening produced:

- ChaCha20 reference: 40 PASS, 1 WEAK, 0 FAIL;
- Chen 4D-DCS: 37 PASS, 4 WEAK, 0 FAIL;
- Logistic Map binary64: 41 PASS, 0 WEAK, 0 FAIL;
- Rule90 negative control: 40 FAIL and 1 INVALID.

The Chen WEAK observations occurred in STS Monobit and
low-order STS Serial results. Because this experiment used one
stream and one p-sample, these observations are treated as
follow-up signals rather than evidence of source failure.

The presence of a WEAK result for the ChaCha20 reference also
demonstrates why isolated borderline p-values must not be
interpreted as source-level failures.

Rule90 was strongly rejected across the valid screening rows,
confirming that the external battery can distinguish the
deliberately defective negative control.

This milestone validates the Dieharder integration and analysis
pipeline. The next stage will use multiple independent
replicates before source-level conclusions are drawn.

### Dieharder 16 MiB four-source screening results

Following validation of the external-battery input path, a four-source
local Dieharder screening experiment was performed.

Each source produced:

- 16 MiB = 16,777,216 bytes;
- 134,217,728 output bits;
- RAW output;
- one experiment replicate;
- one p-sample per Dieharder invocation.

The tested representatives were:

1. Chen 4D-DCS, binary64 reference profile;
2. Logistic Map, binary64;
3. Rule90 cellular automaton negative control;
4. ChaCha20 deterministic cryptographic reference.

The validated no-rewind screening subset consisted of tests:

`0, 2, 4, 8, 9, 15, 16, 100, 101, 102`.

Because STS Serial produces multiple rows for different tuple orders,
each source generated 41 result rows.

#### Input-stream statistics

Chen 4D-DCS:

- bits: 134,217,728
- P(0): 0.5003777891
- P(1): 0.4996222109
- bias: 0.0003777891
- Shannon entropy: 0.9999995882 bits/bit
- SHA-256:
  `db2b705ae2f92dae17065c9f10b25f9dbbecc9cfc713f7543e9ba8345e01ecff`

Logistic Map binary64:

- bits: 134,217,728
- P(0): 0.4999787211
- P(1): 0.5000212789
- bias: 0.0000212789
- Shannon entropy: 0.9999999987 bits/bit
- SHA-256:
  `2f4b859a051a8c1ae32e33ffd9bd805d376a285c62240ade9e5e8c2d22072b97`

Rule90:

- bits: 134,217,728
- P(0): 0.9998825490
- P(1): 0.0001174510
- bias: 0.4998825490
- Shannon entropy: 0.0017028349 bits/bit
- SHA-256:
  `6b8b27580aac46651504cc93c9e52075e4d1917b166ee90b605af97380d87537`

ChaCha20 reference:

- bits: 134,217,728
- P(0): 0.5000008419
- P(1): 0.4999991581
- bias: 0.0000008419
- Shannon entropy: 1.0000000000 bits/bit
- SHA-256:
  `b305c84e9a542cbc3b6d0f2291215f69e89b5427998594e917715513f9d2515e`

#### Screening summary

The parsed screening produced:

| Source | PASS | WEAK | FAIL | INVALID |
|---|---:|---:|---:|---:|
| ChaCha20 | 40 | 1 | 0 | 0 |
| Chen 4D-DCS | 37 | 4 | 0 | 0 |
| Logistic binary64 | 41 | 0 | 0 | 0 |
| Rule90 | 0 | 0 | 40 | 1 |

The Rule90 INVALID row was STS Runs, for which Dieharder produced a
non-finite p-value (`nan`). The parser correctly prevented the textual
Dieharder `PASSED` label from being interpreted as a valid result.

#### Chen 4D-DCS observations

Chen produced no valid `FAILED` rows.

Four rows were classified as `WEAK`:

- STS Monobit:
  p = 0.99989938
- STS Serial, ntuple 1:
  p = 0.99989938
- STS Serial, ntuple 2:
  p = 0.00075384
- STS Serial, ntuple 3:
  p = 0.00426047

The Monobit and Serial ntuple-1 values are not treated as independent
pieces of evidence because they represent closely related low-order
statistics.

The clustering of the Chen borderline values at low-order frequency and
serial statistics is nevertheless retained as a specific follow-up
hypothesis for the multi-replicate campaign.

At this stage the correct conclusion is:

Chen showed no test failures in the validated local screening profile,
but produced several borderline low-order statistical results that
require replication.

This is stronger and more precise than either claiming that the source
"passes randomness testing" or treating an isolated WEAK value as a
failure.

#### ChaCha20 reference observation

ChaCha20 produced:

- 40 PASS;
- 1 WEAK;
- 0 FAIL.

The single WEAK row was:

- STS Serial, ntuple 9:
  p = 0.99555653.

The presence of a borderline result even for the cryptographic reference
illustrates why isolated WEAK assessments are expected to occur
occasionally when many statistical hypotheses are evaluated.

This motivates replicate-level and family-level interpretation rather
than binary source classification from one p-value.

#### Logistic binary64 observation

The Logistic Map binary64 representative produced:

- 41 PASS;
- 0 WEAK;
- 0 FAIL.

For this individual 16 MiB stream, no defect was detected by the
validated local Dieharder subset.

This does not override the broader finite-precision study.

In particular, the project has already demonstrated that statistical
appearance and digital state-cycle behavior are separate properties:
other Logistic numerical representations exhibit exact finite-state
cycles and serial defects despite high Shannon entropy.

#### Rule90 negative control

Rule90 produced:

- 40 valid FAIL results;
- 1 INVALID result;
- 0 PASS;
- 0 WEAK.

The negative control therefore behaves as intended.

Its very strong imbalance also became more pronounced in the longer
16 MiB stream, with approximately 99.988% zero bits and Shannon entropy
of only approximately 0.0017 bits/bit.

The rejection of Rule90 across the external screening battery provides
an important validation that the pipeline is capable of detecting a
deliberately poor source.

#### Scientific interpretation

These results validate the local Dieharder integration but do not yet
constitute the final statistical comparison.

The present experiment uses:

- one source stream per representative;
- one Dieharder p-sample;
- a restricted no-rewind local test subset.

The next statistical stage will use multiple independent experiment
replicates.

The main questions for that campaign include:

1. whether the Chen low-order WEAK pattern persists across independent
   source initializations / experiment seeds;
2. whether occasional ChaCha20 WEAK results occur at the expected
   frequency for multiple testing;
3. how Logistic precision variants differ when evaluated by the same
   external battery;
4. whether conditioning systematically changes the frequency of
   detectable statistical defects;
5. whether the negative Rule90 control remains consistently rejected.


### Replication-semantics audit

Before generating the full multi-replicate statistical campaign, the
meaning of `replicate_id` was empirically verified for each source
family.

Two otherwise identical configurations with replicate identifiers 0
and 1 were generated and their output SHA-256 fingerprints compared.

Results:

- Chen 4D-DCS: identical stream;
- Logistic Map with explicit x0: identical stream;
- Rule30: different stream;
- Rule90: different stream;
- ChaCha20 reference: different stream;
- fixed DNA window: identical stream.

This result revealed an important methodological distinction.

For Chen, Logistic configurations with explicit initial conditions, and
DNA, changing the experiment replicate identifier alone does not create
a new source realization.

Using such configurations as nominal independent replicates would
therefore constitute pseudoreplication.

The final campaign will instead use:

- Chen: distinct deterministic four-dimensional initial states;
- Logistic precision study: distinct x0 values, paired across all
  arithmetic representations;
- Rule30/Rule90: replicate identifiers / derived seeds;
- ChaCha20: replicate identifiers / derived key and nonce material;
- DNA: distinct versioned biological sequence windows.

The audit also demonstrates why reproducibility metadata and source
semantics must be separated: two experiments can have different derived
framework seeds while still producing exactly the same source
bitstream if that particular source configuration does not consume the
seed.


### DNA Dieharder capacity limitation

A standard 400,000-nucleotide DNA window maps to 800,000 bits
(100,000 bytes).

The validated local Dieharder screening subset was applied to one such
window as a capacity experiment.

Every tested invocation reused the finite input file.

The number of rewinds ranged from 41 to 92 depending on the test.

Therefore all produced DNA Dieharder p-values were classified as
INVALID, regardless of Dieharder's textual PASS, WEAK, or FAIL label.

This result is an input-size limitation, not evidence that the tested
DNA window failed the statistical battery.

The project explicitly rejects two potentially misleading solutions:

- looping/repeating the same DNA window;
- reducing test parameters only for DNA and then directly comparing
  those results with the standard digital-source screening.

Instead, individual versioned windows remain the biological replication
units.

For external-battery diagnostics, a separate pooled DNA corpus will be
constructed from distinct preselected windows without repetition.

Corpus-level results will be labeled separately and will not be treated
as replicate-level DNA evidence.


### DNA corpus-level external-battery result

The single-window Dieharder capacity experiment demonstrated that
100,000 bytes of mapped DNA were insufficient for every test in the
validated external-battery subset.

A separate pooled DNA corpus was therefore constructed from all 50
distinct versioned reference windows.

Corpus properties:

- 50 windows;
- 20,000,000 nucleotides;
- 40,000,000 mapped bits;
- 5,000,000 bytes;
- no repeated windows;
- no artificial looping;
- no separators between window bitstreams.

Corpus SHA-256:

`f2ea67e8a6d33cb7b6aa6bfd95a2eab960d323f87acd77128714e7f4609c2c93`

A manifest records the deterministic concatenation order and the
fingerprint of every constituent bitstream.

The corpus was large enough to execute six Dieharder test families
without file reuse:

- Birthdays;
- Count the 1s (stream);
- Diehard Runs;
- STS Monobit;
- STS Runs;
- STS Serial.

Four other tests still rewound the 5 MB corpus once and their outputs
were discarded as INVALID.

Among the 36 valid result rows:

- 2 were PASS;
- 3 were WEAK;
- 31 were FAIL.

The two Diehard Runs rows passed.

Birthdays and STS Monobit produced borderline WEAK results.

STS Runs failed.

Count the 1s (stream) failed.

STS Serial showed strong rejection across nearly every tuple order above
the first-order result.

Because the STS Serial outputs are related subtests, the row count is
not interpreted as a count of independent failures.

Instead, the result provides evidence of strong higher-order serial
structure in the pooled mapped DNA corpus.

This observation is especially relevant because individual DNA windows
frequently exhibit Shannon entropy close to one bit per mapped bit.

The combination demonstrates that a high first-order Shannon entropy
estimate can coexist with substantial higher-order dependence.

The result is intentionally described as corpus-level evidence.

It does not establish that every individual biological window would
independently produce the same Dieharder outcome.


### Paired Dieharder precision validation

A replicate-aware Dieharder validation campaign was executed before the
full multi-replicate campaign.

The campaign contained ten source groups:

- Logistic Map float32
- Logistic Map float64
- Logistic Map Q3.29
- Logistic Map MPFR-256
- Chen 4D-DCS float64
- Rule30, width 256
- Rule30, width 1024
- Rule90, width 256
- Rule90, width 1024
- ChaCha20 reference

Each validation stream contained:

- 16,777,216 bytes;
- 134,217,728 bits.

The validated Dieharder profile was:

`0, 2, 4, 8, 9, 15, 16, 100, 101, 102`

with `psamples = 1`.

No input file was rewound in any validation execution.

The parser produced 410 rows in total.

#### Result summary

| Source | PASS | WEAK | FAIL | INVALID |
|---|---:|---:|---:|---:|
| ChaCha20 | 40 | 1 | 0 | 0 |
| Chen 4D-DCS | 40 | 1 | 0 | 0 |
| Logistic Q3.29 | 0 | 0 | 41 | 0 |
| Logistic float32 | 0 | 0 | 41 | 0 |
| Logistic float64 | 40 | 1 | 0 | 0 |
| Logistic MPFR-256 | 40 | 1 | 0 | 0 |
| Rule30 width 1024 | 39 | 2 | 0 | 0 |
| Rule30 width 256 | 40 | 0 | 1 | 0 |
| Rule90 width 1024 | 0 | 0 | 40 | 1 |
| Rule90 width 256 | 0 | 0 | 40 | 1 |

The INVALID Rule90 rows were non-finite STS Runs results and were not
caused by input reuse.

#### Matched Logistic precision design

All four Logistic arithmetic implementations used the same nominal
initial state in the validation replicate:

`x0 = 0.63481853342071715`

with the same map parameters and extraction rule.

Consequently, the large difference between the four implementations
cannot be attributed to different nominal dynamical initial conditions.

Both float32 and Q3.29 were rejected in every valid output row of the
selected Dieharder profile.

In contrast, float64 and MPFR-256 each produced 40 PASS rows and one
WEAK row, with no FAIL results.

The result provides strong preliminary evidence that finite numerical
representation can dominate the statistical properties of a
digitally implemented chaotic source.

This conclusion concerns the evaluated digital implementations and does
not imply a corresponding property of the ideal real-valued Logistic
Map.

#### Other validation observations

ChaCha20 produced one WEAK STS Serial result and no failures.

Chen 4D-DCS produced one WEAK Diehard Craps result and no failures for
the tested non-reference initial state.

Rule30 width 1024 produced two WEAK STS Serial rows and no failures.

Rule30 width 256 produced one valid Diehard Craps failure. This single
replicate is insufficient to determine whether the result is a
persistent property of the source configuration or an isolated
statistical outcome.

Both Rule90 configurations were strongly rejected, confirming the
intended negative-control behavior.

#### Decision

The 16 MiB test size and the selected Dieharder profile are now frozen
for the multi-replicate digital-source campaign.

Source-level interpretation will be based on repeated realizations
rather than the individual validation replicate.


## Full replicate-aware Dieharder RAW campaign

The frozen RAW digital-source screening campaign comprised
20 deterministic realizations for each of 10 source profiles.
Each realization contained 16 MiB (134,217,728 bits).

The campaign produced 8,200 parsed result rows with zero input
rewinds. Forty-six rows were marked INVALID exclusively because
STS Runs returned a non-finite p-value. These rows were not
reclassified as statistical failures.

Replicate-level outcomes were derived after consolidating
multiple rows emitted by the same Dieharder test family.

| Source | FAIL | WEAK | PASS |
|---|---:|---:|---:|
| ChaCha20 | 0 | 5 | 15 |
| Chen 4D-DCS | 0 | 11 | 9 |
| Logistic Q3.29 | 20 | 0 | 0 |
| Logistic float32 | 20 | 0 | 0 |
| Logistic float64 | 5 | 5 | 10 |
| Logistic MPFR-256 | 0 | 5 | 15 |
| Rule30, 1024 cells | 0 | 7 | 13 |
| Rule30, 256 cells | 20 | 0 | 0 |
| Rule90, 1024 cells | 20 | 0 | 0 |
| Rule90, 256 cells | 20 | 0 | 0 |

### Logistic float64 finite-precision collapse

Five of the 20 frozen float64 trajectories reached exactly
1.0 within the 134,217,728-bit experimental horizon and
subsequently entered the absorbing zero state.

All five collapsed realizations were classified as FAILED by
the replicate-level Dieharder screening. None of the fifteen
non-collapsed float64 realizations was classified as FAILED.

This is an observed association within the fixed deterministic
replicate set and must not be interpreted as an estimate that
25% of arbitrary Logistic Map initial conditions collapse.

The paired MPFR-256 implementation produced no FAILED
realizations across the same 20 nominal initial conditions.

### Cellular automata

Rule30 with 256 cells exhibited a recurrent Diehard Craps
failure in all 20 realizations. Rule30 with 1024 cells produced
no replicate-level FAIL outcomes in the same screening profile.

Rule90 behaved as the intended negative control, with all
realizations strongly rejected.

### Interpretation constraints

WEAK results are descriptive screening observations and are
not treated as independent evidence of a source defect.
Individual Dieharder output rows are also not interpreted as
independent hypothesis tests because some test families,
particularly STS Serial, emit multiple related rows.

Passing this screening does not establish entropy,
unpredictability, or cryptographic security.


## Ascon-XOF128 paired conditioning validation

A paired RAW-versus-Ascon-XOF128 workflow was constructed directly from the frozen replicate-aware Dieharder configurations. Validation of the first two replicates across all ten source groups confirmed 20/20 exact pairs. The only configuration change was `conditioning.mode` from `raw` to `ascon_xof128`.

For Ascon-XOF128, the complete RAW realization is retained and supplied to one conditioner invocation. The conditioned output has the same length as the input. Thus each Dieharder realization uses 16 MiB RAW -> one Ascon-XOF128 invocation -> 16 MiB conditioned output.

The RAW input digest is recorded as `conditioning.input_sha256`.

### Logistic float64 collapsed-realization smoke test

Logistic float64 replicate 001, previously observed to collapse to the absorbing zero state and to fail nine RAW Dieharder families, was used as an extreme conditioning validation case.

RAW input SHA-256:

`9d83f5dcc113c2ab47df859ba00b964cfcb8b8705b9673b9198e3e925c87c763`

After Ascon-XOF128 conditioning:

- P(1) = 0.5000052005
- absolute bias = 0.0000052005
- Shannon entropy = 0.9999999999 bits/bit
- conditioned SHA-256 = `1f998c833fe4d021b60876fe10ee956bdc6f513f216982d3294d128f0f29c5e6`

The conditioned 16 MiB realization passed all ten frozen Dieharder test families (d0, d2, d4, d8, d9, d15, d16, d100, d101, d102), with no input rewind reported.

This remains a single-realization validation result. Source-level conclusions require the full paired replicate campaign.

Statistical improvement after deterministic conditioning must not be interpreted as creation of entropy. Ascon-XOF128 can suppress visible statistical structure in deterministic input without introducing physical entropy or establishing unpredictability absent from that input.


### Paired 2x10 Ascon conditioning smoke campaign

Before launching the full paired conditioning campaign, the
first two frozen replicates of all ten digital source groups
were evaluated after Ascon-XOF128 conditioning.

The smoke campaign contained 20 conditioned realizations and
200 Dieharder test-family executions. It completed with:

- 200/200 Dieharder result files
- 200/200 exit-status files
- 20/20 SHA-256 provenance files
- zero retained temporary bitstreams
- zero input rewinds
- zero replicate-level FAIL outcomes
- 7 replicate-level WEAK outcomes
- 13 replicate-level PASS outcomes
- zero INVALID replicate outcomes

Pre-conditioning provenance was verified independently for all
20 realizations. In every case,
`conditioning.input_sha256` exactly matched the SHA-256 digest
of the corresponding frozen RAW realization.

The paired replicate-level RAW -> Ascon transitions were:

- FAILED -> PASSED: 6
- FAILED -> WEAK: 5
- WEAK -> PASSED: 6
- WEAK -> WEAK: 2
- PASSED -> PASSED: 1

No RAW FAILED realization remained FAILED after conditioning in
this smoke campaign.

Seven conditioned realizations contained one WEAK test family.
Six of these involved STS Serial (d102), while one involved
Diehard Rank 32x32 (d2) for the ChaCha20 reference.

Eight individual WEAK Dieharder rows were observed, but two
belonged to the same Rule30-256 replicate and the same STS
Serial family. This therefore corresponds to seven
family-level WEAK outcomes, illustrating why individual
Dieharder output rows are not treated as independent results.

Notably, the strong RAW defects previously observed for
Logistic float32, Logistic Q3.29, collapsed Logistic float64,
Rule30-256, and both Rule90 widths were no longer expressed as
replicate-level FAIL outcomes after Ascon-XOF128 conditioning.

These observations support proceeding to the full paired
20-replicate conditioning campaign.

They demonstrate suppression of visible output-level
statistical defects, not creation of entropy. Ascon-XOF128 is
deterministic and cannot introduce physical entropy or
unpredictability absent from its input.

### Full paired RAW versus Ascon-XOF128 campaign

The full paired conditioning campaign covered all 200 frozen
digital-source realizations (10 source groups x 20 replicates).

All 200 Ascon inputs were independently verified against the
stored SHA-256 digests of their corresponding RAW realizations.
The provenance check passed for 200/200 pairs.

At replicate level, the conditioned campaign produced:

- PASSED: 146/200
- WEAK: 54/200
- FAILED: 0/200
- INVALID: 0/200

The paired RAW -> Ascon replicate transitions were:

- FAILED -> PASSED: 79
- FAILED -> WEAK: 26
- WEAK -> PASSED: 22
- WEAK -> WEAK: 11
- PASSED -> PASSED: 45
- PASSED -> WEAK: 17

Thus none of the 105 RAW FAILED realizations remained FAILED
after Ascon-XOF128 conditioning.

For Logistic float64, all five realizations previously shown to
undergo exact finite-precision collapse (replicates 001, 005,
007, 008, and 012) changed from RAW FAILED to conditioned
PASSED.

The five conditioned Logistic float64 WEAK outcomes occurred
only among non-collapsed trajectories. Therefore the equality
between the number of collapsed RAW trajectories and the number
of conditioned WEAK outcomes is coincidental in this frozen
replicate set.

The full results reinforce the distinction between statistical
conditioning and entropy generation. Ascon-XOF128 suppresses
the visible statistical defects detected in the RAW streams,
including severe deterministic defects, but this does not imply
that entropy or unpredictability was created.

### Paired test-family comparison

The paired analysis was additionally performed at the frozen
Dieharder test-family level, yielding 2000 exact RAW-versus-
Ascon pairs (200 realizations x 10 test families).

The observed family-level transitions were:

- RAW FAILED -> Ascon PASSED: 798
- RAW FAILED -> Ascon WEAK: 23
- RAW INVALID -> Ascon PASSED: 46
- RAW WEAK -> Ascon PASSED: 43
- RAW WEAK -> Ascon WEAK: 8
- RAW PASSED -> Ascon PASSED: 1053
- RAW PASSED -> Ascon WEAK: 29

No conditioned family was classified as FAILED or INVALID.

Thus all 821 RAW FAILED families were reduced to either PASSED
or WEAK after conditioning, and all 46 RAW INVALID families
became PASSED.

The strongest source-specific examples include:

- Logistic float32: all broad RAW family failures disappeared;
  only one conditioned STS Serial family was WEAK.
- Logistic Q3.29: severe recurrent RAW failures were reduced to
  PASSED or occasional WEAK outcomes.
- Rule30-256 Diehard Craps: 20/20 RAW FAIL became 19 PASSED
  and 1 WEAK.
- Rule90 at both widths: the broad RAW rejection pattern was
  removed, with no conditioned family-level FAIL outcomes.

For the five Logistic float64 realizations known to collapse
exactly because of finite-precision dynamics, all 50 paired
test-family outcomes were PASSED after conditioning. This
includes the five RAW STS Runs families that had been INVALID.

These results demonstrate output-level statistical
regularization by Ascon-XOF128. They do not demonstrate the
creation of entropy or unpredictability from deterministic
input.

### Conditioning result figures

Publication-oriented figures were generated from the frozen
paired RAW-versus-Ascon aggregate tables.

The current figure set contains:

- `raw_vs_ascon_failed_replicates`: replicate-level FAILED
  counts for each source before and after Ascon-XOF128.
- `float64_collapsed_conditioning`: test-family outcomes for
  the five frozen Logistic float64 trajectories that underwent
  exact finite-precision collapse.

Both figures are generated reproducibly by
`analysis/scripts/plot_conditioning_results.py`.

The plotting environment is recorded in
`requirements-analysis.txt`.

### Conditioning result figures

Publication-oriented figures were generated from the frozen
paired RAW-versus-Ascon aggregate results.

The figure set currently contains:

- `raw_vs_ascon_failed_replicates`: replicate-level FAILED
  counts for all ten source groups before and after
  Ascon-XOF128 conditioning.
- `float64_collapsed_conditioning`: family-level outcomes for
  the five frozen Logistic float64 trajectories that underwent
  exact finite-precision collapse.

The figures are generated reproducibly by
`analysis/scripts/plot_conditioning_results.py`.

The Python plotting dependencies are recorded in
`requirements-analysis.txt`.


## 2026-09-08 — NIST SP 800-90B windowed float64 collapse validation

### NIST SP 800-90B integration

Integrated the official NIST SP 800-90B EntropyAssessment
tool at tag `v1.1.8` as a Git submodule. The upstream
self-test passed with numerical deltas far below `1e-6`.

A preprocessing adapter was added to convert the project's
MSB-first packed bitstreams into the one-byte-per-binary-symbol
format expected by `ea_non_iid`.

All generated RAW streams are checked against the SHA-256
recorded for the frozen Dieharder campaign before entropy
assessment.

### 1M-prefix float64 screening

All 20 frozen `logistic-float64` realizations were assessed
using the first 1,000,000 output bits.

All 20 regenerated RAW streams passed provenance validation.

Observed `H_original` range:

- minimum: 0.822919
- maximum: 0.889318
- mean: 0.854196

For the five realizations known to collapse later
(reps 001, 005, 007, 008, 012), mean prefix
`H_original` was approximately 0.844889.

For the remaining 15 realizations, mean prefix
`H_original` was approximately 0.857298.

The two groups overlap strongly at the 1M prefix. Therefore,
early local entropy estimates do not reliably identify the
later finite-precision collapse.

### Windowed analysis — float64 rep001

Frozen realization:

- replicate: `rep001`
- explicit x0: `0.14571965014107383`
- RAW SHA-256:
  `9d83f5dcc113c2ab47df859ba00b964cfcb8b8705b9673b9198e3e925c87c763`
- exact collapse index: 5,919,555

The last observed `1` in the generated output bitstream is at
index 5,919,554. From bit 5,919,555 onward the output is exactly
zero. This agrees exactly with the independently determined
collapse reference; measured index difference = 0.

NIST SP 800-90B non-IID estimates for consecutive 1M-bit
windows:

| Window | P(1) | H_original |
|---|---:|---:|
| 0–1M | 0.500879 | 0.823339 |
| 1–2M | 0.500000 | 0.866904 |
| 2–3M | 0.499581 | 0.843698 |
| 3–4M | 0.499611 | 0.865989 |
| 4–5M | 0.499994 | 0.840139 |
| 5–6M | 0.459056 | 0.000062 |
| 6–7M | 0.000000 | 0.000000 |
| 7–8M | 0.000000 | 0.000000 |

The 5–6M window contains the exact collapse and its NIST
non-IID estimate falls to `0.000062`.

For the post-collapse constant windows, `ea_non_iid` terminates
with exit code 255 and reports:

`Symbol alphabet consists of 1 symbol. No entropy awarded...`

These windows are therefore stored as
`assessment_status=degenerate_constant`, with empirical
min-entropy `0.0`. The value is not represented as a numerical
estimate returned by `ea_non_iid`; its provenance is explicitly
recorded as `empirical_constant_distribution`.

### Interpretation

This result demonstrates a trajectory-length-dependent
finite-precision failure. A float64 logistic-map realization can
show high local statistical quality and substantial empirical
non-IID min-entropy for several million output bits, followed by
an abrupt transition to a deterministic absorbing state.

The NIST values are treated as empirical sequence entropy
estimates only. They do not establish that the deterministic
logistic map is a compliant NIST entropy source and do not imply
cryptographic unpredictability.

## 2026-09-08 — Five-replicate float64 NIST 90B collapse campaign

Windowed NIST SP 800-90B non-IID assessment was completed for all five frozen float64 realizations with independently identified exact finite-precision collapse points.

All regenerated RAW streams passed SHA-256 provenance validation against the frozen Dieharder campaign.

| Replicate | Collapse index | Collapse window | P(1) | H_original | Status |
|---|---:|---|---:|---:|---|
| rep001 | 5,919,555 | 5,000,000–6,000,000 | 0.459056 | 0.00006200 | nist_estimated |
| rep005 | 16,181,612 | 16,000,000–17,000,000 | 0.091052 | 0.00000000 | nist_estimated |
| rep007 | 21,156,926 | 21,000,000–22,000,000 | 0.078795 | 0.00000000 | nist_estimated |
| rep008 | 10,996,001 | 10,000,000–11,000,000 | 0.498449 | 0.00295700 | nist_estimated |
| rep012 | 9,423,224 | 9,000,000–10,000,000 | 0.211820 | 0.00000000 | nist_estimated |

Mean `H_original` across the five collapse-containing windows: `0.00060380`.

Immediately preceding full 1M-bit windows still showed high empirical non-IID min-entropy, approximately `0.84–0.88` bits/bit.

The collapse-containing windows therefore show an abrupt loss of empirical min-entropy rather than a gradual degradation visible from the beginning of the sequence.

For rep001, the independently detected collapse index `5,919,555` equals the first permanently zero output-bit index exactly.

Post-collapse one-symbol windows cause `ea_non_iid` to report `No entropy awarded`. They are represented as `assessment_status=degenerate_constant` with empirical min-entropy `0.0`, while remaining explicitly distinct from numerical estimates returned by NIST.

The parser also normalizes the textual NIST output `-0.000000` to numerical positive zero while retaining the original `ea_non_iid.txt` output for provenance.

These results provide repeatable evidence of a trajectory-length-dependent finite-precision failure mechanism in 5 of the 20 pre-specified deterministic float64 logistic-map realizations.

The NIST SP 800-90B results are interpreted strictly as empirical sequence entropy estimates. They do not make the deterministic logistic map a compliant entropy source and do not establish cryptographic unpredictability.

Combined table:

`results/aggregated/nist90b_logistic-float64_collapsed_windows.tsv`


### Collapse-aligned NIST 90B figure

A collapse-aligned visualization was generated for all five
pre-specified float64 realizations that reach the exact
finite-precision absorbing state.

For each 1M-bit window, the plotted x-coordinate is the window
midpoint relative to the independently determined exact collapse
index:

`relative_position = window_midpoint - collapse_index`.

Therefore `x = 0` represents the exact finite-precision collapse
for every realization despite their different absolute collapse
positions.

Descriptive aggregate values across the five realizations:

- mean `H_original` in the last complete pre-collapse window:
  `0.85626900` bits/bit;
- mean `H_original` in the collapse-containing window:
  `0.00060380` bits/bit;
- mean absolute decrease:
  `0.85566520` bits/bit.

The result is descriptive for the five collapsed members of the
20 pre-specified deterministic float64 realization set. It is not
an estimate of the probability that an arbitrary float64 initial
condition will collapse.

Figure outputs:

- `results/figures/nist90b_float64_collapse_aligned.png`
- `results/figures/nist90b_float64_collapse_aligned.pdf`

Machine-readable summaries:

- `results/aggregated/nist90b_logistic-float64_collapsed_windows.tsv`
- `results/aggregated/nist90b_logistic-float64_collapse_summary.tsv`

Post-collapse one-symbol windows remain explicitly distinguished
from NIST numerical estimates using
`assessment_status=degenerate_constant`.

## 2026-09-09 — NIST SP 800-90B 10-source prefix campaign

Completed NIST SP 800-90B non-IID initial entropy screening for the full frozen 10-source campaign.

Protocol:

- 10 source groups;
- 20 frozen realizations per source;
- 1,000,000 sequential output bits per realization;
- binary samples represented as one byte per bit;
- MSB-first unpacking matching the framework bitstream semantics;
- `ea_non_iid -i` with `bits_per_symbol=1`;
- SHA-256 provenance checked against the frozen RAW campaign.

All 200 regenerated RAW realizations passed provenance validation.

| Source | n | H min | H mean | H median | H max | H SD | mean P(1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| logistic-float32 | 20 | 0.00000000 | 0.00000170 | 0.00000200 | 0.00000200 | 0.00000073 | 0.47133510 |
| logistic-float64 | 20 | 0.82291900 | 0.85419560 | 0.84896500 | 0.88931800 | 0.02442606 | 0.50001335 |
| logistic-fixed_q3_29 | 20 | 0.00000200 | 0.00000230 | 0.00000200 | 0.00000300 | 0.00000047 | 0.50566665 |
| logistic-mpfr_256 | 20 | 0.81390700 | 0.85076925 | 0.84418900 | 0.91249600 | 0.02943400 | 0.49992130 |
| chen-4d-dcs | 20 | 0.81732300 | 0.85573385 | 0.85696800 | 0.88291200 | 0.01649438 | 0.49957485 |
| rule30-cells256 | 20 | 0.67989500 | 0.83901885 | 0.84049400 | 0.94333400 | 0.05192448 | 0.49999530 |
| rule30-cells1024 | 20 | 0.81262800 | 0.85908580 | 0.85358700 | 0.91687100 | 0.03434355 | 0.49996915 |
| rule90-cells256 | 20 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 0.01623620 |
| rule90-cells1024 | 20 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 | 0.26150750 |
| chacha20 | 20 | 0.80916500 | 0.84912370 | 0.84516700 | 0.90117300 | 0.02159738 | 0.50009170 |

Key observations:

- `logistic-float32` has essentially zero empirical non-IID min-entropy despite a much less extreme mean bit balance than the Rule90 cases.
- `logistic-fixed_q3_29` is especially important: mean `P(1)` is close to 0.5 while `H_original` remains near zero. Bit balance alone therefore does not capture the strong sequential predictability detected by the non-IID estimators.
- both Rule90 configurations have `H_original = 0` across all 20 frozen realizations.
- float64, MPFR-256, Chen-4D, Rule30 and ChaCha20 form a high empirical-entropy group on the 1M-bit prefix, with mean `H_original` approximately 0.84–0.86 bits/bit.
- Rule30-256 shows the largest spread within that high group, including a minimum near 0.68.

These values are empirical sequence estimates produced by the SP 800-90B non-IID assessment methodology. They do not establish that deterministic chaos, cellular automata, or ChaCha20 are entropy sources, and they do not imply formal NIST entropy-source compliance or cryptographic secrecy.

The prefix experiment also does not capture late finite-precision collapse in float64 realizations; that phenomenon is analyzed separately using collapse-aligned windowed assessments.

Machine-readable outputs:

- `results/aggregated/nist90b_prefix1m_all_sources.tsv`
- `results/aggregated/nist90b_prefix1m_source_summary.tsv`

### NIST 90B source-comparison figure

Generated a publication-oriented comparison of the 10 frozen
source groups using the mean 1M-prefix `H_original` across
20 realizations per source. Error bars span the observed
minimum-to-maximum replicate range.

Figure outputs:

- `results/figures/nist90b_prefix1m_sources.png`
- `results/figures/nist90b_prefix1m_sources.pdf`

The figure is descriptive of the frozen experimental realization
set. In particular, high empirical `H_original` for a
deterministic generator such as ChaCha20 must not be interpreted
as evidence of fresh physical entropy.

## 2026-09-09 — DNA NIST SP 800-90B campaign

Completed a NIST SP 800-90B non-IID empirical entropy assessment for the frozen genomic DNA corpus.

The existing DNA dataset contains 50 pre-specified genomic windows across five corpora, with 10 windows per corpus. Each window contains 400,000 nucleotides and produces 800,000 encoded bits under the frozen `acgt_2bit` mapping `A=00,C=01,G=10,T=11`.

Because an individual frozen window contains fewer than the 1,000,000 samples required by the assessment tool, windows were paired deterministically within each corpus:

- w00 + w01;
- w02 + w03;
- w04 + w05;
- w06 + w07;
- w08 + w09.

This produces 25 frozen DNA assessment units: five pairs per corpus, each containing 1,600,000 encoded binary samples.

Pairing scheme:

`BIOENTROPY-HPC-DNA-NIST90B-PAIRING-v1`

For every pair, both constituent bitstreams were regenerated from their frozen reference configs and independently checked against the previously recorded RAW SHA-256 values before concatenation.

| Corpus | Pairs | H min | H mean | H median | H max | H SD | mean P(1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| arabidopsis | 5 | 0.00195300 | 0.06668700 | 0.05356800 | 0.17534700 | 0.06470177 | 0.49961512 |
| bacillus_168 | 5 | 0.00633000 | 0.18786800 | 0.08717300 | 0.45257500 | 0.19037013 | 0.50007537 |
| celegans | 5 | 0.00541500 | 0.02216180 | 0.01035100 | 0.04686100 | 0.02015057 | 0.49921187 |
| ecoli_k12 | 5 | 0.00580200 | 0.02386620 | 0.01423700 | 0.07568600 | 0.02919051 | 0.49979137 |
| yeast_s288c | 5 | 0.00180800 | 0.01756620 | 0.00980400 | 0.04974500 | 0.01964253 | 0.50075713 |

Replication semantics differ deliberately from the synthetic generator campaign: the DNA assessment unit is a deterministic pair of pre-specified genomic windows rather than a different pseudorandom seed.

The concatenation boundary is an analysis construction required to reach the NIST assessment sample size; it is not interpreted as a biologically contiguous sequence unless the underlying manifest establishes such contiguity.

These SP 800-90B values are empirical assessments of the encoded sequence. They do not establish that genomic DNA is a physical entropy source, a compliant NIST entropy source, or a cryptographically unpredictable key source.

Machine-readable artifacts:

- `datasets/manifests/dna_nist90b_pairs.jsonl`
- `datasets/manifests/dna_nist90b_pairs.tsv`
- `results/aggregated/nist90b_dna_pairs.tsv`
- `results/aggregated/nist90b_dna_corpus_summary.tsv`

Figures:

- `results/figures/nist90b_dna_corpora.png`
- `results/figures/nist90b_dna_corpora.pdf`

## 2026-09-09 — ChaCha20-Poly1305 AEAD baseline

Added a ChaCha20-Poly1305 AEAD wrapper using the existing OpenSSL
EVP dependency.

The interface intentionally mirrors the existing Ascon-AEAD128
wrapper:

`encrypt(plaintext, associated_data, key, nonce)`

returns the ciphertext followed by the authentication tag, while

`decrypt(ciphertext_and_tag, associated_data, key, nonce)`

returns the recovered plaintext only after successful
authentication.

Parameters:

- key: 256 bits;
- nonce: 96 bits;
- authentication tag: 128 bits.

Validation covers empty and non-empty plaintexts, round-trip
correctness, deterministic output for identical complete inputs,
ciphertext modification, authentication-tag modification,
associated-data modification, incorrect keys, and malformed
ciphertexts shorter than the authentication tag.

The existing `ChaCha20ReferenceSource` remains a separate component:
it is a deterministic reference bitstream generator used in source
quality experiments. `ChaCha20Poly1305` is instead an authenticated
encryption baseline for the downstream cryptographic integration
campaign.

No claim about source entropy is inferred from successful AEAD
operation. The next integration stage evaluates how frozen RAW and
conditioned source material propagates into derived keys/nonces and
subsequent AEAD use.

## 2026-09-09 — Source-derived AEAD key-material protocol

Defined the downstream key-material layout used to connect the
frozen source campaign with authenticated-encryption experiments.

Each realization contributes a 76-byte experimental material
record with non-overlapping fields:

- bytes 0–15: Ascon-AEAD128 key;
- bytes 16–31: Ascon-AEAD128 nonce;
- bytes 32–63: ChaCha20-Poly1305 key;
- bytes 64–75: ChaCha20-Poly1305 nonce.

The separation prevents the same source bytes from being reused
simultaneously as key material for both cipher baselines.

Both AEAD implementations encrypt the same deterministic 4096-byte
plaintext with the same deterministic 32-byte associated-data
payload.

The probe records SHA-256 identifiers for the complete material
record, keys, nonces and resulting ciphertext-plus-tag values.
It also records material zero-byte count, byte diversity and bit
balance, together with authenticated-decryption round-trip status.

A zero-material control is intentionally retained. Successful AEAD
round-trip with an all-zero key/nonce input demonstrates that
cryptographic API correctness must not be confused with entropy,
unpredictability or secure key generation.

The subsequent campaign compares two material paths:

`frozen RAW source -> 76-byte key-material record`

and

`frozen RAW source -> Ascon-XOF128 conditioning -> 76-byte
key-material record`.

Conditioning is treated as deterministic transformation/whitening.
It is not interpreted as creating entropy that was absent from the
input source.

## 2026-09-10 — Float64 post-collapse key-material conditioning

Evaluated the five pre-specified frozen Logistic float64
realizations previously observed to enter a deterministic
all-zero absorbing state: rep001, rep005, rep007, rep008 and
rep012.

For each realization, the 608 bits beginning exactly at the
previously established collapse index were extracted. All five
post-collapse RAW records consisted of exactly 76 zero bytes.

The 76-byte zero records were then independently processed with
Ascon-XOF128 to produce 76-byte conditioned key-material records.

Observed diversity:

- unique post-collapse RAW inputs: 1/5;
- unique conditioned materials: 1/5;
- unique Ascon-AEAD128 keys: 1/5;
- unique ChaCha20-Poly1305 keys: 1/5;
- unique Ascon ciphertext-plus-tag outputs: 1/5;
- unique ChaCha20-Poly1305 ciphertext-plus-tag outputs: 1/5;
- mean conditioned P(1): 0.516447;
- mean conditioned byte diversity: 65.00/76.

Both AEAD implementations authenticated and decrypted all five
cases successfully.

This result separates statistical appearance from entropy and
diversity. Ascon-XOF128 transforms the visibly degenerate all-zero
input into a substantially more balanced-looking byte sequence,
but deterministic conditioning cannot create different outputs
from identical inputs. Consequently, any collisions in the
conditioned keys, nonces and fixed-message ciphertexts are
propagation of the collapsed input state rather than weaknesses
of Ascon-AEAD128 or ChaCha20-Poly1305.

Successful AEAD round-trip is therefore a correctness property
only and does not imply secure key generation or adequate source
entropy.

This targeted result complements the prefix campaign, where all
20 short RAW prefixes were distinct even for several sources with
very low empirical NIST SP 800-90B estimates. Together, the
experiments demonstrate that neither simple key uniqueness nor
visual/statistical whitening is sufficient evidence of entropy.

Artifacts:

- `results/aggregated/float64_collapse_key_material.tsv`
- `results/aggregated/float64_collapse_conditioned_material.tsv`
- `results/figures/float64_collapse_conditioning.png`
- `results/figures/float64_collapse_conditioning.pdf`

## 2026-09-10 — Integrated source-to-crypto evidence

Integrated the frozen source-characterization and downstream key-material results into a single 10-source descriptive comparison.

| Source | NIST H mean | NIST H min | Dieharder FAIL reps | RAW prefix unique | Conditioned prefix unique |
|---|---:|---:|---:|---:|---:|
| chacha20 | 0.849124 | 0.809165 | 0/20 | 20/20 | 20/20 |
| chen-4d-dcs | 0.855734 | 0.817323 | 0/20 | 20/20 | 20/20 |
| logistic-fixed_q3_29 | 0.000002 | 0.000002 | 20/20 | 20/20 | 20/20 |
| logistic-float32 | 0.000002 | 0.000000 | 20/20 | 20/20 | 20/20 |
| logistic-float64 | 0.854196 | 0.822919 | 5/20 | 20/20 | 20/20 |
| logistic-mpfr_256 | 0.850769 | 0.813907 | 0/20 | 20/20 | 20/20 |
| rule30-cells1024 | 0.859086 | 0.812628 | 0/20 | 20/20 | 20/20 |
| rule30-cells256 | 0.839019 | 0.679895 | 20/20 | 20/20 | 20/20 |
| rule90-cells1024 | 0.000000 | 0.000000 | 20/20 | 20/20 | 20/20 |
| rule90-cells256 | 0.000000 | 0.000000 | 20/20 | 20/20 | 20/20 |

Interpretation:

- All frozen 76-byte prefix-derived key-material records were distinct across the 20 realizations of every source. Therefore absence of observed short-prefix collisions is not sufficient evidence of high entropy.

- This distinction is especially important for sources whose empirical non-IID NIST SP 800-90B estimates were very low despite distinct prefix-derived material.

- Dieharder replicate outcomes and NIST H_original are different measurements and must not be treated as interchangeable randomness or security scores.

- The NIST values characterize the first 1,000,000 output bits, while the frozen Dieharder campaign evaluates much longer streams. The float64 collapse experiment demonstrates why this window-length distinction matters: a prefix may retain high empirical H before a later deterministic absorbing state occurs.

- Ascon-XOF128 can transform visibly structured material into statistically more balanced output but cannot create entropy or diversity absent from identical inputs.

- Successful Ascon-AEAD128 and ChaCha20-Poly1305 round-trip tests demonstrate implementation correctness only. They do not establish secure key generation.

- ChaCha20 remains a deterministic software reference source in this study; high empirical H for that stream is not interpreted as fresh physical entropy.

The integrated figure is descriptive rather than a formal correlation analysis. Only ten heterogeneous deterministic source groups are compared, and the underlying measurements use different test procedures and observation lengths.

Artifacts:

- `results/aggregated/integrated_source_quality.tsv`
- `results/figures/integrated_source_quality.png`
- `results/figures/integrated_source_quality.pdf`

## 2026-09-10 — Three-AEAD source-derived key-material campaign

Extended the frozen source-derived key-material experiment to
three authenticated-encryption baselines while preserving the
previous 76-byte protocol as a separate frozen experiment.

The new protocol is identified as `AEAD3-v1` and uses 104 bytes
from each evaluated stream:

- bytes 0-15: Ascon-AEAD128 key;
- bytes 16-31: Ascon-AEAD128 nonce;
- bytes 32-63: ChaCha20-Poly1305 key;
- bytes 64-75: ChaCha20-Poly1305 nonce;
- bytes 76-91: AES-128-GCM key;
- bytes 92-103: AES-128-GCM nonce.

The same fixed deterministic 4096-byte plaintext and 32-byte
associated-data record are used for all three AEADs. The protocol
is a controlled propagation experiment and is not deployment
guidance for nonce management or cryptographic key generation.

The campaign contains 10 frozen source groups, 20 realizations per
group, and two evaluated modes (RAW and full-stream Ascon-XOF128),
for 400 total records.

All 400 records passed source-stream provenance verification and
successful authenticated round-trip for Ascon-AEAD128,
ChaCha20-Poly1305 and AES-128-GCM.

Across the 20 source/mode groups:

- total 104-byte material collisions: 0;
- total Ascon key collisions: 0;
- total ChaCha20-Poly1305 key collisions: 0;
- total AES-128-GCM key collisions: 1.

The absence of observed collisions among only 20 realizations per
group is not interpreted as evidence of high source entropy,
unpredictability or cryptographic security. This is particularly
important because previous NIST SP 800-90B experiments identified
sources with extremely low empirical non-IID min-entropy estimates
despite distinct short prefix-derived materials.

Likewise, ciphertext uniqueness under fixed plaintext and AAD is
not used as a cipher-security metric. Identical ciphertexts in the
targeted collapse experiment would reflect propagation of
identical experimental key/nonce material rather than a weakness
of the underlying AEAD.

For the full-stream Ascon-XOF128 mode, the evaluated prefix is the
prefix of the XOF output computed from the complete RAW stream.
It must therefore not be interpreted as local conditioning of only
the first 104 RAW bytes.

Artifacts:

- `results/aggregated/source_key_material_aead3_campaign.tsv`
- `results/aggregated/source_key_material_aead3_summary.tsv`

## 2026-09-11 — Float64 pre-collapse output convergence and AEAD3 propagation

A targeted bit-exact audit was performed on the five frozen
Logistic float64 realizations previously observed to enter the
permanent all-zero absorbing output state:

- rep001: collapse bit 5,919,555;
- rep005: collapse bit 16,181,612;
- rep007: collapse bit 21,156,926;
- rep008: collapse bit 10,996,001;
- rep012: collapse bit 9,423,224.

All five complete 16 MiB RAW streams remained distinct by SHA-256,
confirming that the realizations are different full-stream
trajectories.

However, when output sequences were aligned by their independently
measured collapse positions and compared backwards from the first
permanently zero bit, unexpectedly long identical pre-collapse
suffixes were observed.

Pairwise common collapse-aligned suffix lengths:

| Pair | Common suffix |
|---|---:|
| rep001 / rep005 | 3 bits |
| rep001 / rep007 | 2 bits |
| rep001 / rep008 | 2 bits |
| rep001 / rep012 | 2 bits |
| rep005 / rep007 | 2 bits |
| rep005 / rep008 | 2 bits |
| rep005 / rep012 | 2 bits |
| rep007 / rep008 | 8,382,774 bits |
| rep007 / rep012 | 4,379,783 bits |
| rep008 / rep012 | 4,379,783 bits |

The three-realization intersection for rep007, rep008 and rep012
is therefore an identical collapse-aligned output suffix of
4,379,783 bits, corresponding to 547,472 complete bytes plus
7 additional bits.

The rep007/rep008 pair shares an even longer suffix of
8,382,774 bits (1,047,846 complete bytes plus 6 bits).

This establishes that the experimentally observed finite-precision
degeneracy is not restricted to the final all-zero absorbing
region. For three frozen realizations, the emitted binary output
has already converged to the same long collapse-relative tail well
before the permanently zero output begins.

The current evidence is strictly output-level. It does not by
itself establish that the internal floating-point Logistic Map
state x_n is identical across the realizations during the whole
shared suffix. A state-level audit would be required to establish
numeric-state coalescence.

### AEAD3 propagation

The same five collapsed realizations were evaluated using the
104-byte `AEAD3-collapse-v1` protocol with:

- Ascon-AEAD128;
- ChaCha20-Poly1305;
- AES-128-GCM.

Four material variants were evaluated per realization:

- pre-collapse RAW;
- post-collapse RAW;
- locally Ascon-XOF128-conditioned pre-collapse window;
- locally Ascon-XOF128-conditioned post-collapse window.

Observed numbers of unique 104-byte materials among the five
realizations were:

| Variant | Unique materials |
|---|---:|
| pre-collapse RAW | 3/5 |
| pre-collapse local Ascon-XOF128 | 3/5 |
| post-collapse RAW | 1/5 |
| post-collapse local Ascon-XOF128 | 1/5 |

Exactly the same 3/5 -> 3/5 and 1/5 -> 1/5 uniqueness pattern was
observed independently for the derived keys, nonces and
fixed-plaintext/fixed-AAD ciphertext-plus-tag outputs of all three
AEAD algorithms.

For the post-collapse RAW material:

- zero bytes: 104/104;
- unique byte values: 1;
- P(1): 0.

After local Ascon-XOF128 conditioning of the identical zero input:

- zero bytes: 0/104;
- unique byte values: 81;
- P(1): 0.513221.

Thus deterministic conditioning strongly changes the visible
statistical appearance of the collapsed input while preserving
its lack of inter-realization diversity: five identical inputs
remain one unique conditioned output.

All 20 AEAD3 records successfully authenticated and decrypted.
This demonstrates implementation correctness only and must not be
interpreted as evidence of secure key generation.

Ciphertext collisions in this controlled experiment are caused by
identical experimental key/nonce material under fixed plaintext
and AAD. They are not interpreted as weaknesses of Ascon-AEAD128,
ChaCha20-Poly1305 or AES-128-GCM.

Artifacts:

- `results/aggregated/float64_collapse_aead3.tsv`
- `results/aggregated/float64_precollapse_suffix_audit.tsv`
- `results/figures/float64_collapse_aead3.png`
- `results/figures/float64_collapse_aead3.pdf`
- `results/figures/float64_precollapse_suffix_audit.png`
- `results/figures/float64_precollapse_suffix_audit.pdf`

## 2026-09-11 — Three-AEAD local performance baseline

A common local performance benchmark was run for Ascon-AEAD128, ChaCha20-Poly1305 and AES-128-GCM.

The benchmark used:

- message sizes: 64 B, 1 KiB, 64 KiB and 1 MiB;
- associated data: 32 B;
- fixed deterministic benchmark-only keys and nonces;
- 20 timing samples per algorithm/message-size combination;
- rotating algorithm execution order across samples;
- successful authenticated round-trip verification;
- median as the primary estimator;
- IQR for dispersion;
- deterministic 10,000-resample bootstrap 95% CI for the median.

| Algorithm | Message | Encrypt MiB/s | 95% CI | vs Ascon | Decrypt MiB/s | 95% CI | vs Ascon |
|---|---:|---:|---:|---:|---:|---:|---:|
| AES-128-GCM | 64 B | 48.7 | [46.3, 50.1] | 0.37× | 48.3 | [45.8, 50.5] | 0.37× |
| Ascon-AEAD128 | 64 B | 132.1 | [127.8, 140.1] | 1.00× | 129.5 | [124.9, 133.7] | 1.00× |
| ChaCha20-Poly1305 | 64 B | 44.6 | [42.8, 47.0] | 0.34× | 46.9 | [45.5, 47.8] | 0.36× |
| AES-128-GCM | 1 KiB | 673.6 | [650.1, 695.7] | 1.99× | 692.2 | [674.6, 729.2] | 2.04× |
| Ascon-AEAD128 | 1 KiB | 338.5 | [331.3, 342.5] | 1.00× | 339.5 | [337.6, 349.2] | 1.00× |
| ChaCha20-Poly1305 | 1 KiB | 542.8 | [529.5, 551.4] | 1.60× | 544.4 | [535.0, 566.3] | 1.60× |
| AES-128-GCM | 64 KiB | 4128.2 | [3914.3, 4278.8] | 11.24× | 3304.1 | [2823.7, 3683.1] | 9.05× |
| Ascon-AEAD128 | 64 KiB | 367.2 | [356.8, 384.8] | 1.00× | 365.3 | [346.7, 374.4] | 1.00× |
| ChaCha20-Poly1305 | 64 KiB | 1705.6 | [1616.3, 1823.6] | 4.64× | 1696.6 | [1370.1, 1791.8] | 4.64× |
| AES-128-GCM | 1 MiB | 3517.7 | [3263.4, 3601.4] | 9.51× | 3522.5 | [3032.6, 3786.8] | 9.96× |
| Ascon-AEAD128 | 1 MiB | 370.0 | [346.3, 379.9] | 1.00× | 353.6 | [347.2, 368.2] | 1.00× |
| ChaCha20-Poly1305 | 1 MiB | 1546.6 | [1325.0, 1614.3] | 4.18× | 1492.4 | [1385.2, 1693.3] | 4.22× |

Interpretation:

- For the 64-byte payload, Ascon-AEAD128 had the highest observed throughput, indicating substantially lower effective per-call overhead in this implementation.

- At 1 KiB, both OpenSSL-backed AES-128-GCM and ChaCha20-Poly1305 exceeded the Ascon-AEAD128 throughput.

- At 64 KiB, AES-128-GCM encryption throughput was approximately 11.24 times the measured Ascon throughput, while ChaCha20-Poly1305 was approximately 4.64 times.

- At 1 MiB, the corresponding encryption throughput ratios were approximately 9.51 times for AES-128-GCM and 4.18 times for ChaCha20-Poly1305.

- These values characterize the specific local software implementations, compiler/build configuration, operating environment and processor used in this experiment. They must not be interpreted as implementation-independent performance rankings of the underlying algorithms.

- In particular, AES-128-GCM and ChaCha20-Poly1305 are provided through OpenSSL, whereas the Ascon implementation comes from the project's selected Ascon C implementation. Optimization level and available hardware acceleration can therefore materially affect the observed ratios.

- The local WSL measurements are treated as the reproducible single-node performance baseline. Final HPC scalability claims require separate cluster experiments.

- Fixed benchmark keys/nonces were used only to remove key-generation variability from timing. Such nonce reuse is not deployment guidance.

Artifacts:

- `results/aggregated/three_aead_benchmark.tsv`
- `results/aggregated/three_aead_benchmark_summary.tsv`
- `results/aggregated/three_aead_benchmark_environment.txt`
- `results/figures/three_aead_encrypt_throughput.png`
- `results/figures/three_aead_encrypt_throughput.pdf`
- `results/figures/three_aead_decrypt_throughput.png`
- `results/figures/three_aead_decrypt_throughput.pdf`

## 2026-09-11 — Cross-layer source-to-cipher evidence synthesis

The frozen source-characterization, conditioning, key-material and
AEAD experiments were integrated into a single source-level
evidence table.

The synthesis keeps distinct measurement dimensions separate:

- empirical NIST SP 800-90B non-IID H_original;
- conservative replicate-level Dieharder screening outcome;
- RAW and full-stream Ascon-XOF128-conditioned 104-byte material
  diversity;
- derived Ascon-AEAD128, ChaCha20-Poly1305 and AES-128-GCM key
  collision observations;
- targeted Logistic float64 collapse behavior.

A central negative result is that all four source groups with mean
empirical H_original below 0.01 still produced 20/20 distinct
104-byte RAW prefix-derived materials in the frozen AEAD3 campaign:

logistic-fixed_q3_29, logistic-float32, rule90-cells1024, rule90-cells256.

Thus absence of observed collisions in a small set of short
source-derived prefixes is not evidence of high source entropy or
unpredictability.

The targeted Logistic float64 experiment provides the complementary
failure case. Across the five frozen collapsed realizations:

- pre-collapse RAW material diversity: 3/5;
- pre-collapse local Ascon-XOF128 diversity: 3/5;
- post-collapse RAW material diversity: 1/5;
- post-collapse local Ascon-XOF128 diversity: 1/5.

Therefore deterministic conditioning changes visible statistical
properties but does not restore inter-realization diversity lost
through deterministic source convergence.

The three AEAD algorithms successfully authenticated and decrypted
all evaluated records. Correct AEAD operation is consequently kept
separate from claims about source entropy or key-generation
security.

Performance measurements are maintained in a separate cipher-level
table because cipher implementation throughput is not a property
of the entropy source.

Artifacts:

- `results/aggregated/cross_layer_source_summary.tsv`
- `results/aggregated/cross_layer_cipher_performance.tsv`
