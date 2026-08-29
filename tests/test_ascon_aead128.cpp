#include "bioentropy/crypto/AsconAead128.hpp"

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
make_data(std::size_t size) {
    std::vector<std::uint8_t> data(size);

    for (std::size_t i = 0; i < size; ++i) {
        data[i] =
            static_cast<std::uint8_t>(
                (i * 37U + 11U) & 0xffU
            );
    }

    return data;
}

bioentropy::AsconAead128::Key
make_key() {
    bioentropy::AsconAead128::Key key{};

    for (std::size_t i = 0; i < key.size(); ++i) {
        key[i] =
            static_cast<std::uint8_t>(i);
    }

    return key;
}

bioentropy::AsconAead128::Nonce
make_nonce() {
    bioentropy::AsconAead128::Nonce nonce{};

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
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(message_size);

    const auto associated_data =
        make_data(23);

    const auto ciphertext =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    require(
        ciphertext.size()
            == plaintext.size()
               + bioentropy::
                 AsconAead128::TagBytes,
        "ciphertext overhead is not 16 bytes"
    );

    const auto recovered =
        aead.decrypt(
            ciphertext,
            associated_data,
            key,
            nonce
        );

    require(
        recovered.has_value(),
        "valid ciphertext rejected"
    );

    require(
        *recovered == plaintext,
        "round-trip plaintext mismatch"
    );
}

void test_determinism() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(128);

    const auto associated_data =
        make_data(11);

    const auto first =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    const auto second =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    require(
        first == second,
        "AEAD output is not deterministic "
        "for identical inputs"
    );
}

void test_ciphertext_tamper() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(128);

    const auto associated_data =
        make_data(17);

    auto ciphertext =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    ciphertext[10] ^= 0x01;

    require(
        !aead.decrypt(
            ciphertext,
            associated_data,
            key,
            nonce
        ).has_value(),
        "modified ciphertext accepted"
    );
}

void test_tag_tamper() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(64);

    const auto associated_data =
        make_data(9);

    auto ciphertext =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    ciphertext.back() ^= 0x80;

    require(
        !aead.decrypt(
            ciphertext,
            associated_data,
            key,
            nonce
        ).has_value(),
        "modified authentication tag accepted"
    );
}

void test_wrong_associated_data() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(64);

    const auto associated_data =
        make_data(20);

    auto wrong_ad =
        associated_data;

    wrong_ad[0] ^= 0x01;

    const auto ciphertext =
        aead.encrypt(
            plaintext,
            associated_data,
            key,
            nonce
        );

    require(
        !aead.decrypt(
            ciphertext,
            wrong_ad,
            key,
            nonce
        ).has_value(),
        "modified associated data accepted"
    );
}

void test_wrong_key() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();

    auto wrong_key = key;
    wrong_key[0] ^= 0x01;

    const auto nonce = make_nonce();

    const auto plaintext =
        make_data(64);

    const auto ciphertext =
        aead.encrypt(
            plaintext,
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

void test_wrong_nonce() {
    const bioentropy::AsconAead128 aead;

    const auto key = make_key();
    const auto nonce = make_nonce();

    auto wrong_nonce = nonce;
    wrong_nonce[15] ^= 0x01;

    const auto plaintext =
        make_data(64);

    const auto ciphertext =
        aead.encrypt(
            plaintext,
            {},
            key,
            nonce
        );

    require(
        !aead.decrypt(
            ciphertext,
            {},
            key,
            wrong_nonce
        ).has_value(),
        "wrong nonce accepted"
    );
}

}  // namespace

int main() {
    for (
        const std::size_t size :
        {
            0UL,
            1UL,
            15UL,
            16UL,
            17UL,
            64UL,
            1024UL
        }
    ) {
        test_round_trip(size);
    }

    test_determinism();
    test_ciphertext_tamper();
    test_tag_tamper();
    test_wrong_associated_data();
    test_wrong_key();
    test_wrong_nonce();

    std::cout
        << "Ascon-AEAD128 tests passed\n";

    return EXIT_SUCCESS;
}
