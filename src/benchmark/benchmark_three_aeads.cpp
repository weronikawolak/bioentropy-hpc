#include "bioentropy/crypto/Aes128Gcm.hpp"
#include "bioentropy/crypto/AsconAead128.hpp"
#include "bioentropy/crypto/ChaCha20Poly1305.hpp"

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;

constexpr std::size_t Samples = 20;
constexpr std::size_t Warmups = 3;

volatile std::uint64_t benchmark_sink = 0;

std::vector<std::uint8_t>
make_plaintext(
    std::size_t size
) {
    std::vector<std::uint8_t> data(size);

    for (
        std::size_t i = 0;
        i < size;
        ++i
    ) {
        data[i] =
            static_cast<std::uint8_t>(
                (i * 37 + 11) & 0xff
            );
    }

    return data;
}

std::vector<std::uint8_t>
make_aad() {
    std::vector<std::uint8_t> data(32);

    for (
        std::size_t i = 0;
        i < data.size();
        ++i
    ) {
        data[i] =
            static_cast<std::uint8_t>(
                (i * 19 + 7) & 0xff
            );
    }

    return data;
}

std::size_t iterations_for(
    std::size_t bytes
) {
    if (bytes <= 64) {
        return 50000;
    }

    if (bytes <= 1024) {
        return 4096;
    }

    if (bytes <= 65536) {
        return 64;
    }

    return 4;
}

double mib_per_second(
    std::size_t bytes,
    double ns_per_op
) {
    if (ns_per_op <= 0.0) {
        return 0.0;
    }

    const double seconds =
        ns_per_op / 1'000'000'000.0;

    const double mib =
        static_cast<double>(bytes)
        / (1024.0 * 1024.0);

    return mib / seconds;
}

void consume(
    const std::vector<std::uint8_t>& data
) {
    std::uint64_t value =
        static_cast<std::uint64_t>(
            data.size()
        );

    if (!data.empty()) {
        value ^=
            static_cast<std::uint64_t>(
                data.front()
            );

        value ^=
            static_cast<std::uint64_t>(
                data.back()
            ) << 8;
    }

    benchmark_sink =
        benchmark_sink ^ value;
}

template <
    typename Encrypt,
    typename Decrypt
>
void benchmark_sample(
    std::ofstream& output,
    const std::string& algorithm,
    std::size_t message_bytes,
    std::size_t sample,
    std::size_t iterations,
    const std::vector<std::uint8_t>& plaintext,
    const std::vector<std::uint8_t>& aad,
    Encrypt&& encrypt,
    Decrypt&& decrypt
) {
    const auto reference =
        encrypt(
            plaintext,
            aad
        );

    const auto recovered =
        decrypt(
            reference,
            aad
        );

    if (
        !recovered.has_value()
        || *recovered != plaintext
    ) {
        throw std::runtime_error(
            algorithm
            + ": pre-benchmark round-trip failed"
        );
    }

    for (
        std::size_t i = 0;
        i < Warmups;
        ++i
    ) {
        const auto encrypted =
            encrypt(
                plaintext,
                aad
            );

        consume(encrypted);

        const auto decrypted =
            decrypt(
                encrypted,
                aad
            );

        if (!decrypted.has_value()) {
            throw std::runtime_error(
                algorithm
                + ": warm-up decrypt failed"
            );
        }

        consume(*decrypted);
    }

    auto start = Clock::now();

    for (
        std::size_t i = 0;
        i < iterations;
        ++i
    ) {
        const auto encrypted =
            encrypt(
                plaintext,
                aad
            );

        consume(encrypted);
    }

    auto stop = Clock::now();

    const double encrypt_ns =
        static_cast<double>(
            std::chrono::duration_cast<
                std::chrono::nanoseconds
            >(
                stop - start
            ).count()
        )
        / static_cast<double>(
            iterations
        );

    start = Clock::now();

    bool decryption_ok = true;

    for (
        std::size_t i = 0;
        i < iterations;
        ++i
    ) {
        const auto decrypted =
            decrypt(
                reference,
                aad
            );

        if (
            !decrypted.has_value()
            || *decrypted != plaintext
        ) {
            decryption_ok = false;
            break;
        }

        consume(*decrypted);
    }

    stop = Clock::now();

    if (!decryption_ok) {
        throw std::runtime_error(
            algorithm
            + ": timed decrypt failed"
        );
    }

    const double decrypt_ns =
        static_cast<double>(
            std::chrono::duration_cast<
                std::chrono::nanoseconds
            >(
                stop - start
            ).count()
        )
        / static_cast<double>(
            iterations
        );

    output
        << algorithm << '\t'
        << message_bytes << '\t'
        << aad.size() << '\t'
        << sample << '\t'
        << iterations << '\t'

        << std::setprecision(15)
        << encrypt_ns << '\t'
        << decrypt_ns << '\t'

        << mib_per_second(
            message_bytes,
            encrypt_ns
        ) << '\t'

        << mib_per_second(
            message_bytes,
            decrypt_ns
        ) << '\t'

        << reference.size() << '\t'
        << (
            reference.size()
            - plaintext.size()
        ) << '\t'

        << 1
        << '\n';
}

} // namespace


