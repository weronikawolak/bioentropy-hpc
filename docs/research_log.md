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
