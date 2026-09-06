#include "bioentropy/crypto/AsconAead128.hpp"

extern "C" {
#include "crypto_aead.h"
}

#include <limits>
#include <stdexcept>

namespace bioentropy {

namespace {

const unsigned char* input_ptr(
    std::span<const std::uint8_t> data
) {
    static const unsigned char empty = 0;

    return data.empty()
        ? &empty
        : data.data();
}

}  // namespace

std::vector<std::uint8_t>
AsconAead128::encrypt(
    std::span<const std::uint8_t> plaintext,
    std::span<const std::uint8_t> associated_data,
    const Key& key,
    const Nonce& nonce
) const {
    if (
        plaintext.size()
        > std::numeric_limits<
            unsigned long long
        >::max()
    ) {
        throw std::overflow_error(
            "plaintext too large"
        );
    }

    std::vector<std::uint8_t> ciphertext(
        plaintext.size() + TagBytes
    );

    unsigned long long ciphertext_length = 0;

    const int result =
        crypto_aead_encrypt(
            ciphertext.data(),
            &ciphertext_length,
            input_ptr(plaintext),
            static_cast<unsigned long long>(
                plaintext.size()
            ),
            input_ptr(associated_data),
            static_cast<unsigned long long>(
                associated_data.size()
            ),
            nullptr,
            nonce.data(),
            key.data()
        );

    if (result != 0) {
        throw std::runtime_error(
            "Ascon-AEAD128 encryption failed"
        );
    }

    ciphertext.resize(
        static_cast<std::size_t>(
            ciphertext_length
        )
    );

    return ciphertext;
}

std::optional<std::vector<std::uint8_t>>
AsconAead128::decrypt(
    std::span<const std::uint8_t> ciphertext,
    std::span<const std::uint8_t> associated_data,
    const Key& key,
    const Nonce& nonce
) const {
    if (ciphertext.size() < TagBytes) {
        return std::nullopt;
    }

    std::vector<std::uint8_t> plaintext(
        ciphertext.size() - TagBytes
    );

    unsigned long long plaintext_length = 0;

    const int result =
        crypto_aead_decrypt(
            plaintext.data(),
            &plaintext_length,
            nullptr,
            input_ptr(ciphertext),
            static_cast<unsigned long long>(
                ciphertext.size()
            ),
            input_ptr(associated_data),
            static_cast<unsigned long long>(
                associated_data.size()
            ),
            nonce.data(),
            key.data()
        );

    if (result != 0) {
        return std::nullopt;
    }

    plaintext.resize(
        static_cast<std::size_t>(
            plaintext_length
        )
    );

    return plaintext;
}

}  // namespace bioentropy
