#include "bioentropy/crypto/AsconAead128.hpp"
#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <span>
#include <stdexcept>
#include <vector>

namespace {

using Clock =
    std::chrono::steady_clock;

constexpr std::size_t Samples = 20;
constexpr std::size_t AssociatedDataBytes = 32;
constexpr std::size_t TargetBytesPerSample =
    4ULL * 1024ULL * 1024ULL;

std::vector<std::uint8_t> make_plaintext(
    const std::size_t size
) {
    std::vector<std::uint8_t> data(size);

    for (std::size_t i = 0; i < size; ++i) {
        data[i] =
            static_cast<std::uint8_t>(
                (
                    i * 131ULL
                    + (i >> 3U)
                    + 17ULL
                )
                & 0xffULL
            );
    }

    return data;
}

std::vector<std::uint8_t>
make_associated_data() {
    std::vector<std::uint8_t> data(
        AssociatedDataBytes
    );

    for (std::size_t i = 0; i < data.size(); ++i) {
        data[i] =
            static_cast<std::uint8_t>(
                0x40U + i
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
make_nonce(
    const std::uint64_t sample
) {
    bioentropy::AsconAead128::Nonce nonce{};

    for (std::size_t i = 0; i < 8; ++i) {
        nonce[i] =
            static_cast<std::uint8_t>(
                0xa0U + i
            );
    }

    for (std::size_t i = 0; i < 8; ++i) {
        nonce[8 + i] =
            static_cast<std::uint8_t>(
                (sample >> (8U * i))
                & 0xffU
            );
    }

    return nonce;
}

std::size_t iterations_for(
    const std::size_t message_bytes
) {
    std::size_t iterations =
        TargetBytesPerSample
        / message_bytes;

    if (iterations < 4) {
        iterations = 4;
    }

    if (iterations > 50'000) {
        iterations = 50'000;
    }

    return iterations;
}

double byte_shannon_entropy(
    std::span<const std::uint8_t> data
) {
    if (data.empty()) {
        return 0.0;
    }

    std::array<std::uint64_t, 256>
        counts{};

    for (const auto byte : data) {
        ++counts[byte];
    }

    const double n =
        static_cast<double>(
            data.size()
        );

    double entropy = 0.0;

    for (const auto count : counts) {
        if (count == 0) {
            continue;
        }

        const double p =
            static_cast<double>(count)
            / n;

        entropy -=
            p * std::log2(p);
    }

    return entropy;
}

double plaintext_ciphertext_correlation(
    std::span<const std::uint8_t> plaintext,
    std::span<const std::uint8_t> ciphertext
) {
    if (
        plaintext.empty()
        || ciphertext.size()
           < plaintext.size()
    ) {
        return 0.0;
    }

    const std::size_t n =
        plaintext.size();

    long double mean_x = 0.0L;
    long double mean_y = 0.0L;

    for (std::size_t i = 0; i < n; ++i) {
        mean_x += plaintext[i];
        mean_y += ciphertext[i];
    }

    mean_x /= static_cast<long double>(n);
    mean_y /= static_cast<long double>(n);

    long double covariance = 0.0L;
    long double variance_x = 0.0L;
    long double variance_y = 0.0L;

    for (std::size_t i = 0; i < n; ++i) {
        const long double dx =
            static_cast<long double>(
                plaintext[i]
            )
            - mean_x;

        const long double dy =
            static_cast<long double>(
                ciphertext[i]
            )
            - mean_y;

        covariance += dx * dy;
        variance_x += dx * dx;
        variance_y += dy * dy;
    }

    if (
        variance_x == 0.0L
        || variance_y == 0.0L
    ) {
        return 0.0;
    }

    return static_cast<double>(
        covariance
        / std::sqrt(
            variance_x
            * variance_y
        )
    );
}

double mib_per_second(
    const std::size_t bytes,
    const double seconds
) {
    if (seconds <= 0.0) {
        return 0.0;
    }

    return (
        static_cast<double>(bytes)
        / (1024.0 * 1024.0)
    ) / seconds;
}

}  // namespace

int main() {
    const std::array<std::size_t, 4>
        message_sizes{
            64,
            1024,
            64 * 1024,
            1024 * 1024
        };

    const bioentropy::AsconAead128 aead;

    const auto key =
        make_key();

    const auto associated_data =
        make_associated_data();

    const std::filesystem::path output_path =
        "results/aggregated/"
        "ascon_aead128_benchmark.tsv";

    std::filesystem::create_directories(
        output_path.parent_path()
    );

    std::ofstream output(output_path);

    if (!output) {
        throw std::runtime_error(
            "cannot open benchmark output"
        );
    }

    output
        << "algorithm\t"
        << "message_bytes\t"
        << "associated_data_bytes\t"
        << "sample\t"
        << "iterations\t"
        << "encrypt_ns_per_op\t"
        << "decrypt_ns_per_op\t"
        << "encrypt_mib_per_s\t"
        << "decrypt_mib_per_s\t"
        << "ciphertext_bytes\t"
        << "expansion_bytes\t"
        << "expansion_percent\t"
        << "ciphertext_bit_shannon\t"
        << "ciphertext_byte_shannon\t"
        << "plaintext_ciphertext_correlation\t"
        << "decryption_ok\n";

    std::cout
        << "Ascon-AEAD128 benchmark\n"
        << "=======================\n";

    for (
        const auto message_bytes :
        message_sizes
    ) {
        const auto plaintext =
            make_plaintext(
                message_bytes
            );

        const std::size_t iterations =
            iterations_for(
                message_bytes
            );

        std::cout
            << "\nMessage size : "
            << message_bytes
            << " bytes\n"
            << "Iterations   : "
            << iterations
            << " per sample\n";

        for (
            std::size_t sample = 0;
            sample < Samples;
            ++sample
        ) {
            const auto nonce =
                make_nonce(sample);

            /*
             * Warm-up.
             */
            auto ciphertext =
                aead.encrypt(
                    plaintext,
                    associated_data,
                    key,
                    nonce
                );

            auto recovered =
                aead.decrypt(
                    ciphertext,
                    associated_data,
                    key,
                    nonce
                );

            if (
                !recovered.has_value()
                || *recovered != plaintext
            ) {
                throw std::runtime_error(
                    "warm-up decryption failed"
                );
            }

            /*
             * Encryption timing.
             */
            const auto encrypt_start =
                Clock::now();

            for (
                std::size_t i = 0;
                i < iterations;
                ++i
            ) {
                ciphertext =
                    aead.encrypt(
                        plaintext,
                        associated_data,
                        key,
                        nonce
                    );
            }

            const auto encrypt_end =
                Clock::now();

            /*
             * Decryption timing.
             */
            const auto decrypt_start =
                Clock::now();

            for (
                std::size_t i = 0;
                i < iterations;
                ++i
            ) {
                recovered =
                    aead.decrypt(
                        ciphertext,
                        associated_data,
                        key,
                        nonce
                    );

                if (!recovered.has_value()) {
                    throw std::runtime_error(
                        "benchmark decryption failed"
                    );
                }
            }

            const auto decrypt_end =
                Clock::now();

            if (*recovered != plaintext) {
                throw std::runtime_error(
                    "recovered plaintext mismatch"
                );
            }

            const double encrypt_seconds =
                std::chrono::duration<double>(
                    encrypt_end
                    - encrypt_start
                ).count();

            const double decrypt_seconds =
                std::chrono::duration<double>(
                    decrypt_end
                    - decrypt_start
                ).count();

            const double encrypt_seconds_op =
                encrypt_seconds
                / static_cast<double>(
                    iterations
                );

            const double decrypt_seconds_op =
                decrypt_seconds
                / static_cast<double>(
                    iterations
                );

            const double encrypt_ns =
                encrypt_seconds_op
                * 1.0e9;

            const double decrypt_ns =
                decrypt_seconds_op
                * 1.0e9;

            bioentropy::
                BitstreamStatisticsAccumulator
                    accumulator;

            accumulator.update(
                std::span<
                    const std::uint8_t
                >(
                    ciphertext.data(),
                    ciphertext.size()
                )
            );

            const auto statistics =
                accumulator.finalize();

            const double byte_entropy =
                byte_shannon_entropy(
                    ciphertext
                );

            const double correlation =
                plaintext_ciphertext_correlation(
                    plaintext,
                    ciphertext
                );

            const std::size_t expansion =
                ciphertext.size()
                - plaintext.size();

            const double expansion_percent =
                100.0
                * static_cast<double>(
                    expansion
                )
                / static_cast<double>(
                    plaintext.size()
                );

            output
                << std::setprecision(17)
                << "ascon_aead128\t"
                << message_bytes
                << '\t'
                << associated_data.size()
                << '\t'
                << sample
                << '\t'
                << iterations
                << '\t'
                << encrypt_ns
                << '\t'
                << decrypt_ns
                << '\t'
                << mib_per_second(
                    message_bytes,
                    encrypt_seconds_op
                )
                << '\t'
                << mib_per_second(
                    message_bytes,
                    decrypt_seconds_op
                )
                << '\t'
                << ciphertext.size()
                << '\t'
                << expansion
                << '\t'
                << expansion_percent
                << '\t'
                << statistics.shannon_entropy
                << '\t'
                << byte_entropy
                << '\t'
                << correlation
                << '\t'
                << "true\n";

            std::cout
                << "  sample "
                << std::setw(2)
                << sample + 1
                << "/"
                << Samples
                << "\r"
                << std::flush;
        }

        std::cout
            << "  samples complete       \n";
    }

    std::cout
        << "\nBenchmark complete.\n"
        << "Output: "
        << output_path
        << '\n';

    return 0;
}
