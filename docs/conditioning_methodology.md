# Conditioning methodology

## Ascon-XOF128

The paired experiments use `ascon_xof128` conditioning.

For each conditioned realization, the corresponding frozen RAW configuration is preserved. Source parameters, explicit initial states, replicate IDs, master seeds, output lengths, and execution chunk sizes remain unchanged. The only experimental change is:

`conditioning.mode: raw` -> `conditioning.mode: ascon_xof128`

## Input and output semantics

Source generation may internally use execution chunks, but these chunks are not conditioned independently.

For Ascon-XOF128, the complete RAW realization is accumulated and supplied as one input message to the conditioner. The XOF output length equals the RAW input length.

For the Dieharder campaign:

- RAW input: 16 MiB
- Ascon-XOF128 invocations per realization: 1
- conditioned output: 16 MiB

## Provenance

The SHA-256 digest of the complete pre-conditioning stream is stored as `conditioning.input_sha256`. The conditioned stream has a separate output SHA-256.

This enables exact pairing of RAW and conditioned realizations.

## Interpretation

Improved statistical-test results after conditioning indicate improved statistical appearance of the output. They do not demonstrate creation of entropy, increased physical entropy, or unpredictability absent from the input.
