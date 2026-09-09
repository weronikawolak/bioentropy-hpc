#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace bioentropy {

class ChaCha20Poly1305 {
public:
    static constexpr std::size_t KeyBytes = 32;
    static constexpr std::size_t NonceBytes = 12;
    static constexpr std::size_t TagBytes = 16;

    using Key =
        std::array<std::uint8_t, KeyBytes>;

    using Nonce =
        std::array<std::uint8_t, NonceBytes>;

    std::vector<std::uint8_t> encrypt(
        std::span<const std::uint8_t> plaintext,
        std::span<const std::uint8_t> associated_data,
        const Key& key,
        const Nonce& nonce
    ) const;

    std::optional<std::vector<std::uint8_t>>
    decrypt(
        std::span<const std::uint8_t> ciphertext_and_tag,
        std::span<const std::uint8_t> associated_data,
        const Key& key,
        const Nonce& nonce
    ) const;
};

} // namespace bioentropy
