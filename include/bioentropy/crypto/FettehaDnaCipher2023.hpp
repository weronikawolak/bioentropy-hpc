#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>

namespace bioentropy {

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
};

}  // namespace bioentropy
