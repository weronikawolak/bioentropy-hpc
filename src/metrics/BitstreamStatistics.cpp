#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace bioentropy {

namespace {

double entropy_component(double probability) {
    if (probability <= 0.0) {
        return 0.0;
    }

    return -probability * std::log2(probability);
}

std::string bytes_to_hex(
    const std::uint8_t* data,
    std::size_t size
) {
    std::ostringstream stream;

    stream
        << std::hex
        << std::setfill('0');

    for (std::size_t i = 0; i < size; ++i) {
        stream
            << std::setw(2)
            << static_cast<unsigned int>(data[i]);
    }

    return stream.str();
}

} // namespace

BitstreamStatisticsAccumulator::
BitstreamStatisticsAccumulator() {
    digest_context_ =
        EVP_MD_CTX_new();

    if (digest_context_ == nullptr) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    if (
        EVP_DigestInit_ex(
            digest_context_,
            EVP_sha256(),
            nullptr
        ) != 1
    ) {
        EVP_MD_CTX_free(digest_context_);
        digest_context_ = nullptr;

        throw std::runtime_error(
            "EVP_DigestInit_ex failed"
        );
    }
}

BitstreamStatisticsAccumulator::
~BitstreamStatisticsAccumulator() {
    if (digest_context_ != nullptr) {
        EVP_MD_CTX_free(digest_context_);
    }
}

void BitstreamStatisticsAccumulator::update(
    std::span<const std::uint8_t> data
) {
    if (finalized_) {
        throw std::logic_error(
            "cannot update finalized bitstream statistics"
        );
    }

    if (
        data.size() >
        (
            std::numeric_limits<std::uint64_t>::max()
            - total_bytes_
        )
    ) {
        throw std::overflow_error(
            "bitstream byte counter overflow"
        );
    }

    const std::uint64_t new_total_bytes =
        total_bytes_
        + static_cast<std::uint64_t>(
            data.size()
        );

    if (
        new_total_bytes >
        std::numeric_limits<std::uint64_t>::max() / 8U
    ) {
        throw std::overflow_error(
            "bitstream bit counter overflow"
        );
    }

    if (!data.empty()) {
        if (
            EVP_DigestUpdate(
                digest_context_,
                data.data(),
                data.size()
            ) != 1
        ) {
            throw std::runtime_error(
                "EVP_DigestUpdate failed"
            );
        }
    }

    for (const auto byte : data) {
        ones_ += static_cast<std::uint64_t>(
            std::popcount(
                static_cast<unsigned int>(byte)
            )
        );
    }

    total_bytes_ =
        new_total_bytes;
}

BitstreamStatistics
BitstreamStatisticsAccumulator::finalize() {
    if (finalized_) {
        throw std::logic_error(
            "bitstream statistics already finalized"
        );
    }

    finalized_ = true;

    std::array<std::uint8_t, EVP_MAX_MD_SIZE>
        digest{};

    unsigned int digest_length = 0;

    if (
        EVP_DigestFinal_ex(
            digest_context_,
            digest.data(),
            &digest_length
        ) != 1
    ) {
        throw std::runtime_error(
            "EVP_DigestFinal_ex failed"
        );
    }

    if (digest_length != 32U) {
        throw std::runtime_error(
            "unexpected SHA-256 digest length"
        );
    }

    BitstreamStatistics result{};

    result.total_bytes =
        total_bytes_;

    result.total_bits =
        total_bytes_ * 8U;

    result.ones =
        ones_;

    result.zeros =
        result.total_bits - result.ones;

    if (result.total_bits > 0) {
        result.probability_one =
            static_cast<double>(result.ones)
            / static_cast<double>(
                result.total_bits
            );

        result.probability_zero =
            static_cast<double>(result.zeros)
            / static_cast<double>(
                result.total_bits
            );

        result.bias =
            std::abs(
                result.probability_one - 0.5
            );

        result.shannon_entropy =
            entropy_component(
                result.probability_zero
            )
            +
            entropy_component(
                result.probability_one
            );
    }

    result.sha256 =
        bytes_to_hex(
            digest.data(),
            digest_length
        );

    return result;
}

} // namespace bioentropy
