# DNA subsequence image cipher — reproduction target

## Reference

Qiang Zhang, Xianglian Xue, Xiaopeng Wei,
"A Novel Image Encryption Algorithm Based on DNA Subsequence Operation",
The Scientific World Journal, 2012, Article ID 286741.

DOI: 10.1100/2012/286741

## Scope of reproduction

The implementation aims to reproduce the algorithm described in the paper,
not to claim that the construction provides modern cryptographic security.

The algorithm is used as the published DNA-based image-cipher comparator
against the standardized Ascon-AEAD128 baseline.

## Image domain

Primary reproduction target:

- 8-bit grayscale image
- original experiment: 256 x 256 Lena
- later benchmark workloads may use additional grayscale images

## DNA encoding

Paper mapping:

- 00 -> G
- 01 -> A
- 10 -> T
- 11 -> C

Watson-Crick complement:

- A <-> T
- C <-> G

Paper validation example:

75 decimal
= 01001011 binary
= A G T C

## Chaotic maps

1D Logistic:

x[n+1] = mu * x[n] * (1 - x[n])

2D Logistic:

x[i+1] =
    mu1 * x[i] * (1 - x[i])
    + gamma1 * y[i]^2

y[i+1] =
    mu2 * y[i] * (1 - y[i])
    + gamma2 * (
        x[i]^2
        + x[i] * y[i]
    )

Paper experimental parameters:

x0     = 0.95
mu1    = 3.2
gamma1 = 0.17
y0     = 0.25
mu2    = 3.3
gamma2 = 0.14

The paper uses 1000 iterations of the 2D map before deriving
parameters for four 1D Logistic maps.

## DNA subsequence lengths

Four DNA planes are partitioned using nominal subsequence lengths:

- l1 = 128
- l2 = 64
- l3 = 32
- l4 = 8

## Published operations

Encryption uses:

- deletion
- elongation/truncation
- transformation
- complement
- DNA decoding
- bit-plane recombination

Decryption uses the inverse operations, including insertion.

## Reproducibility notes

The publication contains several notation inconsistencies.

Examples:

1. gamma1 and gamma2 are described as fixed in one section,
   while the key-space discussion counts them as secret-key components.

2. The experimental parameter listing contains a notation typo
   where mu1 appears twice; the second value is interpreted as mu2.

3. The precise extraction of the eight values after the 1000-step
   2D Logistic warm-up must be documented explicitly in this
   implementation once the published procedure is resolved.

No undocumented interpretation should be silently introduced.

---

# Derivation of the four 1D Logistic maps

Section 3.1 of the publication states that after the 2D Logistic
generation stage eight values x1...x8 are used to construct four
one-dimensional Logistic maps.

The published parameter transformation is:

map 1:

initial state = x1

u1 = 3.9 + 0.1 * x2


map 2:

initial state = x3

u2 = 3.9 + 0.1 * x4


map 3:

initial state = x5

u3 = 3.9 + 0.1 * x6


map 4:

initial state = x7

u4 = 3.9 + 0.1 * x8

Each resulting one-dimensional Logistic sequence has length m * n
for an m by n image.

Important reproduction note:

The publication says that the eight values are produced after iterating
the 2D Logistic system 1000 times, but the wording does not completely
remove ambiguity about the exact extraction indexing of x1...x8.

The implementation must therefore document explicitly which eight
successive state values are used.

This interpretation will be isolated in a dedicated function so that
it can be changed without modifying the rest of the cipher if a more
precise interpretation is later established.
