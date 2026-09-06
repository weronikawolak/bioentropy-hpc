#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

namespace bioentropy {

namespace {

/*
 * Fetteha, Sayed & Said 2023
 * Table 1.
 *
 * Inner index:
 *
 * 0 -> 00
 * 1 -> 01
 * 2 -> 10
 * 3 -> 11
 */
constexpr std::array<
    std::array<DnaBase2023, 4>,
    8
> dna_rules{{
    {
        DnaBase2023::G,
        DnaBase2023::A,
        DnaBase2023::T,
        DnaBase2023::C
    },
    {
        DnaBase2023::T,
        DnaBase2023::C,
        DnaBase2023::G,
        DnaBase2023::A
    },
    {
        DnaBase2023::A,
        DnaBase2023::C,
        DnaBase2023::G,
        DnaBase2023::T
    },
    {
        DnaBase2023::G,
        DnaBase2023::T,
        DnaBase2023::A,
        DnaBase2023::C
    },
    {
        DnaBase2023::C,
        DnaBase2023::T,
        DnaBase2023::A,
        DnaBase2023::G
    },
    {
        DnaBase2023::A,
        DnaBase2023::G,
        DnaBase2023::C,
        DnaBase2023::T
    },
    {
        DnaBase2023::C,
        DnaBase2023::A,
        DnaBase2023::T,
        DnaBase2023::G
    },
    {
        DnaBase2023::T,
        DnaBase2023::G,
        DnaBase2023::C,
        DnaBase2023::A
    }
}};

std::size_t rule_index(
    const std::uint8_t rule
) {
    if (rule < 1 || rule > 8) {
        throw std::invalid_argument(
            "DNA rule must be in [1, 8]"
        );
    }

    return static_cast<std::size_t>(
        rule - 1
    );
}

}  // namespace

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


std::uint8_t
FettehaDnaCipher2023::effective_pass_count(
    const std::uint8_t raw_p
) {
    if (raw_p > 15U) {
        throw std::invalid_argument(
            "Raw P must be in [0, 15]"
        );
    }

    /*
     * BioEntropy HPC reproduction
     * profile v2.
     *
     * The publication reports successful
     * encryption of all-black images,
     * for which sum(pixels) mod 16 = 0.
     *
     * Therefore raw P=0 cannot represent
     * zero effective encryption passes if
     * those reported results are to be
     * reproduced.
     *
     * Interpret zero as sixteen effective
     * passes.
     */
    return raw_p == 0U
        ? 16U
        : raw_p;
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
        const auto offset =
            word_index * 4;

        words[word_index] =
            (
                static_cast<std::uint32_t>(
                    key[offset]
                ) << 24U
            )
            |
            (
                static_cast<std::uint32_t>(
                    key[offset + 1]
                ) << 16U
            )
            |
            (
                static_cast<std::uint32_t>(
                    key[offset + 2]
                ) << 8U
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

double
FettehaDnaCipher2023::
map_raw_condition_s32_2neg26(
    const std::uint32_t raw
) {
    /*
     * BioEntropy HPC reproduction profile v1.
     *
     * Interpret raw XOR output as signed
     * 32-bit two's-complement and apply
     * scale 2^-26.
     *
     * This is NOT specified by the source
     * publication.
     */
    const std::int64_t signed_value =
        raw <= 0x7FFFFFFFU
            ? static_cast<std::int64_t>(raw)
            : static_cast<std::int64_t>(raw)
                - (1LL << 32);

    return std::ldexp(
        static_cast<double>(signed_value),
        -26
    );
}

LorenzState2023
FettehaDnaCipher2023::
map_raw_initial_conditions(
    const FettehaRawInitialConditions2023& raw
) {
    return {
        map_raw_condition_s32_2neg26(
            raw.x0
        ),
        map_raw_condition_s32_2neg26(
            raw.y0
        ),
        map_raw_condition_s32_2neg26(
            raw.z0
        )
    };
}

LorenzState2023
FettehaDnaCipher2023::derive_initial_state(
    const Key& key
) {
    const auto words =
        split_key(key);

    const auto raw =
        derive_raw_initial_conditions(
            words
        );

    return map_raw_initial_conditions(
        raw
    );
}


LorenzState2023
FettehaDnaCipher2023::lorenz_step(
    const LorenzState2023& state,
    const LorenzParameters2023& parameters
) {
    const double next_x =
        state.x
        + parameters.h
            * parameters.sigma
            * (state.y - state.x);

    const double next_y =
        state.y
        + parameters.h
            * (
                parameters.rho * state.x
                - state.y
                - state.x * state.z
            );

    const double next_z =
        state.z
        + parameters.h
            * (
                state.x * state.y
                - parameters.beta * state.z
            );

    return {
        next_x,
        next_y,
        next_z
    };
}


LorenzState2023
FettehaDnaCipher2023::advance_lorenz(
    LorenzState2023 state,
    const std::size_t steps,
    const LorenzParameters2023& parameters
) {
    for (
        std::size_t i = 0;
        i < steps;
        ++i
    ) {
        state =
            lorenz_step(
                state,
                parameters
            );
    }

    return state;
}

std::uint8_t
FettehaDnaCipher2023::extract_rule_index(
    const double value,
    const int binary_shift
) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(
            "Chaotic value must be finite"
        );
    }

    /*
     * Exact power-of-two scaling from
     * Algorithm 1:
     *
     * fix(value * 2^binary_shift)
     */
    const double scaled =
        std::ldexp(
            value,
            binary_shift
        );

    if (!std::isfinite(scaled)) {
        throw std::overflow_error(
            "Chaotic control scaling overflow"
        );
    }

    /*
     * MATLAB fix():
     * truncate toward zero.
     */
    const double fixed =
        std::trunc(scaled);

    /*
     * MATLAB mod(fixed, 8):
     * result must be in [0, 7].
     *
     * std::fmod() preserves the sign of
     * the dividend, so negative results
     * must be normalized explicitly.
     */
    double remainder =
        std::fmod(
            fixed,
            8.0
        );

    if (remainder < 0.0) {
        remainder += 8.0;
    }

    return static_cast<std::uint8_t>(
        remainder
    ) + 1U;
}

DnaControlValues2023
FettehaDnaCipher2023::derive_dna_controls(
    const LorenzState2023& state
) {
    constexpr std::array<int, 4>
        shifts{
            13,
            16,
            19,
            22
        };

    DnaControlValues2023 controls{};

    for (
        std::size_t i = 0;
        i < shifts.size();
        ++i
    ) {
        controls.x_rules[i] =
            extract_rule_index(
                state.x,
                shifts[i]
            );

        controls.y_rules[i] =
            extract_rule_index(
                state.y,
                shifts[i]
            );
    }

    controls.z_bin =
        extract_rule_index(
            state.z,
            22
        );

    return controls;
}

DnaBase2023
FettehaDnaCipher2023::dna_encode_pair(
    const std::uint8_t pair,
    const std::uint8_t rule
) {
    if (pair > 3) {
        throw std::invalid_argument(
            "DNA input pair must be in [0, 3]"
        );
    }

    return dna_rules[
        rule_index(rule)
    ][pair];
}

std::uint8_t
FettehaDnaCipher2023::dna_decode_base(
    const DnaBase2023 base,
    const std::uint8_t rule
) {
    const auto& selected_rule =
        dna_rules[rule_index(rule)];

    for (
        std::uint8_t pair = 0;
        pair < 4;
        ++pair
    ) {
        if (
            selected_rule[pair]
            == base
        ) {
            return pair;
        }
    }

    throw std::logic_error(
        "Invalid DNA rule table"
    );
}

std::uint8_t
FettehaDnaCipher2023::dna_transform_pair(
    const std::uint8_t pair,
    const std::uint8_t encode_rule,
    const std::uint8_t decode_rule
) {
    const auto base =
        dna_encode_pair(
            pair,
            encode_rule
        );

    return dna_decode_base(
        base,
        decode_rule
    );
}

std::array<std::uint8_t, 4>
FettehaDnaCipher2023::split_pixel_pairs(
    const std::uint8_t pixel
) {
    /*
     * Deterministic software representation:
     *
     * pair 0 = bits 7..6
     * pair 1 = bits 5..4
     * pair 2 = bits 3..2
     * pair 3 = bits 1..0
     *
     * This preserves the natural left-to-right
     * order of an 8-bit pixel representation.
     */
    return {
        static_cast<std::uint8_t>(
            (pixel >> 6U) & 0x03U
        ),
        static_cast<std::uint8_t>(
            (pixel >> 4U) & 0x03U
        ),
        static_cast<std::uint8_t>(
            (pixel >> 2U) & 0x03U
        ),
        static_cast<std::uint8_t>(
            pixel & 0x03U
        )
    };
}

std::uint8_t
FettehaDnaCipher2023::join_pixel_pairs(
    const std::array<std::uint8_t, 4>& pairs
) {
    for (const auto pair : pairs) {
        if (pair > 3U) {
            throw std::invalid_argument(
                "DNA pixel pair must be in [0, 3]"
            );
        }
    }

    return static_cast<std::uint8_t>(
        (pairs[0] << 6U)
        | (pairs[1] << 4U)
        | (pairs[2] << 2U)
        | pairs[3]
    );
}

std::uint8_t
FettehaDnaCipher2023::dna_transform_pixel(
    const std::uint8_t pixel,
    const DnaControlValues2023& controls
) {
    auto pairs =
        split_pixel_pairs(pixel);

    for (
        std::size_t i = 0;
        i < pairs.size();
        ++i
    ) {
        pairs[i] =
            dna_transform_pair(
                pairs[i],
                controls.x_rules[i],
                controls.y_rules[i]
            );
    }

    return join_pixel_pairs(pairs);
}

std::uint8_t
FettehaDnaCipher2023::diffuse_pixel(
    const std::uint8_t transformed_pixel,
    const std::uint8_t z_bin,
    const std::uint8_t mask
) {
    if (z_bin < 1U || z_bin > 8U) {
        throw std::invalid_argument(
            "Zbin must be in [1, 8]"
        );
    }

    /*
     * Fetteha et al. 2023, Algorithm 1:
     *
     * output = Zbin XOR T XOR mask
     */
    return static_cast<std::uint8_t>(
        transformed_pixel
        ^ z_bin
        ^ mask
    );
}

std::vector<std::uint8_t>
FettehaDnaCipher2023::encrypt_single_pass(
    const std::span<const std::uint8_t> image,
    const std::span<const DnaControlValues2023> controls,
    const bool flipped
) {
    if (image.size() != controls.size()) {
        throw std::invalid_argument(
            "Image and control sequence sizes must match"
        );
    }

    std::vector<std::uint8_t>
        output(image.size());

    /*
     * Algorithm 1 initializes mask with zero.
     */
    std::uint8_t mask = 0U;

    for (
        std::size_t i = 0;
        i < image.size();
        ++i
    ) {
        const std::size_t source_index =
            flipped
                ? image.size() - 1U - i
                : i;

        const auto transformed =
            dna_transform_pixel(
                image[source_index],
                controls[i]
            );

        output[i] =
            diffuse_pixel(
                transformed,
                controls[i].z_bin,
                mask
            );

        /*
         * Ciphertext feedback:
         * next mask = previous output.
         */
        mask = output[i];
    }

    return output;
}


std::vector<DnaControlValues2023>
FettehaDnaCipher2023::generate_control_sequence(
    const LorenzState2023& initial_state,
    const std::size_t count,
    const std::size_t discard
) {
    auto state =
        advance_lorenz(
            initial_state,
            discard
        );

    std::vector<DnaControlValues2023>
        controls;

    controls.reserve(count);

    for (
        std::size_t i = 0;
        i < count;
        ++i
    ) {
        state =
            lorenz_step(state);

        controls.push_back(
            derive_dna_controls(state)
        );
    }

    return controls;
}

std::vector<std::uint8_t>
FettehaDnaCipher2023::encrypt_with_initial_state(
    const std::span<const std::uint8_t> image,
    const LorenzState2023& initial_state
) {
    std::vector<std::uint8_t>
        current(
            image.begin(),
            image.end()
        );

    const std::uint8_t raw_p =
        iteration_count(image);

    if (image.empty()) {
        return current;
    }

    /*
     * Reproduction profile v2:
     *
     * raw P = sum(image) mod 16
     *
     * raw P=0 is interpreted as
     * sixteen effective passes.
     */
    std::uint8_t p =
        effective_pass_count(raw_p);

    /*
     * Algorithm 1 is interpreted as
     * restarting the same Lorenz trajectory
     * for every complete pass.
     */
    const auto controls =
        generate_control_sequence(
            initial_state,
            image.size(),
            200
        );

    while (p > 0U) {
        const bool flipped =
            (p % 2U) != 0U;

        current =
            encrypt_single_pass(
                current,
                controls,
                flipped
            );

        --p;
    }

    return current;
}


std::uint8_t
FettehaDnaCipher2023::dna_inverse_transform_pixel(
    const std::uint8_t pixel,
    const DnaControlValues2023& controls
) {
    auto pairs =
        split_pixel_pairs(pixel);

    /*
     * Encryption performs:
     *
     * decode_Y(encode_X(pair))
     *
     * Therefore the inverse is:
     *
     * decode_X(encode_Y(pair))
     */
    for (
        std::size_t i = 0;
        i < pairs.size();
        ++i
    ) {
        pairs[i] =
            dna_transform_pair(
                pairs[i],
                controls.y_rules[i],
                controls.x_rules[i]
            );
    }

    return join_pixel_pairs(pairs);
}

std::vector<std::uint8_t>
FettehaDnaCipher2023::decrypt_single_pass(
    const std::span<const std::uint8_t> ciphertext,
    const std::span<const DnaControlValues2023> controls,
    const bool flipped
) {
    if (ciphertext.size() != controls.size()) {
        throw std::invalid_argument(
            "Ciphertext and control sequence sizes must match"
        );
    }

    std::vector<std::uint8_t>
        plaintext(ciphertext.size());

    std::uint8_t mask = 0U;

    for (
        std::size_t i = 0;
        i < ciphertext.size();
        ++i
    ) {
        /*
         * Encryption:
         *
         * C[i] = T XOR Zbin XOR C[i-1]
         *
         * therefore:
         *
         * T = C[i] XOR Zbin XOR C[i-1]
         */
        const std::uint8_t transformed =
            static_cast<std::uint8_t>(
                ciphertext[i]
                ^ controls[i].z_bin
                ^ mask
            );

        const std::uint8_t recovered =
            dna_inverse_transform_pixel(
                transformed,
                controls[i]
            );

        const std::size_t destination_index =
            flipped
                ? ciphertext.size() - 1U - i
                : i;

        plaintext[destination_index] =
            recovered;

        /*
         * Feedback during inversion uses
         * the previous encryption output,
         * i.e. previous ciphertext byte.
         */
        mask = ciphertext[i];
    }

    return plaintext;
}

std::vector<std::uint8_t>
FettehaDnaCipher2023::decrypt_with_initial_state(
    const std::span<const std::uint8_t> ciphertext,
    const LorenzState2023& initial_state,
    const std::uint8_t p
) {
    std::vector<std::uint8_t>
        current(
            ciphertext.begin(),
            ciphertext.end()
        );

    if (ciphertext.empty()) {
        return current;
    }

    const std::uint8_t passes =
        effective_pass_count(p);

    const auto controls =
        generate_control_sequence(
            initial_state,
            ciphertext.size(),
            200
        );

    /*
     * Encryption pass order:
     *
     * P, P-1, ..., 1
     *
     * Therefore decryption must apply
     * inverse passes in reverse order:
     *
     * 1, 2, ..., P.
     */
    for (
        std::uint8_t pass = 1U;
        pass <= passes;
        ++pass
    ) {
        const bool flipped =
            (pass % 2U) != 0U;

        current =
            decrypt_single_pass(
                current,
                controls,
                flipped
            );
    }

    return current;
}

FettehaEncryptionResult2023
FettehaDnaCipher2023::encrypt(
    const std::span<const std::uint8_t> image,
    const Key& key
) {
    const auto initial_state =
        derive_initial_state(key);

    const auto p =
        iteration_count(image);

    return {
        encrypt_with_initial_state(
            image,
            initial_state
        ),
        p
    };
}

std::vector<std::uint8_t>
FettehaDnaCipher2023::decrypt(
    const std::span<const std::uint8_t> ciphertext,
    const Key& key,
    const std::uint8_t p
) {
    const auto initial_state =
        derive_initial_state(key);

    return decrypt_with_initial_state(
        ciphertext,
        initial_state,
        p
    );
}


}  // namespace bioentropy
