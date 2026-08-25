# Logistic Map Implementation Conventions

## Recurrence

The logistic map is evaluated as:

x_{n+1} = (r * x_n) * (1 - x_n)

The parenthesization is intentional.

Publication builds must not use fast-math transformations.

## Initial state

Two modes are supported:

- `explicit`
- `derived_from_seed`

For `derived_from_seed`, the first 64 bits of the deterministic
experiment seed are interpreted as a big-endian integer.

The upper 53 bits are retained and scaled by 2^-53 to obtain a
binary64-representable value in the open interval (0, 1).

## Burn-in

If `burn_in = B`, the recurrence is evaluated B times before output
generation starts.

The first emitted bit is derived from x_{B+1}.

## Threshold extraction

For each generated state:

- x < 0.5  -> bit 0
- x >= 0.5 -> bit 1

## Bit packing

Bits are packed most-significant-bit first.

The first generated bit occupies bit 7 of the first output byte.

## Floating-point reproducibility

The initial implementation uses IEEE-754 binary64 (`double`).

Compiler optimizations that allow unsafe floating-point
reassociation are disabled for the core implementation.

Exact toolchain, compiler flags, architecture, and container version
must be recorded for publication experiments.
