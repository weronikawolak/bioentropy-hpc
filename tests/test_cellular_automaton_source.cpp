#include "bioentropy/sources/CellularAutomatonSource.hpp"

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
    bioentropy::CellularAutomatonConfig
        rule30_config{};

    rule30_config.rule =
        bioentropy::CellularAutomatonRule::Rule30;

    rule30_config.cells = 256;

    bioentropy::CellularAutomatonSource
        rule30(
            rule30_config,
            reference_seed()
        );

    std::array<std::uint8_t, 16>
        rule30_output{};

    rule30.generate(
        rule30_output
    );

    const std::array<std::uint8_t, 16>
        expected_rule30{
            0x5C, 0xFB, 0xAD, 0xCF,
            0xF7, 0x3E, 0x5E, 0xB9,
            0x45, 0xF0, 0x18, 0xC3,
            0x4C, 0x38, 0xC8, 0x29
        };

    require(
        rule30_output ==
        expected_rule30,
        "Rule 30 output does not match reference vector"
    );

    rule30.reset();

    std::array<std::uint8_t, 16>
        repeated{};

    rule30.generate(repeated);

    require(
        repeated == expected_rule30,
        "Rule 30 reset is not reproducible"
    );

    rule30.reset();

    std::array<std::uint8_t, 7>
        first_chunk{};

    std::array<std::uint8_t, 9>
        second_chunk{};

    rule30.generate(first_chunk);
    rule30.generate(second_chunk);

    for (
        std::size_t i = 0;
        i < first_chunk.size();
        ++i
    ) {
        require(
            first_chunk[i] ==
            expected_rule30[i],
            "Rule 30 chunked output mismatch"
        );
    }

    for (
        std::size_t i = 0;
        i < second_chunk.size();
        ++i
    ) {
        require(
            second_chunk[i] ==
            expected_rule30[
                i + first_chunk.size()
            ],
            "Rule 30 chunked output mismatch"
        );
    }

    bioentropy::CellularAutomatonConfig
        rule90_config{};

    rule90_config.rule =
        bioentropy::CellularAutomatonRule::Rule90;

    rule90_config.cells = 256;

    bioentropy::CellularAutomatonSource
        rule90(
            rule90_config,
            reference_seed()
        );

    std::array<std::uint8_t, 16>
        rule90_output{};

    rule90.generate(
        rule90_output
    );

    const std::array<std::uint8_t, 16>
        expected_rule90{
            0xD4, 0xBF, 0xEF, 0xE6,
            0xD5, 0x2F, 0x0C, 0xFC,
            0x50, 0xD0, 0x1A, 0x42,
            0x64, 0x28, 0xE8, 0xB9
        };

    require(
        rule90_output ==
        expected_rule90,
        "Rule 90 output does not match reference vector"
    );

    bioentropy::CellularAutomatonConfig
        large_config{};

    large_config.rule =
        bioentropy::CellularAutomatonRule::Rule30;

    large_config.cells = 1024;

    bioentropy::CellularAutomatonSource
        large_a(
            large_config,
            reference_seed()
        );

    bioentropy::CellularAutomatonSource
        large_b(
            large_config,
            reference_seed()
        );

    std::array<std::uint8_t, 64> a{};
    std::array<std::uint8_t, 64> b{};

    large_a.generate(a);
    large_b.generate(b);

    require(
        a == b,
        "1024-cell automaton is not reproducible"
    );

    std::cout
        << "CellularAutomatonSource tests passed.\n";

    return EXIT_SUCCESS;
}
