# BioEntropy HPC — Project Status

Updated: 2026-09-11

| Phase | Status | Notes |
|---|---|---|
| 0. Protocol freeze | DONE | Frozen deterministic campaign methodology and provenance rules |
| 1. Reproducible/HPC framework | PARTIAL | Local reproducible framework complete; cluster execution pending |
| 2. Reference generators | DONE | ChaCha20 and AES-256 CTR_DRBG deterministic reference sources complete |
| 3. Logistic Map | DONE | float32, float64, Q3.29, MPFR-256, periodicity/collapse analysis |
| 4. Cellular automata | DONE | Rule 30/90, 256/1024 cells |
| 5. DNA | DONE | 50 genomic windows and paired NIST SP 800-90B units |
| 6. Hyperchaotic source | DONE | Chen 4D DCS implementation and screening |
| 7. Statistical stack | DONE LOCAL | Basic metrics, NIST SP 800-90B, Dieharder and targeted TestU01 SmallCrush complete; standalone NIST STS frozen as an optional extension rather than required core work |
| 8. Large source screening | DONE LOCAL | Frozen 200-realization RAW campaign complete |
| 9. Conditioning | DONE | Ascon-XOF128 campaign and targeted collapse conditioning complete |
| 10. Crypto baselines | DONE | Ascon-AEAD128, ChaCha20-Poly1305, AES-128-GCM and common performance baseline |
| 11. Published DNA cipher reproduction | DONE | Fetteha 2023 reproduction and controls |
| 12. End-to-end analysis | DONE LOCAL | Source → entropy → conditioning → key/nonce → AEAD evidence integrated |
| 13. HPC scalability | HPC-BLOCKED | Strong/weak scaling, speedup and parallel efficiency require cluster |
| 14. Statistics and figures | MOSTLY DONE | Main descriptive statistics and local figures complete; final paper curation remains |
| 15. Final reproduction | PARTIAL / HPC-BLOCKED | Final frozen reproduction after remaining local and HPC experiments |

## Main remaining local work

4. Curate final paper-ready figures and tables.
5. Freeze final local protocol/results.

## Remaining HPC work

- Execute cluster-scale source-generation campaigns as required.
- Measure strong scaling.
- Measure weak scaling.
- Report speedup and parallel efficiency.
- Record node/compiler/runtime environment.
- Perform final reproduction run.

## Key completed scientific findings

- Very low empirical non-IID entropy can coexist with 20/20 distinct short source-derived materials.
- Logistic float64 finite-precision collapse can occur after apparently high-entropy prefixes.
- Three frozen float64 realizations share a 4,379,783-bit collapse-aligned output suffix.
- Deterministic Ascon-XOF128 conditioning improves visible statistical appearance but preserves lost inter-realization diversity.
- Identical source-derived key/nonce material propagates to identical fixed-message AEAD outputs across Ascon-AEAD128, ChaCha20-Poly1305 and AES-128-GCM.
- Successful authenticated round-trip does not establish secure key generation.
- Local cipher performance strongly depends on payload size and implementation/platform characteristics.


## Local scope freeze

Standalone NIST STS is classified as an optional extension rather
than required core work.

This is a scope decision, not an equivalence claim:

- NIST SP 800-90B is retained for empirical entropy estimation;
- Dieharder is retained for broad statistical screening;
- TestU01 SmallCrush is retained as an independent targeted
  statistical battery;
- standalone NIST STS would provide an additional overlapping
  randomness-testing view but is not required for the frozen
  local contribution set.

No new large local source-generation or randomness-test campaigns
are planned before HPC execution unless a concrete validation defect
is discovered.

The remaining required work is therefore:

- final paper table/figure curation;
- HPC strong/weak scaling;
- environment and reproducibility capture on the cluster;
- final frozen reproduction.


## HPC execution readiness

The complete HPC execution harness is prepared locally.

Available components include:

- deterministic workload generation;
- static non-overlapping rank sharding;
- local parallel dry-run;
- strong-scaling protocol;
- weak-scaling protocol;
- three-repetition aggregation;
- Slurm execution template;
- cluster preflight validation;
- dry-run-first campaign submitter;
- result provenance;
- speedup and parallel-efficiency analysis.

The submitter does not submit jobs unless the explicit `--submit`
flag is supplied.

Actual HPC scaling measurements remain blocked only by cluster
access and cluster-specific Slurm parameters.
