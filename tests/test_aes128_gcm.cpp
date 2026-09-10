#include "bioentropy/crypto/Aes128Gcm.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>

namespace {

void require(
    bool condition,
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

void test_known_answer() {
    const bioentropy::Aes128Gcm aead;

    bioentropy::Aes128Gcm::Key key{};
    bioentropy::Aes128Gcm::Nonce nonce{};

    const std::vector<std::uint8_t>
        plaintext(16, 0);

    const std::array<std::uint8_t, 32>
        expected = {
            0x03, 0x88, 0xda, 0xce,
            0x60, 0xb6, 0xa3, 0x92,
            0xf3, 0x28, 0xc2, 0xb9,
            0x71, 0xb2, 0xfe, 0x78,

            0xab, 0x6e, 0x47, 0xd4,
            0x2c, 0xec, 0x13, 0xbd,
            0xf5, 0x3a, 0x67, 0xb2,
            0x12, 0x57, 0xbd, 0xdf
        };

    const auto encrypted =
        aead.encrypt(
            plaintext,
            {},
            key,
            nonce
        );

    require(
        std::equal(
            encrypted.begin(),
            encrypted.end(),
            expected.begin(),
            expected.end()
        ),
        "AES-GCM known-answer mismatch"
    );

    const auto recovered =
        aead.decrypt(
            encrypted,
            {},
            key,
            nonce
        );

    require(
        recovered.has_value()
        && *recovered == plaintext,
        "AES-GCM KAT decrypt failed"
    );
}

void test_round_trip() {
    const bioentropy::Aes128Gcm aead;

    bioentropy::Aes128Gcm::Key key{};
    bioentropy::Aes128Gcm::Nonce nonce{};

    for (
        std::size_t i = 0;
        i < key.size();
        ++i
    ) {
        key[i] =
            static_cast<std::uint8_t>(i);
    }

    for (
        std::size_t i = 0;
        i < nonce.size();
        ++i
    ) {
        nonce[i] =
            static_cast<std::uint8_t>(
                0xa0 + i
            );
    }

    std::vector<std::uint8_t>
        plaintext(1024);

    for (
        std::size_t i = 0;
        i < plaintext.size();
        ++i
    ) {
        plaintext[i] =
            static_cast<std::uint8_t>(
                (37 * i + 11) & 0xff
            );
    }

    const std::vector<std::uint8_t>
        aad = {
            1, 2, 3, 4, 5, 6
        };

    auto encrypted =
        aead.encrypt(
            plaintext,
            aad,
            key,
            nonce
        );

    const auto recovered =
        aead.decrypt(
            encrypted,
            aad,
            key,
            nonce
        );

    require(
        recovered.has_value()
        && *recovered == plaintext,
        "AES-GCM round-trip failed"
    );

    encrypted.back() ^= 0x01;

    require(
        !aead.decrypt(
            encrypted,
            aad,
            key,
            nonce
        ).has_value(),
        "AES-GCM modified tag accepted"
    );
}

void test_empty_plaintext() {
    const bioentropy::Aes128Gcm aead;

    bioentropy::Aes128Gcm::Key key{};
    bioentropy::Aes128Gcm::Nonce nonce{};

    const auto encrypted =
        aead.encrypt(
            {},
            {},
            key,
            nonce
        );

    require(
        encrypted.size()
        == bioentropy::Aes128Gcm::TagBytes,
        "AES-GCM empty output size incorrect"
    );

    const auto recovered =
        aead.decrypt(
            encrypted,
            {},
            key,
            nonce
        );

    require(
        recovered.has_value()
        && recovered->empty(),
        "AES-GCM empty round-trip failed"
    );
}

} // namespace

int main() {
    test_known_answer();
    test_round_trip();
    test_empty_plaintext();

    std::cout
        << "AES-128-GCM tests passed\n";

    return EXIT_SUCCESS;
}
