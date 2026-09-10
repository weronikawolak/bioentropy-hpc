#include "bioentropy/crypto/Aes128Gcm.hpp"
#include "bioentropy/crypto/AsconAead128.hpp"
#include "bioentropy/crypto/ChaCha20Poly1305.hpp"

#include <openssl/evp.h>

#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::size_t MaterialBytes = 104;

std::vector<std::uint8_t> read_file(
    const std::string& path
) {
    std::ifstream input(
        path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error(
            "cannot open material file"
        );
    }

    auto data =
        std::vector<std::uint8_t>(
            std::istreambuf_iterator<char>(
                input
            ),
            std::istreambuf_iterator<char>()
        );

    return data;
}

std::string sha256(
    std::span<const std::uint8_t> data
) {
    std::array<unsigned char, EVP_MAX_MD_SIZE>
        digest{};

    unsigned int digest_size = 0;

    const void* input =
        data.empty()
            ? nullptr
            : static_cast<const void*>(
                data.data()
            );

    if (
        EVP_Digest(
            input,
            data.size(),
            digest.data(),
            &digest_size,
            EVP_sha256(),
            nullptr
        ) != 1
    ) {
        throw std::runtime_error(
            "SHA-256 failed"
        );
    }

    std::ostringstream out;

    out << std::hex
        << std::setfill('0');

    for (
        unsigned int i = 0;
        i < digest_size;
        ++i
    ) {
        out << std::setw(2)
            << static_cast<unsigned int>(
                digest[i]
            );
    }

    return out.str();
}

template <typename Array>
void copy_field(
    std::span<const std::uint8_t> material,
    std::size_t offset,
    Array& output
) {
    if (
        offset + output.size()
        > material.size()
    ) {
        throw std::runtime_error(
            "material field outside input"
        );
    }

    std::copy_n(
        material.begin()
            + static_cast<std::ptrdiff_t>(
                offset
            ),
        output.size(),
        output.begin()
    );
}

std::vector<std::uint8_t>
make_plaintext() {
    std::vector<std::uint8_t>
        plaintext(4096);

    for (
        std::size_t i = 0;
        i < plaintext.size();
        ++i
    ) {
        plaintext[i] =
            static_cast<std::uint8_t>(
                (i * 37 + 11) & 0xff
            );
    }

    return plaintext;
}

std::vector<std::uint8_t>
make_aad() {
    std::vector<std::uint8_t>
        aad(32);

    for (
        std::size_t i = 0;
        i < aad.size();
        ++i
    ) {
        aad[i] =
            static_cast<std::uint8_t>(
                (i * 19 + 7) & 0xff
            );
    }

    return aad;
}

struct MaterialStats {
    std::size_t zero_bytes = 0;
    std::size_t unique_bytes = 0;
    double p1 = 0.0;
};

MaterialStats calculate_stats(
    std::span<const std::uint8_t> data
) {
    MaterialStats result;

    std::array<bool, 256> seen{};

    std::uint64_t ones = 0;

    for (const auto value : data) {
        if (value == 0) {
            ++result.zero_bytes;
        }

        seen[value] = true;

        ones += std::popcount(
            static_cast<unsigned int>(
                value
            )
        );
    }

    result.unique_bytes =
        static_cast<std::size_t>(
            std::count(
                seen.begin(),
                seen.end(),
                true
            )
        );

    const auto bits =
        static_cast<double>(
            data.size() * 8
        );

    result.p1 =
        bits == 0.0
            ? 0.0
            : static_cast<double>(
                ones
            ) / bits;

    return result;
}

} // namespace


