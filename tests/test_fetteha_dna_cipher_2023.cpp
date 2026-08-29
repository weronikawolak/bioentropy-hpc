#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
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
    using bioentropy::DnaBase2023;
    using bioentropy::FettehaDnaCipher2023;

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
        "P mismatch"
    );

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
        "X0 mismatch"
    );

    require(
        initial.y0
        == (
            words[2]
            ^ words[3]
            ^ words[4]
            ^ words[5]
        ),
        "Y0 mismatch"
    );

    require(
        initial.z0
        == (
            words[4]
            ^ words[5]
            ^ words[6]
            ^ words[7]
        ),
        "Z0 mismatch"
    );

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
        near(next.x, 10.0),
        "Lorenz X1 mismatch"
    );

    require(
        near(next.y, 10.390625),
        "Lorenz Y1 mismatch"
    );

    require(
        near(next.z, 10.625),
        "Lorenz Z1 mismatch"
    );

    /*
     * Exact Fetteha et al. 2023
     * Table 1.
     *
     * Columns:
     * 00, 01, 10, 11
     */
    const std::array<
        std::array<DnaBase2023, 4>,
        8
    > expected_rules{{
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

    for (
        std::uint8_t rule = 1;
        rule <= 8;
        ++rule
    ) {
        for (
            std::uint8_t pair = 0;
            pair < 4;
            ++pair
        ) {
            const auto base =
                FettehaDnaCipher2023::
                    dna_encode_pair(
                        pair,
                        rule
                    );

            require(
                base
                == expected_rules[
                    rule - 1
                ][pair],
                "DNA Table 1 mismatch"
            );

            require(
                FettehaDnaCipher2023::
                    dna_decode_base(
                        base,
                        rule
                    )
                == pair,
                "DNA round-trip mismatch"
            );

            require(
                FettehaDnaCipher2023::
                    dna_transform_pair(
                        pair,
                        rule,
                        rule
                    )
                == pair,
                "same-rule transform mismatch"
            );
        }
    }

    /*
     * Cross-rule test.
     *
     * Rule 1:
     * 00 -> G
     *
     * Rule 8:
     * G -> 01
     *
     * Therefore:
     * encode(00, rule 1)
     * decode(rule 8)
     * -> 01
     */
    require(
        FettehaDnaCipher2023::
            dna_transform_pair(
                0b00,
                1,
                8
            )
        == 0b01,
        "cross-rule DNA transform mismatch"
    );

    bool invalid_rule_rejected = false;

    try {
        (void)
            FettehaDnaCipher2023::
                dna_encode_pair(
                    0,
                    0
                );
    } catch (
        const std::invalid_argument&
    ) {
        invalid_rule_rejected = true;
    }

    require(
        invalid_rule_rejected,
        "invalid DNA rule was not rejected"
    );


    /*
     * Algorithm 1 chaotic warm-up.
     *
     * The paper discards the first
     * 200 Lorenz outputs.
     */
    const bioentropy::LorenzState2023
        published_demo_initial{
            10.0,
            10.0,
            10.0
        };

    const auto after_200 =
        FettehaDnaCipher2023::
            advance_lorenz(
                published_demo_initial,
                200
            );

    require(
        near(
            after_200.x,
            -4.708084970346886,
            1.0e-9
        ),
        "Lorenz X200 regression mismatch"
    );

    require(
        near(
            after_200.y,
            0.4125556683661835,
            1.0e-9
        ),
        "Lorenz Y200 regression mismatch"
    );

    require(
        near(
            after_200.z,
            20.470682226520772,
            1.0e-9
        ),
        "Lorenz Z200 regression mismatch"
    );

    /*
     * i = 201 is the first state used
     * after the 200-output discard.
     */
    const auto first_usable =
        FettehaDnaCipher2023::
            lorenz_step(
                after_200
            );

    require(
        near(
            first_usable.x,
            -4.388044930427319,
            1.0e-9
        ),
        "Lorenz X201 regression mismatch"
    );

    require(
        near(
            first_usable.y,
            0.5737728256280056,
            1.0e-9
        ),
        "Lorenz Y201 regression mismatch"
    );

    require(
        near(
            first_usable.z,
            20.13565322968712,
            1.0e-9
        ),
        "Lorenz Z201 regression mismatch"
    );

    const auto first_controls =
        FettehaDnaCipher2023::
            derive_dna_controls(
                first_usable
            );

    const std::array<std::uint8_t, 4>
        expected_x_rules{
            7,
            3,
            2,
            7
        };

    const std::array<std::uint8_t, 4>
        expected_y_rules{
            5,
            3,
            7,
            2
        };

    require(
        first_controls.x_rules
        == expected_x_rules,
        "Xbin rule extraction mismatch"
    );

    require(
        first_controls.y_rules
        == expected_y_rules,
        "Ybin rule extraction mismatch"
    );

    require(
        first_controls.z_bin == 3,
        "Zbin extraction mismatch"
    );

    /*
     * Independent synthetic regression
     * including negative values.
     *
     * This specifically verifies MATLAB
     * fix()/mod() semantics.
     */
    const bioentropy::LorenzState2023
        synthetic_controls_state{
            0.123456789,
            -0.234567891,
            0.345678912
        };

    const auto synthetic_controls =
        FettehaDnaCipher2023::
            derive_dna_controls(
                synthetic_controls_state
            );

    require(
        synthetic_controls.x_rules
        == std::array<std::uint8_t, 4>{
            4, 3, 7, 8
        },
        "synthetic X control mismatch"
    );

    require(
        synthetic_controls.y_rules
        == std::array<std::uint8_t, 4>{
            8, 5, 4, 8
        },
        "negative MATLAB-mod semantics mismatch"
    );

    require(
        synthetic_controls.z_bin == 3,
        "synthetic Z control mismatch"
    );

    /*
     * Every DNA selector generated by
     * Algorithm 1 must lie in [1, 8].
     */
    for (
        const auto rule :
        first_controls.x_rules
    ) {
        require(
            rule >= 1 && rule <= 8,
            "X rule outside [1, 8]"
        );
    }

    for (
        const auto rule :
        first_controls.y_rules
    ) {
        require(
            rule >= 1 && rule <= 8,
            "Y rule outside [1, 8]"
        );
    }


    /*
     * Exhaustive byte split/join test.
     */
    for (
        unsigned value = 0;
        value <= 255;
        ++value
    ) {
        const auto byte =
            static_cast<std::uint8_t>(
                value
            );

        const auto pairs =
            FettehaDnaCipher2023::
                split_pixel_pairs(byte);

        require(
            FettehaDnaCipher2023::
                join_pixel_pairs(pairs)
            == byte,
            "pixel pair split/join mismatch"
        );
    }

    /*
     * If encoding and decoding use the
     * same DNA rule, the DNA stage must
     * reproduce the original 2-bit value.
     */
    bioentropy::DnaControlValues2023
        identity_controls{
            {1, 2, 3, 4},
            {1, 2, 3, 4},
            3
        };

    for (
        unsigned value = 0;
        value <= 255;
        ++value
    ) {
        const auto byte =
            static_cast<std::uint8_t>(
                value
            );

        require(
            FettehaDnaCipher2023::
                dna_transform_pixel(
                    byte,
                    identity_controls
                )
            == byte,
            "same-rule DNA pixel transform mismatch"
        );
    }

    /*
     * Algorithm 1 diffusion / feedback test.
     *
     * DNA stage is identity here, therefore:
     *
     * C0 = 0x12 XOR 3 XOR 0
     *    = 0x11
     *
     * C1 = 0x34 XOR 3 XOR 0x11
     *    = 0x26
     *
     * C2 = 0x56 XOR 3 XOR 0x26
     *    = 0x73
     */
    const std::vector<std::uint8_t>
        small_image{
            0x12,
            0x34,
            0x56
        };

    const std::vector<
        bioentropy::DnaControlValues2023
    > identity_control_sequence(
        small_image.size(),
        identity_controls
    );

    const auto normal_pass =
        FettehaDnaCipher2023::
            encrypt_single_pass(
                small_image,
                identity_control_sequence,
                false
            );

    require(
        normal_pass
        == std::vector<std::uint8_t>{
            0x11,
            0x26,
            0x73
        },
        "normal-order feedback encryption mismatch"
    );

    /*
     * Odd-P pixel confusion:
     * process reversed image order.
     *
     * 0x56 -> 0x55
     * 0x34 -> 0x62
     * 0x12 -> 0x73
     */
    const auto flipped_pass =
        FettehaDnaCipher2023::
            encrypt_single_pass(
                small_image,
                identity_control_sequence,
                true
            );

    require(
        flipped_pass
        == std::vector<std::uint8_t>{
            0x55,
            0x62,
            0x73
        },
        "flipped-order feedback encryption mismatch"
    );

    /*
     * DNA transform must also support
     * different encoding and decoding
     * rules for each pair.
     */
    bioentropy::DnaControlValues2023
        cross_rule_controls{
            {1, 1, 1, 1},
            {8, 8, 8, 8},
            1
        };

    const auto cross_rule_pixel =
        FettehaDnaCipher2023::
            dna_transform_pixel(
                0x00,
                cross_rule_controls
            );

    require(
        cross_rule_pixel != 0x00,
        "cross-rule DNA transform had no effect"
    );

    std::cout
        << "Fetteha DNA cipher 2023 "
        << "core and DNA tests passed\n";

    return EXIT_SUCCESS;
}
