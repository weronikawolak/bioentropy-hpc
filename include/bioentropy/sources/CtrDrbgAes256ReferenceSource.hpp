#pragma once

#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace bioentropy {

class CtrDrbgAes256 {
public:
    static constexpr std::size_t KeyBytes = 32;
    static constexpr std::size_t BlockBytes = 16;
    static constexpr std::size_t SeedBytes =
        KeyBytes + BlockBytes;

    static constexpr std::size_t MaxRequestBytes =
        65536;

    using SeedMaterial =
        std::array<std::uint8_t, SeedBytes>;

    explicit CtrDrbgAes256(
        const SeedMaterial& entropy_input
    );

    void reset(
        const SeedMaterial& entropy_input
    );

    /*
     * One SP 800-90A Generate request.
     *
     * This implementation intentionally uses:
     * - AES-256
     * - no derivation function
     * - no prediction resistance
     * - no additional input
     */
    void generate(
        std::span<std::uint8_t> output
    );

private:
    void increment_v();

    void update(
        const SeedMaterial& provided_data
    );

    void encrypt_blocks(
        std::span<const std::uint8_t> input,
        std::span<std::uint8_t> output
    ) const;

    std::array<std::uint8_t, KeyBytes> key_{};
    std::array<std::uint8_t, BlockBytes> v_{};

    std::uint64_t reseed_counter_{0};
};


class CtrDrbgAes256ReferenceSource final
    : public RandomnessSource {
public:
    explicit CtrDrbgAes256ReferenceSource(
        Seed256 seed
    );

    std::string_view name()
        const noexcept override;

    bool deterministic()
        const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

private:
    static CtrDrbgAes256::SeedMaterial
    derive_seed_material(
        const Seed256& seed
    );

    void refill();

    Seed256 seed_{};

    CtrDrbgAes256 drbg_;

    std::array<
        std::uint8_t,
        CtrDrbgAes256::MaxRequestBytes
    > request_buffer_{};

    std::size_t buffer_offset_{
        request_buffer_.size()
    };
};

} // namespace bioentropy
