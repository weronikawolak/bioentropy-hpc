#include "bioentropy/sources/ChaCha20ReferenceSource.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string_view>

#include <openssl/evp.h>

namespace bioentropy {

namespace {

constexpr std::string_view KEY_DOMAIN =
    "BIOENTROPY-HPC-CHACHA20-KEY-v1";

constexpr std::string_view NONCE_DOMAIN =
    "BIOENTROPY-HPC-CHACHA20-NONCE-v1";

} // namespace

ChaCha20ReferenceSource::
ChaCha20ReferenceSource(
    ChaCha20ReferenceConfig config,
    Seed256 seed
)
    : config_(config),
      seed_(seed) {

    derive_key_and_nonce();
    reset();
}

ChaCha20ReferenceSource::
~ChaCha20ReferenceSource() {
    if (context_ != nullptr) {
        EVP_CIPHER_CTX_free(context_);
    }
}

std::string_view
ChaCha20ReferenceSource::name() const noexcept {
    return "chacha20_reference";
}

bool
ChaCha20ReferenceSource::deterministic() const noexcept {
    return true;
}

std::array<std::uint8_t, 32>
ChaCha20ReferenceSource::derive_sha256(
    std::string_view domain,
    const Seed256& seed
) {
    EVP_MD_CTX* digest_context =
        EVP_MD_CTX_new();

    if (digest_context == nullptr) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    std::array<std::uint8_t, 32> digest{};

    unsigned int digest_length = 0;

    bool success = true;

    success =
        success &&
        EVP_DigestInit_ex(
            digest_context,
            EVP_sha256(),
            nullptr
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            digest_context,
            domain.data(),
            domain.size()
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            digest_context,
            seed.data(),
            seed.size()
        ) == 1;

    success =
        success &&
        EVP_DigestFinal_ex(
            digest_context,
            digest.data(),
            &digest_length
        ) == 1;

    EVP_MD_CTX_free(digest_context);

    if (
        !success ||
        digest_length != digest.size()
    ) {
        throw std::runtime_error(
            "failed to derive ChaCha20 material"
        );
    }

    return digest;
}

void
ChaCha20ReferenceSource::
derive_key_and_nonce() {
    key_ =
        derive_sha256(
            KEY_DOMAIN,
            seed_
        );

    const auto nonce_digest =
        derive_sha256(
            NONCE_DOMAIN,
            seed_
        );

    std::copy_n(
        nonce_digest.begin(),
        nonce_.size(),
        nonce_.begin()
    );
}

void
ChaCha20ReferenceSource::
initialize_context() {
    if (context_ != nullptr) {
        EVP_CIPHER_CTX_free(context_);
        context_ = nullptr;
    }

    context_ =
        EVP_CIPHER_CTX_new();

    if (context_ == nullptr) {
        throw std::runtime_error(
            "EVP_CIPHER_CTX_new failed"
        );
    }

    /*
     * OpenSSL 3.x EVP_chacha20 IV:
     *
     * bytes 0..7:
     *   64-bit initial counter,
     *   little-endian
     *
     * bytes 8..15:
     *   64-bit nonce
     */
    std::array<std::uint8_t, 16> iv{};

    for (std::size_t i = 0; i < 8; ++i) {
        iv[i] =
            static_cast<std::uint8_t>(
                (
                    config_.initial_counter
                    >> (8U * i)
                )
                & 0xFFU
            );
    }

    std::copy(
        nonce_.begin(),
        nonce_.end(),
        iv.begin() + 8
    );

    if (
        EVP_EncryptInit_ex(
            context_,
            EVP_chacha20(),
            nullptr,
            key_.data(),
            iv.data()
        ) != 1
    ) {
        EVP_CIPHER_CTX_free(context_);
        context_ = nullptr;

        throw std::runtime_error(
            "failed to initialize ChaCha20 EVP context"
        );
    }
}

void
ChaCha20ReferenceSource::reset() {
    initialize_context();
}

void
ChaCha20ReferenceSource::generate(
    std::span<std::uint8_t> output
) {
    if (output.empty()) {
        return;
    }

    if (context_ == nullptr) {
        throw std::runtime_error(
            "ChaCha20 context is not initialized"
        );
    }

    constexpr std::size_t BUFFER_SIZE =
        65'536;

    std::array<
        std::uint8_t,
        BUFFER_SIZE
    > zero_input{};

    std::size_t offset = 0;

    while (offset < output.size()) {
        const std::size_t remaining =
            output.size() - offset;

        const std::size_t current_size =
            std::min(
                remaining,
                BUFFER_SIZE
            );

        int written = 0;

        if (
            EVP_EncryptUpdate(
                context_,
                output.data() + offset,
                &written,
                zero_input.data(),
                static_cast<int>(
                    current_size
                )
            ) != 1
        ) {
            throw std::runtime_error(
                "ChaCha20 generation failed"
            );
        }

        if (
            written !=
            static_cast<int>(current_size)
        ) {
            throw std::runtime_error(
                "ChaCha20 generated unexpected "
                "number of bytes"
            );
        }

        offset += current_size;
    }
}

} // namespace bioentropy
