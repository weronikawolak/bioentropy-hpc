#include "bioentropy/crypto/AsconAead128.hpp"
#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using Image =
    std::vector<std::uint8_t>;

using Clock =
    std::chrono::steady_clock;

constexpr std::size_t image_bytes =
    256U * 256U;

constexpr std::size_t warmups = 5U;
constexpr std::size_t repetitions = 31U;

volatile std::uint64_t sink = 0;

Image read_fixture(
    const std::filesystem::path& path
) {
    std::ifstream input(
        path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error(
            "Cannot open fixture: "
            + path.string()
        );
    }

    Image image{
        std::istreambuf_iterator<char>(
            input
        ),
        std::istreambuf_iterator<char>()
    };

    if (image.size() != image_bytes) {
        throw std::runtime_error(
            "Unexpected fixture size: "
            + path.string()
        );
    }

    return image;
}

double median(
    std::vector<double> values
) {
    std::sort(
        values.begin(),
        values.end()
    );

    return values[
        values.size() / 2U
    ];
}

double mib_per_second(
    const double microseconds
) {
    const double seconds =
        microseconds / 1.0e6;

    const double mib =
        static_cast<double>(image_bytes)
        / (1024.0 * 1024.0);

    return mib / seconds;
}

void consume(
    const std::vector<std::uint8_t>& data
) {
    std::uint64_t local = 0;

    for (
        std::size_t i = 0;
        i < data.size();
        i += 4096U
    ) {
        local += data[i];
    }

    sink = sink + local;
}

bioentropy::AsconAead128::Key
make_ascon_key() {
    bioentropy::AsconAead128::Key key{};

    for (
        std::size_t i = 0;
        i < key.size();
        ++i
    ) {
        key[i] =
            static_cast<std::uint8_t>(i);
    }

    return key;
}

bioentropy::AsconAead128::Nonce
make_ascon_nonce(
    const unsigned raw_p,
    const std::size_t sample
) {
    bioentropy::AsconAead128::Nonce nonce{};

    /*
     * Deterministic benchmark-only nonce.
     *
     * Each measured encryption gets a
     * distinct nonce. Nonce generation is
     * outside the timed region.
     */
    for (
        std::size_t i = 0;
        i < nonce.size();
        ++i
    ) {
        nonce[i] =
            static_cast<std::uint8_t>(
                (
                    0xA0U
                    + raw_p * 17U
                    + sample * 29U
                    + i * 13U
                )
                & 0xFFU
            );
    }

    return nonce;
}

bioentropy::FettehaDnaCipher2023::Key
make_fetteha_key() {
    return {
        0xfc, 0x93, 0x22, 0x49,
        0x33, 0x3c, 0x5f, 0xd1,
        0x3b, 0xab, 0xc5, 0x1b,
        0xe9, 0x9e, 0x2e, 0x39,
        0x28, 0x68, 0x27, 0xb5,
        0x33, 0x00, 0xcc, 0xa7,
        0x38, 0x22, 0x7f, 0x90,
        0x9b, 0xe8, 0x5b, 0xda
    };
}

struct TimingResult {
    double encrypt_us{};
    double decrypt_us{};
};

TimingResult benchmark_ascon_once(
    const bioentropy::AsconAead128& aead,
    const Image& image,
    const bioentropy::AsconAead128::Key& key,
    const bioentropy::AsconAead128::Nonce& nonce
) {
    const auto start_encrypt =
        Clock::now();

    const auto ciphertext =
        aead.encrypt(
            image,
            {},
            key,
            nonce
        );

    const auto end_encrypt =
        Clock::now();

    consume(ciphertext);

    const auto start_decrypt =
        Clock::now();

    const auto recovered =
        aead.decrypt(
            ciphertext,
            {},
            key,
            nonce
        );

    const auto end_decrypt =
        Clock::now();

    if (
        !recovered.has_value()
        || *recovered != image
    ) {
        throw std::runtime_error(
            "Ascon round-trip failed"
        );
    }

    consume(*recovered);

    return {
        std::chrono::duration<
            double,
            std::micro
        >(
            end_encrypt
            - start_encrypt
        ).count(),

        std::chrono::duration<
            double,
            std::micro
        >(
            end_decrypt
            - start_decrypt
        ).count()
    };
}

