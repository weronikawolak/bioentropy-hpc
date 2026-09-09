#include "bioentropy/crypto/ChaCha20Poly1305.hpp"

#include <cstddef>
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

std::vector<std::uint8_t>
make_data(
    std::size_t size
) {
    std::vector<std::uint8_t>
        data(size);

    for (
        std::size_t i = 0;
        i < size;
        ++i
    ) {
        data[i] =
            static_cast<std::uint8_t>(
                (i * 37U + 11U)
                & 0xffU
            );
    }

    return data;
}

bioentropy::ChaCha20Poly1305::Key
make_key() {
    bioentropy::
        ChaCha20Poly1305::Key key{};

    for (
        std::size_t i = 0;
        i < key.size();
        ++i
    ) {
        key[i] =
            static_cast<std::uint8_t>(
                i
            );
    }

    return key;
}

bioentropy::ChaCha20Poly1305::Nonce
make_nonce() {
    bioentropy::
        ChaCha20Poly1305::Nonce nonce{};

    for (
        std::size_t i = 0;
        i < nonce.size();
        ++i
    ) {
        nonce[i] =
            static_cast<std::uint8_t>(
                0xa0U + i
            );
    }

    return nonce;
}

void test_round_trip(
    std::size_t message_size
) {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    const auto nonce =
        make_nonce();

    const auto plaintext =
        make_data(
            message_size
        );

    const auto aad =
        make_data(23);

    const auto ciphertext =
        aead.encrypt(
            plaintext,
            aad,
            key,
            nonce
        );

    require(
        ciphertext.size()
            == plaintext.size()
            + bioentropy::
              ChaCha20Poly1305::
              TagBytes,
        "incorrect ciphertext/tag size"
    );

    const auto recovered =
        aead.decrypt(
            ciphertext,
            aad,
            key,
            nonce
        );

    require(
        recovered.has_value(),
        "valid ciphertext rejected"
    );

    require(
        *recovered == plaintext,
        "round-trip mismatch"
    );
}

void test_determinism() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    const auto nonce =
        make_nonce();

    const auto plaintext =
        make_data(128);

    const auto aad =
        make_data(11);

    const auto first =
        aead.encrypt(
            plaintext,
            aad,
            key,
            nonce
        );

    const auto second =
        aead.encrypt(
            plaintext,
            aad,
            key,
            nonce
        );

    require(
        first == second,
        "identical inputs produced "
        "different outputs"
    );
}

void test_ciphertext_tamper() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    const auto nonce =
        make_nonce();

    auto ciphertext =
        aead.encrypt(
            make_data(128),
            make_data(9),
            key,
            nonce
        );

    ciphertext[10] ^= 0x01;

    require(
        !aead.decrypt(
            ciphertext,
            make_data(9),
            key,
            nonce
        ).has_value(),
        "modified ciphertext accepted"
    );
}

void test_tag_tamper() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    const auto nonce =
        make_nonce();

    const auto aad =
        make_data(9);

    auto ciphertext =
        aead.encrypt(
            make_data(64),
            aad,
            key,
            nonce
        );

    ciphertext.back() ^= 0x80;

    require(
        !aead.decrypt(
            ciphertext,
            aad,
            key,
            nonce
        ).has_value(),
        "modified tag accepted"
    );
}

void test_wrong_aad() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    const auto nonce =
        make_nonce();

    const auto aad =
        make_data(20);

    auto wrong_aad =
        aad;

    wrong_aad[0] ^= 0x01;

    const auto ciphertext =
        aead.encrypt(
            make_data(64),
            aad,
            key,
            nonce
        );

    require(
        !aead.decrypt(
            ciphertext,
            wrong_aad,
            key,
            nonce
        ).has_value(),
        "wrong AAD accepted"
    );
}

void test_wrong_key() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const auto key =
        make_key();

    auto wrong_key =
        key;

    wrong_key[0] ^= 0x01;

    const auto nonce =
        make_nonce();

    const auto ciphertext =
        aead.encrypt(
            make_data(64),
            {},
            key,
            nonce
        );

    require(
        !aead.decrypt(
            ciphertext,
            {},
            wrong_key,
            nonce
        ).has_value(),
        "wrong key accepted"
    );
}

void test_short_ciphertext() {
    const bioentropy::
        ChaCha20Poly1305 aead;

    const std::vector<std::uint8_t>
        invalid(15);

    require(
        !aead.decrypt(
            invalid,
            {},
            make_key(),
            make_nonce()
        ).has_value(),
        "ciphertext shorter than tag accepted"
    );
}

} // namespace

int main() {
    test_round_trip(0);
    test_round_trip(1);
    test_round_trip(64);
    test_round_trip(1024);

    test_determinism();
    test_ciphertext_tamper();
    test_tag_tamper();
    test_wrong_aad();
    test_wrong_key();
    test_short_ciphertext();

    std::cout
        << "ChaCha20-Poly1305: "
        << "10 tests passed\n";

    return EXIT_SUCCESS;
}
