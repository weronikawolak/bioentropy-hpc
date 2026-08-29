#include "bioentropy/sources/Chen4DDcsSource.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "FAILED: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

} // namespace

int main() {
    bioentropy::Chen4DDcsConfig config{};

    config.r = 5.0;

    config.x0 = 0.1;
    config.y0 = 0.2;
    config.z0 = 0.3;
    config.w0 = 0.4;

    config.burn_in = 10;

    config.threshold = 0.5;

    bioentropy::Chen4DDcsSource source(
        config
    );

    require(
        source.name() ==
            "chen_4d_dcs",
        "unexpected source name"
    );

    require(
        source.deterministic(),
        "Chen 4D-DCS must be deterministic"
    );

    std::array<std::uint8_t, 8>
        output{};

    source.generate(output);

    const std::array<std::uint8_t, 8>
        expected{
            0x7D,
            0xF6,
            0x45,
            0x4A,
            0x31,
            0x8D,
            0x88,
            0xEF
        };

    require(
        output == expected,
        "Chen 4D-DCS output does not "
        "match reference vector"
    );

    source.reset();

    std::array<std::uint8_t, 8>
        repeated{};

    source.generate(repeated);

    require(
        repeated == expected,
        "Chen 4D-DCS reset did not "
        "reproduce reference stream"
    );

    bool invalid_r_rejected = false;

    try {
        auto invalid = config;

        invalid.r = 11.0;

        bioentropy::Chen4DDcsSource
            invalid_source(invalid);

        (void) invalid_source;
    } catch (
        const std::invalid_argument&
    ) {
        invalid_r_rejected = true;
    }

    require(
        invalid_r_rejected,
        "invalid Chen 4D-DCS r accepted"
    );

    std::cout
        << "Chen 4D-DCS source tests passed.\n";

    return EXIT_SUCCESS;
}