int main() {
    try {
        const std::array<
            std::size_t,
            4
        > message_sizes = {
            64,
            1024,
            65536,
            1048576,
        };

        const auto aad =
            make_aad();

        const bioentropy::AsconAead128
            ascon;

        const bioentropy::ChaCha20Poly1305
            chacha;

        const bioentropy::Aes128Gcm
            aes;

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

        for (
            std::size_t i = 0;
            i < ascon_key.size();
            ++i
        ) {
            ascon_key[i] =
                static_cast<std::uint8_t>(i);
        }

        for (
            std::size_t i = 0;
            i < ascon_nonce.size();
            ++i
        ) {
            ascon_nonce[i] =
                static_cast<std::uint8_t>(
                    0xa0 + i
                );
        }

        for (
            std::size_t i = 0;
            i < chacha_key.size();
            ++i
        ) {
            chacha_key[i] =
                static_cast<std::uint8_t>(i);
        }

        for (
            std::size_t i = 0;
            i < chacha_nonce.size();
            ++i
        ) {
            chacha_nonce[i] =
                static_cast<std::uint8_t>(
                    0xb0 + i
                );
        }

        for (
            std::size_t i = 0;
            i < aes_key.size();
            ++i
        ) {
            aes_key[i] =
                static_cast<std::uint8_t>(i);
        }

        for (
            std::size_t i = 0;
            i < aes_nonce.size();
            ++i
        ) {
            aes_nonce[i] =
                static_cast<std::uint8_t>(
                    0xc0 + i
                );
        }

        const std::filesystem::path
            output_path =
                "results/aggregated/"
                "three_aead_benchmark.tsv";

        std::filesystem::create_directories(
            output_path.parent_path()
        );

        std::ofstream output(
            output_path
        );

        if (!output) {
            throw std::runtime_error(
                "cannot create benchmark output"
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
            << "decryption_ok\n";

        for (
            const auto message_bytes
                : message_sizes
        ) {
            const auto plaintext =
                make_plaintext(
                    message_bytes
                );

            const auto iterations =
                iterations_for(
                    message_bytes
                );

            std::cout
                << "\nMessage size: "
                << message_bytes
                << " bytes\n";

            std::cout
                << "Iterations  : "
                << iterations
                << " per sample\n";

            for (
                std::size_t sample = 0;
                sample < Samples;
                ++sample
            ) {
                /*
                 * Rotate benchmark order between samples
                 * to reduce systematic order/thermal bias.
                 */
                const std::size_t rotation =
                    sample % 3;

                for (
                    std::size_t slot = 0;
                    slot < 3;
                    ++slot
                ) {
                    const auto which =
                        (slot + rotation) % 3;

                    if (which == 0) {
                        benchmark_sample(
                            output,
                            "ascon_aead128",
                            message_bytes,
                            sample,
                            iterations,
                            plaintext,
                            aad,

                            [&](
                                const auto& p,
                                const auto& a
                            ) {
                                return ascon.encrypt(
                                    p,
                                    a,
                                    ascon_key,
                                    ascon_nonce
                                );
                            },

                            [&](
                                const auto& c,
                                const auto& a
                            ) {
                                return ascon.decrypt(
                                    c,
                                    a,
                                    ascon_key,
                                    ascon_nonce
                                );
                            }
                        );
                    }
                    else if (which == 1) {
                        benchmark_sample(
                            output,
                            "chacha20_poly1305",
                            message_bytes,
                            sample,
                            iterations,
                            plaintext,
                            aad,

                            [&](
                                const auto& p,
                                const auto& a
                            ) {
                                return chacha.encrypt(
                                    p,
                                    a,
                                    chacha_key,
                                    chacha_nonce
                                );
                            },

                            [&](
                                const auto& c,
                                const auto& a
                            ) {
                                return chacha.decrypt(
                                    c,
                                    a,
                                    chacha_key,
                                    chacha_nonce
                                );
                            }
                        );
                    }
                    else {
                        benchmark_sample(
                            output,
                            "aes128_gcm",
                            message_bytes,
                            sample,
                            iterations,
                            plaintext,
                            aad,

                            [&](
                                const auto& p,
                                const auto& a
                            ) {
                                return aes.encrypt(
                                    p,
                                    a,
                                    aes_key,
                                    aes_nonce
                                );
                            },

                            [&](
                                const auto& c,
                                const auto& a
                            ) {
                                return aes.decrypt(
                                    c,
                                    a,
                                    aes_key,
                                    aes_nonce
                                );
                            }
                        );
                    }
                }

                std::cout
                    << '.'
                    << std::flush;
            }

            std::cout << '\n';
        }

        std::cout
            << "\nBenchmark complete.\n"
            << "Output: "
            << output_path
            << '\n'
            << "Sink: "
            << benchmark_sink
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
