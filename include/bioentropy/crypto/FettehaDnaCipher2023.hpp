#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace bioentropy {

enum class DnaBase2023 : std::uint8_t {
    A,
    C,
    G,
    T
};

struct LorenzParameters2023 {
    double h{1.0 / 128.0};
    double sigma{8.0};
    double rho{16.0};
    double beta{2.0};
};

struct LorenzState2023 {
    double x{};
    double y{};
    double z{};
};

struct FettehaRawInitialConditions2023 {
    std::uint32_t x0{};
    std::uint32_t y0{};
    std::uint32_t z0{};
};

struct DnaControlValues2023 {
    std::array<std::uint8_t, 4> x_rules{};
    std::array<std::uint8_t, 4> y_rules{};
    std::uint8_t z_bin{};

    bool operator==(
        const DnaControlValues2023&
    ) const = default;
};

class FettehaDnaCipher2023 {
public:
    using Key =
        std::array<std::uint8_t, 32>;

    using KeyWords =
        std::array<std::uint32_t, 8>;

    [[nodiscard]]
    static std::uint64_t pixel_sum(
        std::span<const std::uint8_t> image
    );

    [[nodiscard]]
    static std::uint8_t iteration_count(
        std::span<const std::uint8_t> image
    );

    [[nodiscard]]
    static KeyWords split_key(
        const Key& key
    );

    [[nodiscard]]
    static FettehaRawInitialConditions2023
    derive_raw_initial_conditions(
        const KeyWords& words
    );

    [[nodiscard]]
    static LorenzState2023 lorenz_step(
        const LorenzState2023& state,
        const LorenzParameters2023& parameters = {}
    );

    [[nodiscard]]
    static LorenzState2023 advance_lorenz(
        LorenzState2023 state,
        std::size_t steps,
        const LorenzParameters2023& parameters = {}
    );

    [[nodiscard]]
    static std::uint8_t extract_rule_index(
        double value,
        int binary_shift
    );

    [[nodiscard]]
    static DnaControlValues2023
    derive_dna_controls(
        const LorenzState2023& state
    );

    [[nodiscard]]
    static DnaBase2023 dna_encode_pair(
        std::uint8_t pair,
        std::uint8_t rule
    );

    [[nodiscard]]
    static std::uint8_t dna_decode_base(
        DnaBase2023 base,
        std::uint8_t rule
    );

    [[nodiscard]]
    static std::uint8_t dna_transform_pair(
        std::uint8_t pair,
        std::uint8_t encode_rule,
        std::uint8_t decode_rule
    );

    [[nodiscard]]
    static std::array<std::uint8_t, 4>
    split_pixel_pairs(
        std::uint8_t pixel
    );

    [[nodiscard]]
    static std::uint8_t join_pixel_pairs(
        const std::array<std::uint8_t, 4>& pairs
    );

    [[nodiscard]]
    static std::uint8_t dna_transform_pixel(
        std::uint8_t pixel,
        const DnaControlValues2023& controls
    );

    [[nodiscard]]
    static std::uint8_t diffuse_pixel(
        std::uint8_t transformed_pixel,
        std::uint8_t z_bin,
        std::uint8_t mask
    );

    [[nodiscard]]
    static std::vector<std::uint8_t>
    encrypt_single_pass(
        std::span<const std::uint8_t> image,
        std::span<const DnaControlValues2023> controls,
        bool flipped
    );

    [[nodiscard]]
    static std::vector<DnaControlValues2023>
    generate_control_sequence(
        const LorenzState2023& initial_state,
        std::size_t count,
        std::size_t discard = 200
    );

    [[nodiscard]]
    static std::vector<std::uint8_t>
    encrypt_with_initial_state(
        std::span<const std::uint8_t> image,
        const LorenzState2023& initial_state
    );
};

}  // namespace bioentropy
