# ChaCha20 Reference Generator Conventions

## Purpose

ChaCha20 is used as a deterministic cryptographic reference generator.

It is not treated as a physical entropy source.

Its purpose is to provide a high-quality cryptographic baseline against
which the statistical properties of the candidate bio-inspired sources
can be compared.

## Input seed

Each experiment supplies a deterministic 256-bit experiment seed.

## Key derivation

The 256-bit ChaCha20 key is:

SHA-256(
    "BIOENTROPY-HPC-CHACHA20-KEY-v1"
    || experiment_seed
)

## Nonce derivation

A separate domain is used for nonce derivation:

SHA-256(
    "BIOENTROPY-HPC-CHACHA20-NONCE-v1"
    || experiment_seed
)

The first 64 bits of this digest form the ChaCha20 nonce.

Domain separation ensures that key and nonce material are not obtained
by directly reusing the same bytes.

## IV layout

The implementation targets the OpenSSL 3.x EVP_chacha20 interface.

The 128-bit IV is:

counter64_le || nonce64

where:

- counter64_le is a 64-bit little-endian initial counter
- nonce64 is the derived 64-bit nonce

The default initial counter is 0.

## Output generation

ChaCha20 is applied to an all-zero byte stream.

Because ChaCha20 is a stream cipher, encrypting zeros directly exposes
the generated keystream.

## Reproducibility

Identical:

- experiment seed
- initial counter

must produce the same byte stream.

Execution chunk size must not alter the output.

## Interpretation

Passing statistical randomness tests does not establish that another
candidate source is cryptographically equivalent to ChaCha20.

ChaCha20 serves only as a deterministic cryptographic reference
generator in the experimental framework.