int main(
    int argc,
    char* argv[]
) {
    if (argc != 5) {
        std::cerr
            << "Usage: "
            << argv[0]
            << " <material.bin>"
            << " <source>"
            << " <replicate_id>"
            << " <mode>\n";

        return 2;
    }

    try {
        const auto material =
            read_file(argv[1]);

        if (
            material.size()
            != MaterialBytes
        ) {
            throw std::runtime_error(
                "expected exactly 104 bytes "
                "of key material"
            );
        }

        const std::span<
            const std::uint8_t
        > material_span(
            material
        );

        bioentropy::AsconAead128::Key
            ascon_key{};

        bioentropy::AsconAead128::Nonce
            ascon_nonce{};

        bioentropy::ChaCha20Poly1305::Key
            chacha_key{};

        bioentropy::ChaCha20Poly1305::Nonce
            chacha_nonce{};

        bioentropy::Aes128Gcm::Key
            aes_key{};

        bioentropy::Aes128Gcm::Nonce
            aes_nonce{};

        copy_field(
            material_span,
            0,
            ascon_key
        );

        copy_field(
            material_span,
            16,
            ascon_nonce
        );

        copy_field(
            material_span,
            32,
            chacha_key
        );

        copy_field(
            material_span,
            64,
            chacha_nonce
        );

        copy_field(
            material_span,
            76,
            aes_key
        );

        copy_field(
            material_span,
            92,
            aes_nonce
        );

        const auto plaintext =
            make_plaintext();

        const auto aad =
            make_aad();

        const bioentropy::AsconAead128
            ascon;

        const bioentropy::ChaCha20Poly1305
            chacha;

        const bioentropy::Aes128Gcm
            aes;

        const auto ascon_ciphertext =
            ascon.encrypt(
                plaintext,
                aad,
                ascon_key,
                ascon_nonce
            );

        const auto chacha_ciphertext =
            chacha.encrypt(
                plaintext,
                aad,
                chacha_key,
                chacha_nonce
            );

        const auto aes_ciphertext =
            aes.encrypt(
                plaintext,
                aad,
                aes_key,
                aes_nonce
            );

        const auto ascon_plaintext =
            ascon.decrypt(
                ascon_ciphertext,
                aad,
                ascon_key,
                ascon_nonce
            );

        const auto chacha_plaintext =
            chacha.decrypt(
                chacha_ciphertext,
                aad,
                chacha_key,
                chacha_nonce
            );

        const auto aes_plaintext =
            aes.decrypt(
                aes_ciphertext,
                aad,
                aes_key,
                aes_nonce
            );

        const bool ascon_ok =
            ascon_plaintext.has_value()
            && *ascon_plaintext
                == plaintext;

        const bool chacha_ok =
            chacha_plaintext.has_value()
            && *chacha_plaintext
                == plaintext;

        const bool aes_ok =
            aes_plaintext.has_value()
            && *aes_plaintext
                == plaintext;

        const auto stats =
            calculate_stats(
                material_span
            );

        std::cout
            << "source\t"
            << "replicate_id\t"
            << "mode\t"
            << "material_sha256\t"
            << "zero_bytes\t"
            << "unique_bytes\t"
            << "p1\t"

            << "ascon_key_sha256\t"
            << "ascon_nonce_sha256\t"
            << "ascon_ciphertext_sha256\t"
            << "ascon_roundtrip\t"

            << "chacha_key_sha256\t"
            << "chacha_nonce_sha256\t"
            << "chacha_ciphertext_sha256\t"
            << "chacha_roundtrip\t"

            << "aes_key_sha256\t"
            << "aes_nonce_sha256\t"
            << "aes_ciphertext_sha256\t"
            << "aes_roundtrip\n";

        std::cout
            << argv[2] << '\t'
            << argv[3] << '\t'
            << argv[4] << '\t'

            << sha256(material_span) << '\t'
            << stats.zero_bytes << '\t'
            << stats.unique_bytes << '\t'
            << std::setprecision(12)
            << stats.p1 << '\t'

            << sha256(ascon_key) << '\t'
            << sha256(ascon_nonce) << '\t'
            << sha256(ascon_ciphertext) << '\t'
            << (ascon_ok ? 1 : 0) << '\t'

            << sha256(chacha_key) << '\t'
            << sha256(chacha_nonce) << '\t'
            << sha256(chacha_ciphertext) << '\t'
            << (chacha_ok ? 1 : 0) << '\t'

            << sha256(aes_key) << '\t'
            << sha256(aes_nonce) << '\t'
            << sha256(aes_ciphertext) << '\t'
            << (aes_ok ? 1 : 0)
            << '\n';

        return (
            ascon_ok
            && chacha_ok
            && aes_ok
        )
            ? 0
            : 1;
    }
    catch (
        const std::exception& error
    ) {
        std::cerr
            << "ERROR: "
            << error.what()
            << '\n';

        return 1;
    }
}
