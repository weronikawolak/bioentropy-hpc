# Fetteha, Sayed & Said 2023 — Lightweight DNA Image Cipher

## Publication

Marwan A. Fetteha, Wafaa S. Sayed, Lobna A. Said

"A Lightweight Image Encryption Scheme Using DNA Coding and Chaos"

Electronics, 2023, 12(24), 4895.

DOI:

10.3390/electronics12244895

Published:

5 December 2023

## Role in BioEntropy HPC

This publication is the primary published DNA-based lightweight
cryptographic comparator selected for reproduction in BioEntropy HPC.

It replaces the previously considered Zhang et al. 2012 cipher as the
implementation target.

Zhang et al. 2012 remains relevant only as earlier related work.

## Reason for selection

The paper is substantially better aligned with the BioEntropy HPC
research question because it explicitly targets lightweight image
encryption and combines:

- DNA coding,
- deterministic chaos,
- pseudorandom sequence generation,
- image-dependent processing,
- low-complexity implementation.

The authors additionally provide a hardware FPGA implementation and
evaluate both security-related image metrics and implementation
efficiency.

This makes the construction a more appropriate comparator for the
standardized Ascon-AEAD128 lightweight baseline.

## Input

The proposed algorithm operates on grayscale images.

## Main building blocks reported by the publication

The construction uses:

- a 256-bit secret key,
- Lorenz chaotic dynamics,
- DNA encoding and decoding,
- image pixel summation,
- iterative encryption,
- feedback from the previous encrypted output.

## Pixel-dependent iteration count

The sum of all image pixels is calculated:

P_sum = sum(image pixels)

and:

P = P_sum mod 16

The value P controls the number of encryption iterations.

## Key structure

The 256-bit input key is divided into:

8 x 32-bit key words.

These values are combined using XOR operations to generate initial
conditions for the Lorenz chaotic system.

## Chaotic generator

The publication uses a digitally evaluated Lorenz system.

The Euler discretization is:

X[n+1] =
    X[n] + h * sigma * (Y[n] - X[n])

Y[n+1] =
    Y[n] + h * (
        rho * X[n]
        - Y[n]
        - X[n] * Z[n]
    )

Z[n+1] =
    Z[n] + h * (
        X[n] * Y[n]
        - beta * Z[n]
    )

The hardware-oriented parameters reported in the paper are:

h = 2^-7

sigma = 8

rho = 16

beta = 2

These power-of-two parameters allow multiplication operations to be
implemented efficiently using shifts in hardware.

## Chaotic warm-up

The first:

200

generated chaotic outputs are discarded before encryption use.

## DNA processing

Chaotic output bits are used to select DNA encoding and decoding rules
for 2-bit portions of each image pixel.

The publication uses the eight valid complementary DNA coding rules.

The exact rule-selection and bit-extraction procedure must be reproduced
carefully from the article before implementation.

## Pixel confusion

The value P also determines image orientation.

The paper specifies that one parity of P processes the image normally,
while the other processes a flipped image.

This is intended as a low-complexity pixel-confusion mechanism.

## Diffusion / feedback

After DNA encoding and decoding, the resulting 8-bit value is XORed
with:

- chaotic Z-derived bits,
- a mask containing the previous encrypted output.

The mask is initially zero.

This introduces ciphertext feedback between pixels.

## Evaluation reported by the authors

The paper evaluates:

- histogram/statistical behavior,
- adjacent-pixel correlation,
- information entropy,
- NPCR,
- UACI,
- known-plaintext black/white image tests,
- key space,
- NIST SP 800-22.

NPCR and UACI are calculated as the mean of 50 iterations.

## Hardware implementation

The publication reports an implementation on a Xilinx Genesys 2 FPGA.

Reported maximum frequency:

110.8 MHz

Reported throughput:

147.73 Mbps

The authors report LUT, FF, and DSP utilization below 1% on the selected
FPGA.

These hardware results will be used only as publication context.

They must not be directly compared numerically with BioEntropy HPC CPU
throughput without explicitly noting the different execution platforms.

## Reproduction policy

BioEntropy HPC will reproduce the software-visible encryption algorithm,
not the FPGA RTL implementation.

Every article-derived component must be linked to its publication
section.

Any detail that cannot be uniquely determined from the publication will
be documented explicitly before an implementation interpretation is
introduced.

The reproduced DNA-based cipher is a comparison target, not an original
contribution of BioEntropy HPC.

---

## Implementation status — core milestone

Implemented and tested:

