# Experiment Result Dataset

## Per-experiment output

Each completed experiment produces one JSON result file.

Example:

results/metrics/smoke-test-001_rep0000.json

The JSON representation is intended for:

- experiment-level inspection
- debugging
- reproducibility
- failed-job investigation

## Aggregated dataset

Experiment JSON files are aggregated into:

results/aggregated/results.parquet

Apache Parquet is the primary analytical format used for large
experimental campaigns.

The dataset contains one row per unique:

experiment_id + replicate_id

combination.

## Validation

The aggregation process validates:

- schema version
- required result fields
- output bit count
- zero/one consistency
- probability ranges
- bias range
- Shannon entropy range
- seed length
- SHA-256 fingerprint length
- duplicate experiment/replicate combinations

Malformed experiment results are rejected instead of being silently
included in the analytical dataset.

## Reproducibility

Each row contains:

- experiment identifier
- replicate identifier
- source type
- output size
- execution chunk size
- derived experiment seed
- SHA-256 bitstream fingerprint
- basic statistical metrics

This allows analytical results to be traced back to individual
experiment executions.
