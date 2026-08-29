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
