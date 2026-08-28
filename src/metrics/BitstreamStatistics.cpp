#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <algorithm>
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

double entropy_component(
    double probability
) {
    if (probability <= 0.0) {
        return 0.0;
    }

    return
        -probability
        * std::log2(probability);
}

std::string bytes_to_hex(
    const std::uint8_t* data,
    std::size_t size
) {
    std::ostringstream stream;

    stream
        << std::hex
        << std::setfill('0');

    for (
        std::size_t i = 0;
        i < size;
        ++i
    ) {
        stream
            << std::setw(2)
            << static_cast<unsigned int>(
                data[i]
            );
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
        EVP_MD_CTX_free(
            digest_context_
        );

        digest_context_ = nullptr;

        throw std::runtime_error(
            "EVP_DigestInit_ex failed"
        );
    }
}

BitstreamStatisticsAccumulator::
~BitstreamStatisticsAccumulator() {
    if (digest_context_ != nullptr) {
        EVP_MD_CTX_free(
            digest_context_
        );
    }
}

void
BitstreamStatisticsAccumulator::update(
    std::span<const std::uint8_t> data
) {
    if (finalized_) {
        throw std::logic_error(
            "cannot update finalized "
            "bitstream statistics"
        );
    }

    if (
        data.size() >
        (
            std::numeric_limits<
                std::uint64_t
            >::max()
            - total_bytes_
        )
    ) {
        throw std::overflow_error(
            "bitstream byte counter overflow"
        );
    }

    const std::uint64_t
        new_total_bytes =
            total_bytes_
            + static_cast<std::uint64_t>(
                data.size()
            );

    if (
        new_total_bytes >
        std::numeric_limits<
            std::uint64_t
        >::max() / 8U
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

        ones_ +=
            static_cast<std::uint64_t>(
                std::popcount(
                    static_cast<
                        unsigned int
                    >(byte)
                )
            );

        /*
         * All source conventions in the framework use
         * MSB-first bit packing.
         */
        for (
            unsigned int bit_index = 0;
            bit_index < 8U;
            ++bit_index
        ) {
            const unsigned int shift =
                7U - bit_index;

            const auto bit =
                static_cast<std::uint8_t>(
                    (byte >> shift) & 0x01U
                );

            /*
             * First bit initializes run tracking.
             */
            if (!has_previous_bit_) {
                has_previous_bit_ = true;

                first_bit_ = bit;
                previous_bit_ = bit;

                current_run_length_ = 1;
                longest_run_ = 1;

                continue;
            }

            /*
             * Count 1->1 pairs required for lag-1
             * Pearson correlation.
             */
            if (
                previous_bit_ == 1U &&
                bit == 1U
            ) {
                ++adjacent_11_pairs_;
            }

            /*
             * Runs and transitions.
             */
            if (bit == previous_bit_) {
                ++current_run_length_;
            } else {
                ++transitions_;

                current_run_length_ = 1;
            }

            longest_run_ =
                std::max(
                    longest_run_,
                    current_run_length_
                );

            previous_bit_ = bit;
        }
    }

    total_bytes_ =
        new_total_bytes;
}

BitstreamStatistics
BitstreamStatisticsAccumulator::finalize() {
    if (finalized_) {
        throw std::logic_error(
            "bitstream statistics "
            "already finalized"
        );
    }

    finalized_ = true;

    std::array<
        std::uint8_t,
        EVP_MAX_MD_SIZE
    > digest{};

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
            "unexpected SHA-256 "
            "digest length"
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
        result.total_bits
        - result.ones;

    if (result.total_bits > 0) {
        result.probability_one =
            static_cast<double>(
                result.ones
            )
            /
            static_cast<double>(
                result.total_bits
            );

        result.probability_zero =
            static_cast<double>(
                result.zeros
            )
            /
            static_cast<double>(
                result.total_bits
            );

        result.bias =
            std::abs(
                result.probability_one
                - 0.5
            );

        result.shannon_entropy =
            entropy_component(
                result.probability_zero
            )
            +
            entropy_component(
                result.probability_one
            );

        /*
         * Number of runs:
         *
         * every transition starts a new run.
         */
        result.runs =
            transitions_ + 1U;

        result.longest_run =
            longest_run_;

        const double n =
            static_cast<double>(
                result.total_bits
            );

        const double n0 =
            static_cast<double>(
                result.zeros
            );

        const double n1 =
            static_cast<double>(
                result.ones
            );

        /*
         * Expected number of runs under independent
         * Bernoulli ordering with observed n0 and n1:
         *
         * E[R] = 1 + 2*n0*n1/n
         */
        result.expected_runs =
            1.0
            +
            (
                2.0 * n0 * n1
                / n
            );

        /*
         * Wald-Wolfowitz run-count variance:
         *
         * Var(R) =
         *
         * 2*n0*n1*(2*n0*n1-n)
         * ---------------------
         * n^2 * (n-1)
         */
        if (result.total_bits > 1U) {
            const double variance_numerator =
                2.0
                * n0
                * n1
                * (
                    2.0 * n0 * n1
                    - n
                );

            const double variance_denominator =
                n
                * n
                * (n - 1.0);

            if (
                variance_numerator > 0.0 &&
                variance_denominator > 0.0
            ) {
                const double variance =
                    variance_numerator
                    / variance_denominator;

                if (variance > 0.0) {
                    result.runs_z_score =
                        (
                            static_cast<double>(
                                result.runs
                            )
                            -
                            result.expected_runs
                        )
                        /
                        std::sqrt(
                            variance
                        );

                    result.runs_z_score_defined =
                        true;
                }
            }
        }

        /*
         * Lag-1 Pearson autocorrelation.
         *
         * For:
         *
         * X = b[0 .. N-2]
         * Y = b[1 .. N-1]
         *
         * we need only:
         * - total ones
         * - first bit
         * - last bit
         * - number of adjacent 11 pairs
         *
         * so the metric remains fully streaming.
         */
        if (
            result.total_bits > 1U &&
            has_previous_bit_
        ) {
            const double pair_count =
                static_cast<double>(
                    result.total_bits - 1U
                );

            const double sum_x =
                static_cast<double>(
                    result.ones
                    - previous_bit_
                );

            const double sum_y =
                static_cast<double>(
                    result.ones
                    - first_bit_
                );

            const double sum_xy =
                static_cast<double>(
                    adjacent_11_pairs_
                );

            const double variance_x =
                pair_count * sum_x
                - sum_x * sum_x;

            const double variance_y =
                pair_count * sum_y
                - sum_y * sum_y;

            if (
                variance_x > 0.0 &&
                variance_y > 0.0
            ) {
                result.autocorrelation_lag1 =
                    (
                        pair_count * sum_xy
                        -
                        sum_x * sum_y
                    )
                    /
                    std::sqrt(
                        variance_x
                        * variance_y
                    );

                result.autocorrelation_lag1_defined =
                    true;
            }
        }
    }

    result.sha256 =
        bytes_to_hex(
            digest.data(),
            digest_length
        );

    return result;
}

} // namespace bioentropy
