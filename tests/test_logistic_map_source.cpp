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

    /*
     * Explicit float32 regression.
     *
     * Same logical parameters as the original float64
     * reference vector, but binary32 arithmetic must follow
     * a different deterministic digital trajectory.
     */
    bioentropy::LogisticMapConfig
        float32_config = config;

    float32_config.arithmetic_mode =
        bioentropy::
            LogisticArithmeticMode::Float32;

    bioentropy::LogisticMapSource
        float32_source(
            float32_config,
            zero_seed()
        );

    std::array<std::uint8_t, 4>
        float32_output{};

    float32_source.generate(
        float32_output
    );

    const std::array<std::uint8_t, 4>
        expected_float32{
            0x15,
            0xC4,
            0xF7,
            0xFE
        };

    require(
        float32_output ==
            expected_float32,
        "float32 logistic output does not "
        "match reference vector"
    );

    require(
        float32_output != expected,
        "float32 and float64 trajectories "
        "must differ"
    );

    float32_source.reset();

    std::array<std::uint8_t, 4>
        float32_repeated{};

    float32_source.generate(
        float32_repeated
    );

    require(
        float32_repeated ==
            expected_float32,
        "float32 reset did not reproduce "
        "the same bitstream"
    );

    /*
     * Fixed-point Q3.29 regression.
     *
     * Exact reproduction profile:
     *
     * R = floor(r * 2^29)
     * X = floor(x * 2^29)
     *
     * with truncation after every logistic-map iteration.
     */
    bioentropy::LogisticMapConfig
        fixed_config = config;

    fixed_config.arithmetic_mode =
        bioentropy::
            LogisticArithmeticMode::FixedQ3_29;

    bioentropy::LogisticMapSource
        fixed_source(
            fixed_config,
            zero_seed()
        );

    std::array<std::uint8_t, 4>
        fixed_output{};

    fixed_source.generate(
        fixed_output
    );

    const std::array<std::uint8_t, 4>
        expected_fixed{
            0x15,
            0xCD,
            0x6D,
            0x57
        };

    require(
        fixed_output ==
            expected_fixed,
        "Q3.29 logistic output does not "
        "match reference vector"
    );

    require(
        fixed_output != expected,
        "Q3.29 and float64 trajectories "
        "must differ"
    );

    fixed_source.reset();

    std::array<std::uint8_t, 4>
        fixed_repeated{};

    fixed_source.generate(
        fixed_repeated
    );

    require(
        fixed_repeated ==
            expected_fixed,
        "Q3.29 reset did not reproduce "
        "the same bitstream"
    );

    /*
     * MPFR-256 regression.
     *
     * Decimal parameter literals are preserved so that
     * MPFR does not begin from binary64-quantized input.
     *
     * The first four output bytes happen to match the
     * binary64 trajectory for this reference case.
     * The trajectories diverge at byte five.
     */
    bioentropy::LogisticMapConfig
        mpfr_config = config;

    mpfr_config.arithmetic_mode =
        bioentropy::
            LogisticArithmeticMode::Mpfr256;

    mpfr_config.r_literal =
        "4.0";

    mpfr_config.x0_literal =
        std::string(
            "0.123456789"
        );

    bioentropy::LogisticMapSource
        mpfr_source(
            mpfr_config,
            zero_seed()
        );

    std::array<std::uint8_t, 8>
        mpfr_output{};

    mpfr_source.generate(
        mpfr_output
    );

    const std::array<std::uint8_t, 8>
        expected_mpfr{
            0x15,
            0xCD,
            0xFC,
            0x5E,
            0x5F,
            0x1A,
            0x00,
            0xFB
        };

    require(
        mpfr_output ==
            expected_mpfr,
        "MPFR-256 logistic output does not "
        "match reference vector"
    );

    mpfr_source.reset();

    std::array<std::uint8_t, 8>
        mpfr_repeated{};

    mpfr_source.generate(
        mpfr_repeated
    );

    require(
        mpfr_repeated ==
            expected_mpfr,
        "MPFR-256 reset did not reproduce "
        "the same bitstream"
    );

    std::cout
        << "LogisticMapSource tests passed.\n";

    return EXIT_SUCCESS;
}
