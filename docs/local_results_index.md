# Local Results Index

This document indexes the frozen local evidence used before HPC
scalability experiments.

## Source quality

- `results/aggregated/nist90b_prefix1m_all_sources.tsv`
- `results/aggregated/dieharder_campaign_full20.tsv`
- `results/aggregated/integrated_source_quality.tsv`
- `results/aggregated/testu01_smallcrush_detailed_summary.tsv`
- `results/aggregated/testu01_smallcrush_suspect_tests.tsv`

## Conditioning

- RAW vs Ascon-XOF128 Dieharder comparison
- Logistic float64 collapse-aligned NIST SP 800-90B analysis
- targeted pre/post-collapse key-material conditioning analysis

## Crypto propagation

- `results/aggregated/source_key_material_campaign.tsv`
- `results/aggregated/source_key_material_aead3_campaign.tsv`
- `results/aggregated/source_key_material_aead3_summary.tsv`
- `results/aggregated/float64_collapse_aead3.tsv`
- `results/aggregated/float64_precollapse_suffix_audit.tsv`

## Cross-layer synthesis

- `results/aggregated/cross_layer_source_summary.tsv`
- `results/aggregated/cross_layer_source_summary_testu01.tsv`
- `results/aggregated/cross_layer_descriptive_stats.tsv`
- `results/tables/paper_local_source_summary.tsv`
- `results/tables/paper_local_source_summary.md`

## Cipher performance

- `results/aggregated/three_aead_benchmark.tsv`
- `results/aggregated/three_aead_benchmark_summary.tsv`
- `results/aggregated/three_aead_benchmark_environment.txt`
- `results/aggregated/cross_layer_cipher_performance.tsv`

## Main figures

- `results/figures/nist90b_float64_collapse_aligned.pdf`
- `results/figures/integrated_source_quality.pdf`
- `results/figures/float64_collapse_aead3.pdf`
- `results/figures/float64_precollapse_suffix_audit.pdf`
- `results/figures/three_aead_encrypt_throughput.pdf`
- `results/figures/three_aead_decrypt_throughput.pdf`
- `results/figures/cross_layer_source_profile.pdf`
- `results/figures/paper_cross_layer_overview.pdf`

## Scope boundary

Standalone NIST STS is frozen as an optional extension.

No further large local source-generation or statistical campaigns
are required before HPC unless validation identifies a concrete
defect.

The remaining required experimental work is HPC scalability and
final reproduction.
