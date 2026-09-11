# BioEntropy HPC — Project Status

Updated: 2026-09-11

| Phase | Status | Notes |
|---|---|---|
| 0. Protocol freeze | DONE | Frozen deterministic campaign methodology and provenance rules |
| 1. Reproducible/HPC framework | PARTIAL | Local reproducible framework complete; cluster execution pending |
| 2. Reference generators | PARTIAL | ChaCha20 complete; CTR_DRBG remains |
| 3. Logistic Map | DONE | float32, float64, Q3.29, MPFR-256, periodicity/collapse analysis |
| 4. Cellular automata | DONE | Rule 30/90, 256/1024 cells |
| 5. DNA | DONE | 50 genomic windows and paired NIST SP 800-90B units |
| 6. Hyperchaotic source | DONE | Chen 4D DCS implementation and screening |
| 7. Statistical stack | PARTIAL | Basic metrics, NIST SP 800-90B and Dieharder complete; TestU01 remains; standalone NIST STS optional/remaining depending final scope |
| 8. Large source screening | DONE LOCAL | Frozen 200-realization RAW campaign complete |
| 9. Conditioning | DONE | Ascon-XOF128 campaign and targeted collapse conditioning complete |
| 10. Crypto baselines | DONE | Ascon-AEAD128, ChaCha20-Poly1305, AES-128-GCM and common performance baseline |
| 11. Published DNA cipher reproduction | DONE | Fetteha 2023 reproduction and controls |
| 12. End-to-end analysis | DONE LOCAL | Source → entropy → conditioning → key/nonce → AEAD evidence integrated |
| 13. HPC scalability | HPC-BLOCKED | Strong/weak scaling, speedup and parallel efficiency require cluster |
| 14. Statistics and figures | MOSTLY DONE | Main descriptive statistics and local figures complete; final paper curation remains |
| 15. Final reproduction | PARTIAL / HPC-BLOCKED | Final frozen reproduction after remaining local and HPC experiments |

## Main remaining local work

1. Add CTR_DRBG reference source.
2. Add targeted TestU01 validation.
3. Decide whether standalone NIST STS is required for the final scope.
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
