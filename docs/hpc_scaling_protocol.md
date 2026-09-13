# HPC Ensemble Scaling Protocol

## Scope

The HPC experiments evaluate computational scalability of independent
experiment workloads.

They do not measure entropy, randomness quality, or cryptographic
security.

They also do not claim that a single Logistic Map, cellular automaton,
or cryptographic generator realization is internally parallelized.

## Parallelism model

The unit of parallel work is one independent experiment configuration.

Static assignment follows:

`workload_index mod world_size == rank`

Therefore each rank executes a disjoint subset of the frozen workload
ensemble.

The reported scaling is consequently:

- ensemble scaling;
- workflow-level scaling;
- campaign throughput scaling.

It must not be described as speedup of one individual generator
realization.

## Ensemble strong scaling

A fixed total workload ensemble is executed using increasing numbers
of workers.

For worker count `p`:

`S_p = T_1 / T_p`

and:

`E_p = S_p / p`

where `T_p` is the median job-level wall time.

## Ensemble weak scaling

The number of independent workload items per worker remains fixed.

For worker count `p`:

`total workload = p * workload_per_worker`

Weak-scaling efficiency is:

`E_p = T_1 / T_p`

## Timing

Elapsed durations are measured using a monotonic high-resolution
clock.

Absolute UTC timestamps are recorded only as provenance and are not
used to calculate benchmark duration.

The primary timing boundary surrounds completion of the full workload
ensemble.

Per-rank timings are retained for load-imbalance diagnostics.

## Repetitions

The final cluster campaign uses three timing repetitions per scaling
point.

The median wall time is the primary statistic.

Minimum and maximum values are retained as descriptive variability
information.

## Planned profiles

Core profiles:

- AES-256 CTR_DRBG deterministic reference;
- Logistic Map MPFR-256.

CTR_DRBG provides a conventional deterministic reference workload.

MPFR-256 represents a substantially more expensive numerical
chaotic-source workload.

## Interpretation boundary

Performance results must remain separate from statistical quality
results.

Higher throughput or better scaling does not imply higher entropy,
better statistical randomness, or stronger cryptographic security.
