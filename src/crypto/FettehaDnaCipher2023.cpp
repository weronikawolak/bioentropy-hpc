#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <cstddef>
#include <cstdint>

namespace bioentropy {

std::uint64_t
FettehaDnaCipher2023::pixel_sum(
    const std::span<const std::uint8_t> image
) {
    std::uint64_t sum = 0;

    for (const auto pixel : image) {
        sum += pixel;
    }

    return sum;
}

std::uint8_t
FettehaDnaCipher2023::iteration_count(
    const std::span<const std::uint8_t> image
) {
    return static_cast<std::uint8_t>(
        pixel_sum(image) % 16ULL
    );
}

FettehaDnaCipher2023::KeyWords
FettehaDnaCipher2023::split_key(
    const Key& key
) {
    KeyWords words{};

    for (
        std::size_t word_index = 0;
        word_index < words.size();
        ++word_index
    ) {
        const std::size_t offset =
            word_index * 4;

        words[word_index] =
            (
                static_cast<std::uint32_t>(
                    key[offset]
                )
                << 24U
            )
            |
            (
                static_cast<std::uint32_t>(
                    key[offset + 1]
                )
                << 16U
            )
            |
            (
                static_cast<std::uint32_t>(
                    key[offset + 2]
                )
                << 8U
            )
            |
            static_cast<std::uint32_t>(
                key[offset + 3]
            );
    }

    return words;
}

FettehaRawInitialConditions2023
FettehaDnaCipher2023::
derive_raw_initial_conditions(
    const KeyWords& words
) {
    /*
     * Direct reproduction of Algorithm 1:
     *
     * X0 = Key1 XOR Key2 XOR Key3 XOR Key4
     * Y0 = Key3 XOR Key4 XOR Key5 XOR Key6
     * Z0 = Key5 XOR Key6 XOR Key7 XOR Key8
     */
    return {
        words[0]
            ^ words[1]
            ^ words[2]
            ^ words[3],

        words[2]
            ^ words[3]
            ^ words[4]
            ^ words[5],

        words[4]
            ^ words[5]
            ^ words[6]
            ^ words[7]
    };
}

LorenzState2023
FettehaDnaCipher2023::lorenz_step(
    const LorenzState2023& state,
    const LorenzParameters2023& parameters
) {
    /*
     * Fetteha et al. 2023,
     * Equations (1a)-(1c).
     *
     * All next-state values are calculated
     * from the same previous state.
     */
    const double next_x =
        state.x
        + parameters.h
            * parameters.sigma
            * (
                state.y
                - state.x
            );

    const double next_y =
        state.y
        + parameters.h
            * (
                parameters.rho
                    * state.x
                - state.y
                - state.x
                    * state.z
            );

    const double next_z =
        state.z
        + parameters.h
            * (
                state.x
                    * state.y
                - parameters.beta
                    * state.z
            );

    return {
        next_x,
        next_y,
        next_z
    };
}

}  // namespace bioentropy
