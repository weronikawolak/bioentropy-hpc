#include "bioentropy/sources/LogisticMapSource.hpp"

#include <array>
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

bioentropy::Seed256 zero_seed() {
    return bioentropy::Seed256{};
}

} // namespace

int main() {
    bioentropy::LogisticMapConfig config{};

    config.r = 4.0;
    config.initial_state_mode =
        bioentropy::LogisticInitialStateMode::Explicit;

    config.x0 = 0.123456789;
    config.burn_in = 10;

    config.extraction =
        bioentropy::LogisticExtractionMethod::Threshold;

    bioentropy::LogisticMapSource source(
        config,
        zero_seed()
    );

    std::array<std::uint8_t, 4> output{};

    source.generate(output);

    const std::array<std::uint8_t, 4> expected{
        0x15,
        0xCD,
        0xFC,
        0x5E
    };

    require(
        output == expected,
        "logistic output does not match reference vector"
    );

    /*
     * reset() must restore exactly the same state.
     */
    source.reset();

    std::array<std::uint8_t, 4> repeated{};
    source.generate(repeated);

    require(
        repeated == expected,
        "reset did not reproduce the same bitstream"
    );

    /*
     * Streaming must not change the output.
     */
    source.reset();

    std::array<std::uint8_t, 2> first_half{};
    std::array<std::uint8_t, 2> second_half{};

    source.generate(first_half);
    source.generate(second_half);

    require(
        first_half[0] == expected[0] &&
        first_half[1] == expected[1] &&
        second_half[0] == expected[2] &&
        second_half[1] == expected[3],
        "chunked generation differs from contiguous generation"
    );

    /*
     * Derived initial state must also be reproducible.
     */
    bioentropy::LogisticMapConfig derived_config{};

    derived_config.r = 3.99;
    derived_config.initial_state_mode =
        bioentropy::LogisticInitialStateMode::DerivedFromSeed;

    derived_config.burn_in = 100;

    bioentropy::Seed256 seed{};

    for (std::size_t i = 0; i < seed.size(); ++i) {
        seed[i] = static_cast<std::uint8_t>(i);
    }

    bioentropy::LogisticMapSource derived_a(
        derived_config,
        seed
    );

    bioentropy::LogisticMapSource derived_b(
        derived_config,
        seed
    );

    std::array<std::uint8_t, 16> a{};
    std::array<std::uint8_t, 16> b{};

    derived_a.generate(a);
    derived_b.generate(b);

    require(
        a == b,
        "same seed must produce the same logistic stream"
    );

    std::cout
        << "LogisticMapSource tests passed.\n";

    return EXIT_SUCCESS;
}