TimingResult benchmark_fetteha_once(
    const Image& image,
    const bioentropy::
        FettehaDnaCipher2023::Key& key
) {
    const auto start_encrypt =
        Clock::now();

    const auto encrypted =
        bioentropy::
            FettehaDnaCipher2023::
                encrypt(
                    image,
                    key
                );

    const auto end_encrypt =
        Clock::now();

    consume(
        encrypted.ciphertext
    );

    const auto start_decrypt =
        Clock::now();

    const auto recovered =
        bioentropy::
            FettehaDnaCipher2023::
                decrypt(
                    encrypted.ciphertext,
                    key,
                    encrypted.p
                );

    const auto end_decrypt =
        Clock::now();

    if (recovered != image) {
        throw std::runtime_error(
            "Fetteha round-trip failed"
        );
    }

    consume(recovered);

    return {
        std::chrono::duration<
            double,
            std::micro
        >(
            end_encrypt
            - start_encrypt
        ).count(),

        std::chrono::duration<
            double,
            std::micro
        >(
            end_decrypt
            - start_decrypt
        ).count()
    };
}

}  // namespace

int main() {
    const bioentropy::AsconAead128
        ascon;

    const auto ascon_key =
        make_ascon_key();

    const auto fetteha_key =
        make_fetteha_key();

    /*
     * Representative Fetteha execution
     * costs:
     *
     * P=1  -> minimum
     * P=8  -> middle
     * P=0  -> 16 effective passes
     */
    const std::vector<unsigned>
        raw_p_values{
            1U,
            8U,
            0U
        };

    std::filesystem::create_directories(
        "results/aggregated"
    );

    const std::filesystem::path output_path =
        "results/aggregated/"
        "ascon_vs_fetteha_64k.tsv";

    std::ofstream output(
        output_path
    );

    if (!output) {
        throw std::runtime_error(
            "Cannot open benchmark output"
        );
    }

    output
        << "raw_p\t"
        << "effective_passes\t"
        << "message_bytes\t"
        << "repetitions\t"
        << "ascon_ciphertext_bytes\t"
        << "fetteha_ciphertext_bytes\t"
        << "ascon_encrypt_median_us\t"
        << "ascon_decrypt_median_us\t"
        << "fetteha_encrypt_median_us\t"
        << "fetteha_decrypt_median_us\t"
        << "ascon_encrypt_mib_s\t"
        << "ascon_decrypt_mib_s\t"
        << "fetteha_encrypt_mib_s\t"
        << "fetteha_decrypt_mib_s\t"
        << "fetteha_encrypt_slowdown\t"
        << "fetteha_decrypt_slowdown\n";

    output << std::setprecision(12);

    for (
        const unsigned raw_p :
        raw_p_values
    ) {
        const std::string number =
            raw_p < 10U
                ? "0"
                    + std::to_string(raw_p)
                : std::to_string(raw_p);

        const auto fixture_path =
            std::filesystem::path(
                "results/generated/"
                "fetteha_p_fixtures"
            )
            / (
                "p_"
                + number
                + ".bin"
            );

        const Image image =
            read_fixture(
                fixture_path
            );

        const auto observed_p =
            bioentropy::
                FettehaDnaCipher2023::
                    iteration_count(
                        image
                    );

        if (observed_p != raw_p) {
            throw std::runtime_error(
                "Fixture P mismatch"
            );
        }

        const auto effective_passes =
            bioentropy::
                FettehaDnaCipher2023::
                    effective_pass_count(
                        observed_p
                    );

        /*
         * Warm-up both implementations.
         */
        for (
            std::size_t i = 0;
            i < warmups;
            ++i
        ) {
            const auto nonce =
                make_ascon_nonce(
                    raw_p,
                    1000U + i
                );

            static_cast<void>(
                benchmark_ascon_once(
                    ascon,
                    image,
                    ascon_key,
                    nonce
                )
            );

            static_cast<void>(
                benchmark_fetteha_once(
                    image,
                    fetteha_key
                )
            );
        }

        std::vector<double>
            ascon_encrypt;

        std::vector<double>
            ascon_decrypt;

        std::vector<double>
            fetteha_encrypt;

        std::vector<double>
            fetteha_decrypt;

        ascon_encrypt.reserve(
            repetitions
        );

        ascon_decrypt.reserve(
            repetitions
        );

        fetteha_encrypt.reserve(
            repetitions
        );

        fetteha_decrypt.reserve(
            repetitions
        );

        for (
            std::size_t rep = 0;
            rep < repetitions;
            ++rep
        ) {
            const auto nonce =
                make_ascon_nonce(
                    raw_p,
                    rep
                );

            TimingResult ascon_result{};
            TimingResult fetteha_result{};

            /*
             * Alternate benchmark order
             * to reduce systematic thermal /
             * cache ordering bias.
             */
            if (rep % 2U == 0U) {
                ascon_result =
                    benchmark_ascon_once(
                        ascon,
                        image,
                        ascon_key,
                        nonce
                    );

                fetteha_result =
                    benchmark_fetteha_once(
                        image,
                        fetteha_key
                    );
            } else {
                fetteha_result =
                    benchmark_fetteha_once(
                        image,
                        fetteha_key
                    );

                ascon_result =
                    benchmark_ascon_once(
                        ascon,
                        image,
                        ascon_key,
                        nonce
                    );
            }

            ascon_encrypt.push_back(
                ascon_result.encrypt_us
            );

            ascon_decrypt.push_back(
                ascon_result.decrypt_us
            );

            fetteha_encrypt.push_back(
                fetteha_result.encrypt_us
            );

            fetteha_decrypt.push_back(
                fetteha_result.decrypt_us
            );
        }

        const double ascon_enc_us =
            median(ascon_encrypt);

        const double ascon_dec_us =
            median(ascon_decrypt);

        const double fetteha_enc_us =
            median(fetteha_encrypt);

        const double fetteha_dec_us =
            median(fetteha_decrypt);

        /*
         * Verify output-size difference.
         *
         * Ascon carries its authentication
         * tag in the returned ciphertext.
         */
        const auto verification_nonce =
            make_ascon_nonce(
                raw_p,
                999999U
            );

        const auto ascon_ciphertext =
            ascon.encrypt(
                image,
                {},
                ascon_key,
                verification_nonce
            );

        const auto fetteha_ciphertext =
            bioentropy::
                FettehaDnaCipher2023::
                    encrypt(
                        image,
                        fetteha_key
                    );

        output
            << raw_p << '\t'
            << static_cast<unsigned>(
                effective_passes
            ) << '\t'
            << image.size() << '\t'
            << repetitions << '\t'
            << ascon_ciphertext.size()
            << '\t'
            << fetteha_ciphertext
                .ciphertext.size()
            << '\t'
            << ascon_enc_us << '\t'
            << ascon_dec_us << '\t'
            << fetteha_enc_us << '\t'
            << fetteha_dec_us << '\t'
            << mib_per_second(
                ascon_enc_us
            ) << '\t'
            << mib_per_second(
                ascon_dec_us
            ) << '\t'
            << mib_per_second(
                fetteha_enc_us
            ) << '\t'
            << mib_per_second(
                fetteha_dec_us
            ) << '\t'
            << (
                fetteha_enc_us
                / ascon_enc_us
            ) << '\t'
            << (
                fetteha_dec_us
                / ascon_dec_us
            ) << '\n';

        std::cout
            << "P="
            << raw_p
            << " effective="
            << static_cast<unsigned>(
                effective_passes
            )
            << "\n"
            << "  Ascon enc   : "
            << ascon_enc_us
            << " us\n"
            << "  Fetteha enc: "
            << fetteha_enc_us
            << " us\n"
            << "  slowdown   : "
            << (
                fetteha_enc_us
                / ascon_enc_us
            )
            << "x\n";
    }

    std::cout
        << "\nCommon benchmark complete\n"
        << output_path.string()
        << "\n"
        << "sink="
        << sink
        << '\n';

    return 0;
}
