# Cellular Automata Implementation Conventions

## Scope

The framework evaluates two one-dimensional elementary cellular automata:

- Rule 30
- Rule 90

No additional rules are included in the primary study.

## Lattice sizes

Supported lattice sizes:

- 256 cells
- 1024 cells

## Boundary conditions

Periodic boundary conditions are used.

For a lattice of N cells:

- the left neighbour of cell 0 is cell N-1
- the right neighbour of cell N-1 is cell 0

## Initial state

Each experiment provides a deterministic 256-bit seed.

The cellular automaton initial state is expanded using:

SHA-256(
    "BIOENTROPY-HPC-CA-INIT-v1"
    || seed
    || counter
)

The counter is encoded as a 32-bit big-endian integer.

This operation creates a reproducible initial state and must not be
interpreted as increasing the entropy of the original seed.

## Generation numbering

The expanded initial state is generation 0.

Generation 0 is not emitted directly.

The cellular automaton is evolved once before output generation begins.

Therefore, the first output bits originate from generation 1.

## Rule evaluation

The local neighbourhood is encoded as:

4 * left + 2 * center + right

The corresponding bit of the elementary cellular automaton rule number
defines the next state of the center cell.

## Output

The complete generation is emitted sequentially.

Cells are packed most-significant-bit first into bytes.

After all cells from the current generation are emitted, the cellular
automaton advances to the next generation.

## Reproducibility

Identical:

- seed
- rule
- lattice size

must produce an identical bitstream.

Execution chunk size must not affect the generated output or the
SHA-256 fingerprint.
