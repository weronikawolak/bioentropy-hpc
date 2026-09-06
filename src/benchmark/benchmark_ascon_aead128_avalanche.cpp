#include "bioentropy/crypto/AsconAead128.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

constexpr std::size_t Trials = 100;
constexpr std::size_t AssociatedDataBytes = 32;

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
make_nonce() {
    bioentropy::AsconAead128::Nonce nonce{};

    for (std::size_t i = 0; i < nonce.size(); ++i) {
        nonce[i] =
            static_cast<std::uint8_t>(
                0xa0U + i
            );
    }

    return nonce;
}

std::uint64_t hamming_bits(
    const std::uint8_t* first,
    const std::uint8_t* second,
    const std::size_t size
) {
    std::uint64_t distance = 0;

    for (std::size_t i = 0; i < size; ++i) {
        distance +=
            static_cast<std::uint64_t>(
                std::popcount(
                    static_cast<unsigned>(
                        first[i] ^ second[i]
                    )
                )
            );
    }

    return distance;
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

    const auto nonce =
        make_nonce();

    const auto associated_data =
        make_associated_data();

    const std::filesystem::path output_path =
        "results/aggregated/"
        "ascon_aead128_avalanche.tsv";

    std::filesystem::create_directories(
        output_path.parent_path()
    );

    std::ofstream output(output_path);

    if (!output) {
        throw std::runtime_error(
            "cannot open avalanche output"
        );
    }

    output
        << "algorithm\t"
        << "message_bytes\t"
        << "trial\t"
        << "flipped_bit\t"
        << "ciphertext_changed_bits\t"
        << "ciphertext_total_bits\t"
        << "ciphertext_change_percent\t"
        << "payload_changed_bits\t"
        << "payload_total_bits\t"
        << "payload_change_percent\t"
        << "tag_changed_bits\t"
        << "tag_total_bits\t"
        << "tag_change_percent\n";

    std::cout
        << "Ascon-AEAD128 avalanche benchmark\n"
        << "=================================\n";

    for (
        const auto message_bytes :
        message_sizes
    ) {
        const auto original_plaintext =
            make_plaintext(
                message_bytes
            );

        const auto baseline =
            aead.encrypt(
                original_plaintext,
                associated_data,
                key,
                nonce
            );

        if (
            baseline.size()
            != message_bytes
               + bioentropy::
                 AsconAead128::TagBytes
        ) {
            throw std::runtime_error(
                "unexpected ciphertext size"
            );
        }

        const std::size_t plaintext_bits =
            message_bytes * 8;

        const std::size_t payload_bytes =
            message_bytes;

        const std::size_t tag_offset =
            payload_bytes;

        std::cout
            << "\nMessage size: "
            << message_bytes
            << " bytes\n";

        for (
            std::size_t trial = 0;
            trial < Trials;
            ++trial
        ) {
            /*
             * Deterministically spread flipped bits
             * across the entire plaintext.
             */
            const std::size_t bit_index =
                (
                    trial
                    * plaintext_bits
                )
                / Trials;

            const std::size_t byte_index =
                bit_index / 8;

            const std::size_t bit_in_byte =
                bit_index % 8;

            auto modified_plaintext =
                original_plaintext;

            modified_plaintext[
                byte_index
            ] ^= static_cast<std::uint8_t>(
                1U << bit_in_byte
            );

            const auto modified =
                aead.encrypt(
                    modified_plaintext,
                    associated_data,
                    key,
                    nonce
                );

            if (
                modified.size()
                != baseline.size()
            ) {
                throw std::runtime_error(
                    "ciphertext size changed"
                );
            }

            const auto payload_changed =
                hamming_bits(
                    baseline.data(),
                    modified.data(),
                    payload_bytes
                );

            const auto tag_changed =
                hamming_bits(
                    baseline.data()
                        + tag_offset,
                    modified.data()
                        + tag_offset,
                    bioentropy::
                        AsconAead128::TagBytes
                );

            const auto total_changed =
                payload_changed
                + tag_changed;

            const std::uint64_t
                payload_total_bits =
                    static_cast<std::uint64_t>(
                        payload_bytes
                    ) * 8ULL;

            const std::uint64_t
                tag_total_bits =
                    bioentropy::
                        AsconAead128::TagBytes
                    * 8ULL;

            const std::uint64_t
                total_bits =
                    payload_total_bits
                    + tag_total_bits;

            const double payload_percent =
                100.0
                * static_cast<double>(
                    payload_changed
                )
                / static_cast<double>(
                    payload_total_bits
                );

            const double tag_percent =
                100.0
                * static_cast<double>(
                    tag_changed
                )
                / static_cast<double>(
                    tag_total_bits
                );

            const double total_percent =
                100.0
                * static_cast<double>(
                    total_changed
                )
                / static_cast<double>(
                    total_bits
                );

            output
                << std::setprecision(17)
                << "ascon_aead128\t"
                << message_bytes
                << '\t'
                << trial
                << '\t'
                << bit_index
                << '\t'
                << total_changed
                << '\t'
                << total_bits
                << '\t'
                << total_percent
                << '\t'
                << payload_changed
                << '\t'
                << payload_total_bits
                << '\t'
                << payload_percent
                << '\t'
                << tag_changed
                << '\t'
                << tag_total_bits
                << '\t'
                << tag_percent
                << '\n';
        }

        std::cout
            << "  "
            << Trials
            << " one-bit trials complete\n";
    }

    std::cout
        << "\nAvalanche benchmark complete.\n"
        << "Output: "
        << output_path
        << '\n';

    return 0;
}