- P_sum calculation,
- P = P_sum mod 16,
- 256-bit key split into 8 x 32-bit words,
- XOR-based raw initial-condition derivation,
- one Euler-discretized Lorenz step.

The DNA coding stage is intentionally implemented separately in the
next milestone so that Table 1 can be reproduced and tested exactly.

---

## Implementation status — chaotic control extraction

Implemented and tested from Algorithm 1:

- deterministic advancement of the Lorenz system,
- discard of the first 200 generated states,
- first usable state at iteration 201,
- Xbin1 through Xbin4 extraction,
- Ybin1 through Ybin4 extraction,
- Zbin extraction,
- MATLAB-compatible fix() semantics,
- MATLAB-compatible mod(..., 8) behavior for negative values.

The published expressions reproduced are:

Xbin1 = mod(fix(X * 2^13), 8) + 1
Xbin2 = mod(fix(X * 2^16), 8) + 1
Xbin3 = mod(fix(X * 2^19), 8) + 1
Xbin4 = mod(fix(X * 2^22), 8) + 1

with analogous expressions for Y, and:

Zbin = mod(fix(Z * 2^22), 8) + 1.

Two parts of the complete cipher remain intentionally unresolved:

1. the exact numerical interpretation of the 32-bit XOR-derived
   initial-condition words before they enter the Lorenz equations,

2. the precise outer-loop placement of P = P - 1, because the prose and
   Algorithm 1 pseudocode are not completely consistent.

Neither ambiguity is currently hidden by an implementation assumption.

---

## Implementation status — pixel DNA and diffusion pipeline

Implemented and tested:

- deterministic splitting of an 8-bit pixel into four 2-bit groups,
- dynamic DNA encoding rule selection using Xbin1...Xbin4,
- dynamic DNA decoding rule selection using Ybin1...Ybin4,
- reconstruction of the transformed 8-bit pixel,
- XOR with Zbin,
- ciphertext feedback using the previous encrypted output as mask,
- normal and reversed pixel traversal.

The implementation isolates this publication-defined pixel operation
from the still-unresolved key-to-Lorenz numerical-state conversion.

The software representation uses the four 2-bit groups in MSB-first
order:

bits 7..6,
bits 5..4,
bits 3..2,
bits 1..0.

This ordering is documented explicitly as an implementation convention
rather than an additional claim about the publication.

The single-pass API intentionally does not decrement P and does not
implement the complete outer encryption loop.

This separation avoids silently choosing between inconsistent
descriptions of P control flow in the publication.

---

## Implementation status — full image passes

Implemented and tested:

- generation of a complete chaotic control sequence,
- 200-state discard before usable controls,
- deterministic repeated control generation,
- P-controlled complete image passes,
- normal traversal for even P,
- reversed traversal for odd P,
- pass-local feedback initialization,
- explicit raw-P=0 to 16-effective-pass behavior.

The P-loop structure is an explicitly documented reproduction
interpretation.

Key-to-Lorenz numerical conversion remains deliberately unresolved.

---

## Key-to-Lorenz reproducibility limitation

The publication specifies XOR combinations of eight 32-bit key words
for deriving X0, Y0 and Z0, but does not specify the numerical
fixed-point interpretation of the resulting words.

A dedicated sensitivity analysis was therefore performed across
multiple explicit 32-bit scaling profiles.

The primary software reproduction profile interprets each raw XOR word
as a signed 32-bit integer scaled by:

2^-26

giving the numerical interval:

[-32, 32).

This choice is an explicitly documented reproduction decision and is
not presented as an undocumented property of the original FPGA design.

Alternative mappings are retained in the key-mapping sensitivity
analysis.

---

## Differential sensitivity diagnostic

A synthetic 256x256 image experiment compared two one-pixel
perturbation methods:

1. conventional intensity change that changes P,
2. intensity change by 16 that preserves P.

For the tested black, white, checkerboard and gradient baselines,
raw P was zero and therefore corresponded to 16 effective passes.

Changing one pixel by one changed raw P to one, reducing the execution
to a single effective pass.

Under this condition, NPCR and UACI were approximately:

NPCR ~ 99.6%
UACI ~ 33.5%

which closely matches conventional reference values.

When P was preserved, differential metrics were substantially lower:

NPCR ~ 52-64%
UACI ~ 7-10%.

This suggests that P-changing plaintext perturbations may confound
differential-security measurements by changing the cipher execution
path itself.

The observation requires further evaluation across all possible P
values before being treated as a general conclusion.
