# DNA Sequence Source Conventions

## Purpose

DNA sequences are treated as deterministic candidate
randomness sources.

Public reference genome sequences are not assumed to be
physical entropy sources.

The framework evaluates statistical properties of
deterministically selected sequence windows.

## Input representation

The C++ DNA source consumes a preprocessed nucleotide window.

The input file contains only canonical nucleotides:

- A
- C
- G
- T

Whitespace is ignored.

Any other nucleotide symbol causes the experiment to fail.

Ambiguous bases such as N are therefore handled during the
preprocessing stage rather than silently mapped by the
generator.

## Primary mapping

The primary nucleotide-to-bit mapping is:

A = 00
C = 01
G = 10
T = 11

Four nucleotides therefore produce one byte.

Bits are packed MSB-first.

Example:

ACGT -> 00011011 -> 0x1B

## Window metadata

Each experiment records:

- assembly accession
- sequence accession
- original window start
- window length
- nucleotide-to-bit mapping
- SHA-256 of the canonical nucleotide window

`window_start_nt` uses a zero-based coordinate in the
original reference sequence.

## Reproducibility

The canonical nucleotide window is hashed using SHA-256.

If the configured digest does not match the loaded sequence,
the experiment fails.

This protects against accidental changes to downloaded or
preprocessed datasets.

## Experiment seed

DNA sequence generation does not use the experiment seed.

Window selection is performed deterministically during
preprocessing.

The selected coordinates are persisted in the experiment
configuration and dataset manifest.

The general experiment framework may still derive and record
an experiment seed, but that value does not alter the DNA
bitstream.

## Output length

Each nucleotide contributes exactly two bits.

Therefore:

output_bits = 2 * window_length_nt

The current byte-oriented implementation requires the
nucleotide count to be divisible by four.

## Reference genome dataset

The primary DNA dataset contains five version-pinned NCBI
RefSeq assemblies representing diverse organisms.

Ten windows are selected per assembly.

The dataset therefore contains 50 primary DNA streams.

## Primary window length

Each primary window contains:

400,000 nucleotides

which produces:

800,000 output bits

under the primary 2-bit nucleotide mapping.

## Canonical-run filtering

Windows never cross ambiguous nucleotide symbols.

Each FASTA record is divided into maximal runs containing
only:

A
C
G
T

Ambiguous symbols, including N, separate eligible runs.

## Non-overlapping candidate construction

Each canonical run is divided from its beginning into
non-overlapping fixed-size blocks of 400,000 nucleotides.

Incomplete trailing fragments are excluded.

This construction prevents overlap between candidate windows
belonging to the same reference sequence.

## Deterministic window selection

Candidate blocks are ranked using SHA-256 over deterministic
metadata containing:

- BIOENTROPY-HPC-DNA-WINDOW-SELECTION-v1
- assembly accession
- sequence accession
- window start
- window length

The ten candidates with the lowest deterministic hash
ranking are selected.

The selection procedure contains no runtime randomness.

## Provenance

For every selected window the dataset manifest records:

- versioned assembly accession
- sequence accession
- zero-based window start
- window length
- nucleotide mapping
- window SHA-256
- source genomic FASTA SHA-256
- selection score
- selection scheme identifier
- generated experiment configuration

This permits exact reconstruction and verification of the
experimental DNA dataset.

## Interpretation

A high Shannon entropy, low bit bias, or success in
statistical randomness tests does not make a public DNA
sequence a cryptographically secure entropy source.

DNA is evaluated as a deterministic bio-inspired candidate
source.
