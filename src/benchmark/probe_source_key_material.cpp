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
#include <set>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr std::size_t MaterialBytes = 76;

std::vector<std::uint8_t>
read_material(
    const std::string& path
) {
    std::ifstream input(
        path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error(
            "cannot open material file: "
            + path
        );
    }

    std::vector<std::uint8_t>
        data(
            (
                std::istreambuf_iterator<char>(
                    input
                )
            ),
            std::istreambuf_iterator<char>()
        );

    if (
        data.size()
        != MaterialBytes
    ) {
        throw std::runtime_error(
            "expected exactly 76 material bytes, got "
            + std::to_string(
                data.size()
            )
        );
    }

    return data;
}

std::string sha256_hex(
    std::span<const std::uint8_t> data
) {
    EVP_MD_CTX* context =
        EVP_MD_CTX_new();

    if (context == nullptr) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    std::array<
        unsigned char,
        EVP_MAX_MD_SIZE
    > digest{};

    unsigned int digest_length = 0;

    const bool ok =
        EVP_DigestInit_ex(
            context,
            EVP_sha256(),
            nullptr
        ) == 1
        &&
        EVP_DigestUpdate(
            context,
            data.data(),
            data.size()
        ) == 1
        &&
        EVP_DigestFinal_ex(
            context,
            digest.data(),
            &digest_length
        ) == 1;

    EVP_MD_CTX_free(context);

    if (!ok) {
        throw std::runtime_error(
            "SHA-256 calculation failed"
        );
    }

    std::ostringstream result;

    result
        << std::hex
        << std::setfill('0');

    for (
        unsigned int i = 0;
        i < digest_length;
        ++i
    ) {
        result
            << std::setw(2)
            << static_cast<unsigned int>(
                digest[i]
            );
    }

    return result.str();
}

template <
    std::size_t N
>
std::array<std::uint8_t, N>
extract(
    const std::vector<std::uint8_t>& data,
    std::size_t offset
) {
    if (
        offset + N
        > data.size()
    ) {
        throw std::runtime_error(
            "material extraction overflow"
        );
    }

    std::array<std::uint8_t, N>
        result{};

    std::copy_n(
        data.begin()
            + static_cast<
                std::ptrdiff_t
            >(offset),
        N,
        result.begin()
    );

    return result;
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
                (
                    i * 37U
                    + 11U
                )
                & 0xffU
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
                (
                    i * 19U
                    + 7U
                )
                & 0xffU
            );
    }

    return aad;
}

} // namespace

int main(
    int argc,
    char* argv[]
) {
    if (argc != 5) {
        std::cerr
            << "Usage:\n"
            << argv[0]
            << " <material.bin>"
            << " <source>"
            << " <replicate_id>"
            << " <mode>\n";

        return 2;
    }

    try {
        const std::string material_path =
            argv[1];

        const std::string source =
            argv[2];

        const std::string replicate_id =
            argv[3];

        const std::string mode =
            argv[4];

        const auto material =
            read_material(
                material_path
            );

        const auto ascon_key =
            extract<
                bioentropy::
                AsconAead128::
                KeyBytes
            >(
                material,
                0
            );

        const auto ascon_nonce =
            extract<
                bioentropy::
                AsconAead128::
                NonceBytes
            >(
                material,
                16
            );

        const auto chacha_key =
            extract<
                bioentropy::
                ChaCha20Poly1305::
                KeyBytes
            >(
                material,
                32
            );

        const auto chacha_nonce =
            extract<
                bioentropy::
                ChaCha20Poly1305::
                NonceBytes
            >(
                material,
                64
            );

        const auto plaintext =
            make_plaintext();

        const auto aad =
            make_aad();

        const bioentropy::
            AsconAead128
                ascon;

        const auto ascon_ciphertext =
            ascon.encrypt(
                plaintext,
                aad,
                ascon_key,
                ascon_nonce
            );

        const auto ascon_recovered =
            ascon.decrypt(
                ascon_ciphertext,
                aad,
                ascon_key,
                ascon_nonce
            );

        const bool ascon_ok =
            ascon_recovered.has_value()
            &&
            *ascon_recovered
                == plaintext;

        const bioentropy::
            ChaCha20Poly1305
                chacha;

        const auto chacha_ciphertext =
            chacha.encrypt(
                plaintext,
                aad,
                chacha_key,
                chacha_nonce
            );

        const auto chacha_recovered =
            chacha.decrypt(
                chacha_ciphertext,
                aad,
                chacha_key,
                chacha_nonce
            );

        const bool chacha_ok =
            chacha_recovered.has_value()
            &&
            *chacha_recovered
                == plaintext;

        if (
            !ascon_ok
            || !chacha_ok
        ) {
            throw std::runtime_error(
                "AEAD round-trip failed"
            );
        }

        std::size_t zero_bytes = 0;
        std::uint64_t ones = 0;

        std::set<std::uint8_t>
            unique_bytes;

        for (
            const auto byte :
            material
        ) {
            if (byte == 0) {
                ++zero_bytes;
            }

            ones +=
                static_cast<std::uint64_t>(
                    std::popcount(
                        static_cast<
                            unsigned int
                        >(byte)
                    )
                );

            unique_bytes.insert(
                byte
            );
        }

        const double p1 =
            static_cast<double>(
                ones
            )
            /
            static_cast<double>(
                material.size()
                * 8U
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
            << "chacha_roundtrip\n";

        std::cout
            << source << '\t'
            << replicate_id << '\t'
            << mode << '\t'
            << sha256_hex(material) << '\t'
            << zero_bytes << '\t'
            << unique_bytes.size() << '\t'
            << std::setprecision(17)
            << p1 << '\t'
            << sha256_hex(ascon_key) << '\t'
            << sha256_hex(ascon_nonce) << '\t'
            << sha256_hex(
                ascon_ciphertext
            ) << '\t'
            << (ascon_ok ? 1 : 0)
            << '\t'
            << sha256_hex(chacha_key) << '\t'
            << sha256_hex(
                chacha_nonce
            ) << '\t'
            << sha256_hex(
                chacha_ciphertext
            ) << '\t'
            << (chacha_ok ? 1 : 0)
            << '\n';

        return 0;
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
