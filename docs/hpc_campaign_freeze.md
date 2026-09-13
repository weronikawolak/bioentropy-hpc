# Frozen HPC Campaign Protocol

## Status

This document freezes the HPC campaign design before access to the
target cluster.

The code baseline is identified by the annotated Git tag:

`hpc-ready-v1`

Cluster-dependent resource values are intentionally resolved only
after the cluster preflight.

## Scientific scope

The HPC experiment evaluates workflow-level ensemble scalability.

One workload is one independent frozen experiment configuration.

The experiment does not claim parallel execution of one internal
generator trajectory.

Performance results must remain separate from entropy, statistical
randomness, and cryptographic-security results.

## Frozen profiles

Two workload profiles are required:

1. `ctr-drbg`
   - AES-256 CTR_DRBG deterministic reference;
   - conventional reference workload.

2. `logistic-mpfr`
   - Logistic Map using MPFR-256 arithmetic;
   - expensive precision-sensitive numerical workload.

Both profiles must be evaluated independently.

## Task-count rule

The scaling task set uses powers of two:

`1, 2, 4, 8, ... P_max`

where `P_max` is the largest power of two that is practical and
permitted by the target cluster allocation.

The campaign must always contain the `p=1` baseline.

The task set is frozen after cluster preflight and must then remain
unchanged within the final campaign.

## Workload-count rule

Let:

`K = 3`

represent the number of independent workload items per worker at the
largest strong-scaling point.

For the final task set:

`strong_items = K * P_max`

and:

`weak_items_per_task = K`

This guarantees that the strong workload count is divisible by every
power-of-two task count in the campaign.

It also makes the largest strong-scaling point and largest weak-scaling
point contain the same total number of independent workload items.

## Output-size calibration

The bitstream size per workload is cluster-dependent because CTR_DRBG
and MPFR-256 have substantially different computational costs.

For each profile separately:

1. run only `p=1`;
2. use one workload item;
3. increase `output_bits` by powers of two;
4. choose the smallest power-of-two output size whose workload runtime
   is approximately 5--15 seconds on the target compute node.

The selected value is then frozen for that profile.

The same `output_bits` value must be used for all strong and weak
scaling points of that profile.

Calibration runs are infrastructure measurements and are excluded from
the final scaling dataset.

## Strong scaling

For one profile:

- `strong_items = 3 * P_max`;
- total workload remains fixed;
- `p` varies over the frozen task set;
- three independent timing repetitions are performed per point.

Primary quantities:

`S_p = T_1 / T_p`

`E_p = S_p / p`

where `T_p` is the median full-job wall time.

## Weak scaling

For one profile:

- `weak_items_per_task = 3`;
- total workload is `3 * p`;
- three independent timing repetitions are performed per point.

Weak-scaling efficiency:

`E_p = T_1 / T_p`

where `T_p` is the median full-job wall time.

## Repetitions

Exactly three timing repetitions are required for every final scaling
point.

The primary statistic is the median.

Minimum and maximum wall times are retained as descriptive variability
information.

Failed or incomplete repetitions must not be silently included in an
aggregate.

## Timing boundary

Elapsed time is calculated from a monotonic clock around the complete
parallel workload execution.

UTC timestamps are provenance metadata only.

Per-rank timings are retained for imbalance diagnostics.

## Required execution sequence

The cluster execution order is:

1. checkout `hpc-ready-v1`;
2. run strict cluster preflight;
3. record cluster environment;
4. determine the permitted power-of-two task set;
5. calibrate `output_bits` separately for both profiles;
6. freeze the final campaign parameters;
7. perform a tiny `p=1` / `p=2` Slurm smoke;
8. generate final manifests;
9. execute CTR_DRBG strong scaling;
10. execute CTR_DRBG weak scaling;
11. execute MPFR-256 strong scaling;
12. execute MPFR-256 weak scaling;
13. validate rank coverage and completeness;
14. aggregate results;
15. generate final scaling figures;
16. record all final parameters and provenance.

## No-rerun rule

Once the final campaign begins, completed valid points must not be
rerun merely because their measured performance is unexpected.

A rerun is permitted only for a documented execution defect, such as:

- job failure;
- incomplete rank output;
- incorrect manifest;
- cluster failure;
- violated frozen parameters.

Any such rerun must be explicitly recorded.
