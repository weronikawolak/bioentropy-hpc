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
#include <numeric>
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

    const std::size_t middle =
        values.size() / 2U;

    if (values.size() % 2U != 0U) {
        return values[middle];
    }

    return (
        values[middle - 1U]
        + values[middle]
    ) / 2.0;
}

double throughput_mib_s(
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
    const Image& data
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

}  // namespace

int main() {
    using bioentropy::
        FettehaDnaCipher2023;

    const FettehaDnaCipher2023::Key key{
        0xfc, 0x93, 0x22, 0x49,
        0x33, 0x3c, 0x5f, 0xd1,
        0x3b, 0xab, 0xc5, 0x1b,
        0xe9, 0x9e, 0x2e, 0x39,
        0x28, 0x68, 0x27, 0xb5,
        0x33, 0x00, 0xcc, 0xa7,
        0x38, 0x22, 0x7f, 0x90,
        0x9b, 0xe8, 0x5b, 0xda
    };

    std::filesystem::create_directories(
        "results/aggregated"
    );

    std::ofstream output(
        "results/aggregated/"
        "fetteha_p_performance.tsv"
    );

    if (!output) {
        std::cerr
            << "Cannot open benchmark output\n";

        return 1;
    }

    output
        << "raw_p\t"
        << "effective_passes\t"
        << "image_bytes\t"
        << "repetitions\t"
        << "encrypt_median_us\t"
        << "decrypt_median_us\t"
        << "encrypt_mib_s\t"
        << "decrypt_mib_s\t"
        << "encrypt_amortized_us_per_pass\t"
        << "decrypt_amortized_us_per_pass\n";

    output << std::setprecision(12);

    for (
        unsigned raw_p = 0U;
        raw_p <= 15U;
        ++raw_p
    ) {
        const std::string number =
            raw_p < 10U
                ? "0" + std::to_string(raw_p)
                : std::to_string(raw_p);

        const auto path =
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
            read_fixture(path);

        const auto observed_p =
            FettehaDnaCipher2023::
                iteration_count(image);

        if (observed_p != raw_p) {
            throw std::runtime_error(
                "Fixture P mismatch"
            );
        }

        const auto effective_passes =
            FettehaDnaCipher2023::
                effective_pass_count(
                    observed_p
                );

        /*
         * Warm-up.
         */
        for (
            std::size_t i = 0;
            i < warmups;
            ++i
        ) {
            const auto encrypted =
                FettehaDnaCipher2023::
                    encrypt(
                        image,
                        key
                    );

            const auto decrypted =
                FettehaDnaCipher2023::
                    decrypt(
                        encrypted.ciphertext,
                        key,
                        encrypted.p
                    );

            if (decrypted != image) {
                throw std::runtime_error(
                    "Warm-up round-trip failed"
                );
            }

            consume(
                encrypted.ciphertext
            );
        }

        std::vector<double>
            encryption_times;

        std::vector<double>
            decryption_times;

        encryption_times.reserve(
            repetitions
        );

        decryption_times.reserve(
            repetitions
        );

        for (
            std::size_t rep = 0;
            rep < repetitions;
            ++rep
        ) {
            const auto encrypt_start =
                Clock::now();

            const auto encrypted =
                FettehaDnaCipher2023::
                    encrypt(
                        image,
                        key
                    );

            const auto encrypt_end =
                Clock::now();

            consume(
                encrypted.ciphertext
            );

            const auto decrypt_start =
                Clock::now();

            const auto decrypted =
                FettehaDnaCipher2023::
                    decrypt(
                        encrypted.ciphertext,
                        key,
                        encrypted.p
                    );

            const auto decrypt_end =
                Clock::now();

            if (decrypted != image) {
                throw std::runtime_error(
                    "Benchmark round-trip failed"
                );
            }

            consume(decrypted);

            const double encrypt_us =
                std::chrono::duration<
                    double,
                    std::micro
                >(
                    encrypt_end
                    - encrypt_start
                ).count();

            const double decrypt_us =
                std::chrono::duration<
                    double,
                    std::micro
                >(
                    decrypt_end
                    - decrypt_start
                ).count();

            encryption_times.push_back(
                encrypt_us
            );

            decryption_times.push_back(
                decrypt_us
            );
        }

        const double enc_median =
            median(encryption_times);

        const double dec_median =
            median(decryption_times);

        output
            << raw_p << '\t'
            << static_cast<unsigned>(
                effective_passes
            ) << '\t'
            << image_bytes << '\t'
            << repetitions << '\t'
            << enc_median << '\t'
            << dec_median << '\t'
            << throughput_mib_s(
                enc_median
            ) << '\t'
            << throughput_mib_s(
                dec_median
            ) << '\t'
            << (
                enc_median
                / static_cast<double>(
                    effective_passes
                )
            ) << '\t'
            << (
                dec_median
                / static_cast<double>(
                    effective_passes
                )
            ) << '\n';

        std::cout
            << "P="
            << raw_p
            << " effective="
            << static_cast<unsigned>(
                effective_passes
            )
            << " enc="
            << enc_median
            << " us dec="
            << dec_median
            << " us\n";
    }

    std::cout
        << "Fetteha P-performance benchmark complete\n"
        << "results/aggregated/"
        << "fetteha_p_performance.tsv\n"
        << "sink="
        << sink
        << '\n';

    return 0;
}
