#include "bioentropy/sources/DNASequenceSource.hpp"

#include <algorithm>
#include <cctype>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

#include <openssl/evp.h>

namespace bioentropy {

DNASequenceSource::DNASequenceSource(
    DNASequenceConfig config
)
    : config_(std::move(config)) {

    load_and_encode();
    reset();
}

std::string_view
DNASequenceSource::name() const noexcept {
    return "dna_sequence";
}

bool
DNASequenceSource::deterministic() const noexcept {
    return true;
}

void
DNASequenceSource::reset() {
    position_ = 0;
}

std::string
DNASequenceSource::load_sequence(
    const std::string& path
) {
    std::ifstream input(path);

    if (!input) {
        throw std::runtime_error(
            "failed to open DNA sequence file: "
            + path
        );
    }

    std::string sequence;
    char c{};

    while (input.get(c)) {
        if (
            std::isspace(
                static_cast<unsigned char>(c)
            )
        ) {
            continue;
        }

        c = static_cast<char>(
            std::toupper(
                static_cast<unsigned char>(c)
            )
        );

        if (
            c != 'A' &&
            c != 'C' &&
            c != 'G' &&
            c != 'T'
        ) {
            throw std::invalid_argument(
                "DNA sequence contains unsupported "
                "symbol; expected only A/C/G/T"
            );
        }

        sequence.push_back(c);
    }

    if (sequence.empty()) {
        throw std::invalid_argument(
            "DNA sequence is empty"
        );
    }

    return sequence;
}

std::string
DNASequenceSource::sha256_hex(
    std::string_view sequence
) {
    EVP_MD_CTX* context =
        EVP_MD_CTX_new();

    if (context == nullptr) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    unsigned char digest[EVP_MAX_MD_SIZE]{};
    unsigned int digest_length = 0;

    bool success =
        EVP_DigestInit_ex(
            context,
            EVP_sha256(),
            nullptr
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            context,
            sequence.data(),
            sequence.size()
        ) == 1;

    success =
        success &&
        EVP_DigestFinal_ex(
            context,
            digest,
            &digest_length
        ) == 1;

    EVP_MD_CTX_free(context);

    if (
        !success ||
        digest_length != 32
    ) {
        throw std::runtime_error(
            "failed to calculate DNA sequence SHA-256"
        );
    }

    std::ostringstream output;

    output << std::hex
           << std::setfill('0');

    for (
        unsigned int i = 0;
        i < digest_length;
        ++i
    ) {
        output
            << std::setw(2)
            << static_cast<unsigned int>(
                digest[i]
            );
    }

    return output.str();
}

std::uint8_t
DNASequenceSource::nucleotide_value(
    char nucleotide
) {
    switch (nucleotide) {
        case 'A':
            return 0b00;

        case 'C':
            return 0b01;

        case 'G':
            return 0b10;

        case 'T':
            return 0b11;

        default:
            throw std::invalid_argument(
                "invalid DNA nucleotide"
            );
    }
}

void
DNASequenceSource::load_and_encode() {
    const std::string sequence =
        load_sequence(
            config_.sequence_file
        );

    if (
        sequence.size() !=
        config_.window_length_nt
    ) {
        throw std::invalid_argument(
            "DNA sequence length does not match "
            "window_length_nt"
        );
    }

    if (sequence.size() % 4 != 0) {
        throw std::invalid_argument(
            "DNA sequence length must be "
            "divisible by 4 nucleotides"
        );
    }

    if (
        !config_.expected_sequence_sha256.empty()
    ) {
        std::string expected =
            config_.expected_sequence_sha256;

        std::transform(
            expected.begin(),
            expected.end(),
            expected.begin(),
            [](unsigned char c) {
                return static_cast<char>(
                    std::tolower(c)
                );
            }
        );

        const std::string actual =
            sha256_hex(sequence);

        if (actual != expected) {
            throw std::invalid_argument(
                "DNA sequence SHA-256 mismatch"
            );
        }
    }

    encoded_.resize(
        sequence.size() / 4
    );

    for (
        std::size_t i = 0;
        i < encoded_.size();
        ++i
    ) {
        const std::size_t base =
            i * 4;

        std::uint8_t byte = 0;

        byte |= static_cast<std::uint8_t>(
            nucleotide_value(
                sequence[base]
            ) << 6
        );

        byte |= static_cast<std::uint8_t>(
            nucleotide_value(
                sequence[base + 1]
            ) << 4
        );

        byte |= static_cast<std::uint8_t>(
            nucleotide_value(
                sequence[base + 2]
            ) << 2
        );

        byte |= nucleotide_value(
            sequence[base + 3]
        );

        encoded_[i] = byte;
    }
}

void
DNASequenceSource::generate(
    std::span<std::uint8_t> output
) {
    if (output.empty()) {
        return;
    }

    if (
        position_ + output.size() >
        encoded_.size()
    ) {
        throw std::out_of_range(
            "DNA source requested beyond "
            "available sequence window"
        );
    }

    std::memcpy(
        output.data(),
        encoded_.data() + position_,
        output.size()
    );

    position_ += output.size();
}

} // namespace bioentropy
