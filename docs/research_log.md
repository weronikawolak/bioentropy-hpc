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
