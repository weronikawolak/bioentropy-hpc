#pragma once

#include <cstdint>
#include <span>
#include <string>

#include <openssl/evp.h>

namespace bioentropy {

struct BitstreamStatistics {
    std::uint64_t total_bytes{};
    std::uint64_t total_bits{};

    std::uint64_t zeros{};
    std::uint64_t ones{};

    double probability_zero{};
    double probability_one{};

    double bias{};
    double shannon_entropy{};

    /*
     * Pearson correlation between consecutive bits:
     *
     * X = b[0 .. N-2]
     * Y = b[1 .. N-1]
     *
     * Undefined for streams for which either side has
     * zero variance.
     */
    double autocorrelation_lag1{};
    bool autocorrelation_lag1_defined{false};

    /*
     * Wald-Wolfowitz style run statistics.
     */
    std::uint64_t runs{};
    double expected_runs{};

    double runs_z_score{};
    bool runs_z_score_defined{false};

    std::uint64_t longest_run{};

    std::string sha256;
};

class BitstreamStatisticsAccumulator {
public:
    BitstreamStatisticsAccumulator();

    ~BitstreamStatisticsAccumulator();

    BitstreamStatisticsAccumulator(
        const BitstreamStatisticsAccumulator&
    ) = delete;

    BitstreamStatisticsAccumulator& operator=(
        const BitstreamStatisticsAccumulator&
    ) = delete;

    void update(
        std::span<const std::uint8_t> data
    );

    BitstreamStatistics finalize();

private:
    EVP_MD_CTX* digest_context_{nullptr};

    std::uint64_t total_bytes_{0};
    std::uint64_t ones_{0};

    /*
     * Serial-bit state.
     *
     * This state deliberately persists between update()
     * calls so chunk boundaries do not change metrics.
     */
    bool has_previous_bit_{false};

    std::uint8_t first_bit_{0};
    std::uint8_t previous_bit_{0};

    std::uint64_t adjacent_11_pairs_{0};
    std::uint64_t transitions_{0};

    std::uint64_t current_run_length_{0};
    std::uint64_t longest_run_{0};

    bool finalized_{false};
};

} // namespace bioentropy
