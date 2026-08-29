# Chen et al. (2026) — low-complexity 4D discrete chaotic system

## Reference

Han Chen, Qingye Huang, Yingjie Su, Lezhu Chen, Baoyi Liao,
Linqing Huang, and Changwen Chen.

"A Low-Complexity 4D Discrete Chaotic System for Secure Image
Encryption Based on Reversible Neural Network."

Entropy, 28(7), 753, 2026.

DOI: 10.3390/e28070753

Published: 1 July 2026.

## Role in this project

The publication introduces a low-complexity four-dimensional
discrete chaotic system, referred to as 4D-DCS.

The system is used in this project as a modern published
high-dimensional chaotic candidate randomness source.

The image-encryption construction proposed by Chen et al. is
not reproduced here. Only the underlying dynamical system is
used.

The source is therefore evaluated independently using the same
project pipeline as Logistic Map, cellular automata, DNA, and
the deterministic ChaCha20 reference.

## Published dynamical system

The implemented recurrence follows Equation (5) of Chen et al.

x(k+1) = mod((1.7 + exp(r)) * x(k) + 0.1 * y(k), 1)

y(k+1) = mod((0.4 + exp(r)) * y(k) - 0.2 * z(k), 1)

z(k+1) = mod(0.3 * x(k) + (0.5 + exp(r)) * z(k), 1)

w(k+1) = mod(0.1 * y(k) + (1.8 + exp(r)) * w(k), 1)

All four coordinates for iteration k+1 are calculated from the
same state at iteration k.

For the reference smoke profile:

r = 5

x0 = 0.1
y0 = 0.2
z0 = 0.3
w0 = 0.4

burn-in = 1000 iterations

These values follow the representative configuration used in
the publication.

## Project-defined extraction profile

The bit-extraction rule used by BioEntropy-HPC is deliberately
simpler than the downstream processing used by Chen et al.

For each coordinate after a state transition:

coordinate >= 0.5 -> 1
coordinate <  0.5 -> 0

The output order is:

x, y, z, w

Each iteration therefore produces four bits.

Two successive iterations form one byte, with the first
iteration occupying the most significant four bits.

This extraction profile is project-defined. It must not be
described as an exact reproduction of the PRNG or image
encryption procedure from Chen et al.

The purpose is to expose the raw numerical dynamics to the same
controlled statistical pipeline used for the other candidate
sources.

## Arithmetic profile

The initial implementation uses IEEE-754 binary64 arithmetic.

Mathematical modulo 1 is implemented as:

value - floor(value)

rather than fmod(value, 1), so negative intermediate values map
to the interval [0, 1).

No cryptographic post-processing is performed inside the source.

Ascon-XOF128 conditioning remains a separate experimental stage.

## Scientific positioning

Chen et al. report hyperchaotic characteristics based on
Lyapunov-exponent analysis and additional numerical tests.

Within this project the source should therefore be described as
a published 4D discrete system reported as hyperchaotic by its
authors.

Passing randomness tests or exhibiting hyperchaotic dynamics
must not be interpreted as proof of cryptographic entropy,
unpredictability, or secrecy.


## Finite-precision periodicity probe

The binary64 reference configuration was subjected to an
exact-state cycle search.

The comparison uses exact equality of the complete
four-dimensional floating-point state:

(x, y, z, w)

For r=5.0 and initial state
(0.1, 0.2, 0.3, 0.4), no exact recurrence was detected within
10,000,000 state transitions.

The same result was obtained when the search started after the
standard 1000-transition burn-in.

The appropriate interpretation is therefore:

"No exact recurrence was detected within 10^7 transitions."

The result does not establish mathematical or digital
aperiodicity.

