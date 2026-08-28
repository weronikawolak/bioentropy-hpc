#include "bioentropy/sources/ChaCha20ReferenceSource.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace {

void require(
    bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "TEST FAILURE: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

bioentropy::Seed256 reference_seed() {
    bioentropy::Seed256 seed{};

    for (
        std::size_t i = 0;
        i < seed.size();
        ++i
    ) {
        seed[i] =
            static_cast<std::uint8_t>(i);
    }

    return seed;
}

} // namespace

int main() {
    bioentropy::ChaCha20ReferenceConfig
        config{};

    config.initial_counter = 0;

    bioentropy::ChaCha20ReferenceSource
        source(
            config,
            reference_seed()
        );

    std::array<std::uint8_t, 64>
        output{};

    source.generate(output);

    const std::array<std::uint8_t, 64>
        expected{
            0xBD, 0x25, 0x7D, 0x57,
            0x24, 0x34, 0x2C, 0x56,
            0x52, 0x28, 0x45, 0x87,
            0xF0, 0xB9, 0x68, 0x83,
            0xE0, 0xCB, 0x01, 0x06,
            0xD9, 0x43, 0xD0, 0x32,
            0x33, 0x91, 0x22, 0x6B,
            0x8F, 0x96, 0x79, 0xFD,
            0x75, 0x29, 0x85, 0xBF,
            0x79, 0x75, 0x2D, 0xBF,
            0xB3, 0x81, 0xF0, 0xC8,
            0x25, 0x05, 0xA2, 0x26,
            0xEE, 0x84, 0x4C, 0x7B,
            0xAE, 0xCE, 0x3A, 0xC6,
            0xC7, 0x96, 0x29, 0xD6,
            0xEE, 0xEA, 0x73, 0x89
        };

    require(
        output == expected,
        "ChaCha20 output does not match "
        "reference vector"
    );

    source.reset();

    std::array<std::uint8_t, 64>
        repeated{};

    source.generate(repeated);

    require(
        repeated == expected,
        "ChaCha20 reset is not reproducible"
    );

    source.reset();

    std::array<std::uint8_t, 7>
        first_chunk{};

    std::array<std::uint8_t, 57>
        second_chunk{};

    source.generate(first_chunk);
    source.generate(second_chunk);

    for (
        std::size_t i = 0;
        i < first_chunk.size();
        ++i
    ) {
        require(
            first_chunk[i] == expected[i],
            "ChaCha20 first chunk mismatch"
        );
    }

    for (
        std::size_t i = 0;
        i < second_chunk.size();
        ++i
    ) {
        require(
            second_chunk[i] ==
            expected[
                i + first_chunk.size()
            ],
            "ChaCha20 second chunk mismatch"
        );
    }

    std::cout
        << "ChaCha20ReferenceSource tests passed.\n";

    return EXIT_SUCCESS;
}
