#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace bioentropy {

class AsconAead128 {
public:
    static constexpr std::size_t KeyBytes = 16;
    static constexpr std::size_t NonceBytes = 16;
    static constexpr std::size_t TagBytes = 16;

    using Key =
        std::array<std::uint8_t, KeyBytes>;

    using Nonce =
        std::array<std::uint8_t, NonceBytes>;

    [[nodiscard]]
    std::vector<std::uint8_t> encrypt(
        std::span<const std::uint8_t> plaintext,
        std::span<const std::uint8_t> associated_data,
        const Key& key,
        const Nonce& nonce
    ) const;

    [[nodiscard]]
    std::optional<std::vector<std::uint8_t>>
    decrypt(
        std::span<const std::uint8_t> ciphertext,
        std::span<const std::uint8_t> associated_data,
        const Key& key,
        const Nonce& nonce
    ) const;
};

}  // namespace bioentropy
