#pragma once

#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <array>
#include <cstdint>
#include <span>
#include <string_view>

#include <openssl/evp.h>

namespace bioentropy {

class ChaCha20ReferenceSource final
    : public RandomnessSource {
public:
    ChaCha20ReferenceSource(
        ChaCha20ReferenceConfig config,
        Seed256 seed
    );

    ~ChaCha20ReferenceSource() override;

    ChaCha20ReferenceSource(
        const ChaCha20ReferenceSource&
    ) = delete;

    ChaCha20ReferenceSource& operator=(
        const ChaCha20ReferenceSource&
    ) = delete;

    std::string_view name() const noexcept override;

    bool deterministic() const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

private:
    ChaCha20ReferenceConfig config_;
    Seed256 seed_;

    std::array<std::uint8_t, 32> key_{};
    std::array<std::uint8_t, 8> nonce_{};

    EVP_CIPHER_CTX* context_{nullptr};

    static std::array<std::uint8_t, 32>
    derive_sha256(
        std::string_view domain,
        const Seed256& seed
    );

    void derive_key_and_nonce();

    void initialize_context();
};

} // namespace bioentropy
