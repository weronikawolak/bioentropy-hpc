#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>

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

bool near(
    const double first,
    const double second,
    const double tolerance = 1.0e-12
) {
    return std::abs(
        first - second
    ) <= tolerance;
}

}  // namespace

int main() {
    using bioentropy::
        FettehaDnaCipher2023;

    /*
     * Article Steps 1-2:
     *
     * Psum = SUM(image)
     * P = mod(Psum, 16)
     */
    const std::vector<std::uint8_t>
        pixels{
            10,
            20,
            30,
            40
        };

    require(
        FettehaDnaCipher2023::
            pixel_sum(pixels)
        == 100,
        "pixel sum mismatch"
    );

    require(
        FettehaDnaCipher2023::
            iteration_count(pixels)
        == 4,
        "P = pixel sum mod 16 mismatch"
    );

    /*
     * Deterministic 256-bit key layout.
     */
    FettehaDnaCipher2023::Key key{};

    for (
        std::size_t i = 0;
        i < key.size();
        ++i
    ) {
        key[i] =
            static_cast<std::uint8_t>(i);
    }

    const auto words =
        FettehaDnaCipher2023::
            split_key(key);

    require(
        words[0] == 0x00010203U,
        "key word 1 mismatch"
    );

    require(
        words[1] == 0x04050607U,
        "key word 2 mismatch"
    );

    require(
        words[7] == 0x1c1d1e1fU,
        "key word 8 mismatch"
    );

    const auto initial =
        FettehaDnaCipher2023::
            derive_raw_initial_conditions(
                words
            );

    require(
        initial.x0
        == (
            words[0]
            ^ words[1]
            ^ words[2]
            ^ words[3]
        ),
        "X0 XOR derivation mismatch"
    );

    require(
        initial.y0
        == (
            words[2]
            ^ words[3]
            ^ words[4]
            ^ words[5]
        ),
        "Y0 XOR derivation mismatch"
    );

    require(
        initial.z0
        == (
            words[4]
            ^ words[5]
            ^ words[6]
            ^ words[7]
        ),
        "Z0 XOR derivation mismatch"
    );

    /*
     * Figure 1 / Equations (1a)-(1c)
     * reference parameters.
     */
    const bioentropy::LorenzState2023
        state{
            10.0,
            10.0,
            10.0
        };

    const auto next =
        FettehaDnaCipher2023::
            lorenz_step(state);

    require(
        near(
            next.x,
            10.0
        ),
        "Lorenz X1 mismatch"
    );

    require(
        near(
            next.y,
            10.390625
        ),
        "Lorenz Y1 mismatch"
    );

    require(
        near(
            next.z,
            10.625
        ),
        "Lorenz Z1 mismatch"
    );

    std::cout
        << "Fetteha DNA cipher 2023 "
        << "core tests passed\n";

    return EXIT_SUCCESS;
}
