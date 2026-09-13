# TestU01 SmallCrush provenance

## Execution semantics

The TestU01 adapter evaluates bytes obtained directly from
`RandomnessSource`.

It does not execute the framework conditioning pipeline.

Therefore all TestU01 SmallCrush experiments represent RAW source
screening.

## Historical configuration repair

The original frozen TestU01 subset generator selected several source
templates originating from Ascon-XOF128 conditioning campaigns.

Those YAML files could therefore retain:

`conditioning.mode: ascon_xof128`

even though the TestU01 adapter bypassed conditioning and consumed the
underlying `RandomnessSource` directly.

This was a provenance inconsistency, not a change in the tested
bitstream.

The frozen TestU01 configurations were subsequently normalized to:

`conditioning.mode: raw`

The repair preserves the original configuration SHA-256 together with
the repaired SHA-256 in:

`results/aggregated/testu01_provenance_repair.tsv`

No SmallCrush battery was rerun as part of this metadata repair.

## Interpretation

SmallCrush results are statistical screening results for one frozen
deterministic realization per selected generator.

They are not:

- entropy estimates;
- cryptographic security proofs;
- independent Bernoulli trials;
- population-level failure-rate estimates.

The number reported as `SmallCrush suspect statistics` counts
individual statistics reported by TestU01 as having suspect p-values.
It must not be interpreted as a synthetic randomness score.
