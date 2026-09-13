# HPC Scaling Protocol

## Scope

HPC experiments evaluate scalability and execution performance.
They do not provide additional evidence of entropy or
cryptographic security.

## Workload model

Each independent experiment configuration is one workload item.

Workloads are deterministically distributed among workers using:

`workload_index mod world_size == rank`

This guarantees complete, non-overlapping static partitioning.

## Strong scaling

Strong scaling keeps total work fixed while increasing the number
of Slurm tasks.

For each process count:

- the same frozen manifest is used;
- the same workload limit is used;
- three independent timing repetitions are executed.

Reported quantities:

- median job wall time;
- throughput;
- speedup `S_p = T_1 / T_p`;
- parallel efficiency `E_p = S_p / p`.

## Weak scaling

Weak scaling keeps the number of workload items per task fixed.

For `p` tasks and `w` workload items per task:

`total_workloads = p * w`.

Three timing repetitions are executed per process count.

Reported quantities:

- median job wall time;
- aggregate throughput;
- weak-scaling efficiency `E_p = T_1 / T_p`.

## Timing boundary

The primary timing measure is job-level wall time surrounding the
parallel `srun` execution.

Per-rank timings are retained for imbalance diagnostics but are not
summed to obtain application wall time.

## Repetitions

The final HPC campaign uses three repetitions per scaling point.

The median is the primary summary statistic.

Minimum and maximum times are retained as descriptive variability
information.

## Provenance

Each HPC result records:

- Git commit;
- profile;
- scaling mode;
- task count;
- repetition;
- manifest;
- workload limit;
- total generated bits;
- Slurm job ID;
- node list;
- CPUs per task;
- job wall time.

Cluster-specific environment information will be captured during the
actual HPC campaign.

## Profiles

The planned core profiles are:

- AES-256 CTR_DRBG deterministic reference;
- Logistic Map MPFR-256.

The cryptographic reference provides a comparatively conventional
compute workload.

MPFR-256 represents the higher-cost precision-sensitive chaotic
generator.

## Interpretation

Scaling performance must not be interpreted as a randomness,
entropy, or security metric.
