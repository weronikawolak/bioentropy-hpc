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

    bool finalized_{false};
};

} // namespace bioentropy
