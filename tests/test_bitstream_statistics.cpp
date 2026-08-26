#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <span>
#include <string>

namespace {

void require(
    bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "TEST FAILURE: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

bool approximately_equal(
    double left,
    double right,
    double tolerance = 1e-12
) {
    return std::abs(left - right) <= tolerance;
}

} // namespace

int main() {
    /*
     * Binary representation:
     *
     * 00 = 00000000
     * FF = 11111111
     * F0 = 11110000
     * 0F = 00001111
     *
     * Total:
     *   16 zeros
     *   16 ones
     */
    const std::array<std::uint8_t, 4> data{
        0x00,
        0xFF,
        0xF0,
        0x0F
    };

    bioentropy::BitstreamStatisticsAccumulator
        accumulator;

    accumulator.update(data);

    const auto statistics =
        accumulator.finalize();

    require(
        statistics.total_bytes == 4,
        "incorrect byte count"
    );

    require(
        statistics.total_bits == 32,
        "incorrect bit count"
    );

    require(
        statistics.zeros == 16,
        "incorrect zero count"
    );

    require(
        statistics.ones == 16,
        "incorrect one count"
    );

    require(
        approximately_equal(
            statistics.probability_zero,
            0.5
        ),
        "incorrect zero probability"
    );

    require(
        approximately_equal(
            statistics.probability_one,
            0.5
        ),
        "incorrect one probability"
    );

    require(
        approximately_equal(
            statistics.bias,
            0.0
        ),
        "incorrect bias"
    );

    require(
        approximately_equal(
            statistics.shannon_entropy,
            1.0
        ),
        "incorrect Shannon entropy"
    );

    require(
        statistics.sha256 ==
        "f0e773f69d71d66fee4f9dc4b9bfeea"
        "ebb73f4e90c1c814c7f9e61178e50e553",
        "incorrect SHA-256 digest"
    );

    /*
     * Verify that chunking does not affect results.
     */
    bioentropy::BitstreamStatisticsAccumulator
        chunked_accumulator;

    chunked_accumulator.update(
        std::span<const std::uint8_t>(
            data.data(),
            2
        )
    );

    chunked_accumulator.update(
        std::span<const std::uint8_t>(
            data.data() + 2,
            2
        )
    );

    const auto chunked_statistics =
        chunked_accumulator.finalize();

    require(
        chunked_statistics.total_bytes ==
        statistics.total_bytes,
        "chunked byte count differs"
    );

    require(
        chunked_statistics.ones ==
        statistics.ones,
        "chunked ones count differs"
    );

    require(
        chunked_statistics.zeros ==
        statistics.zeros,
        "chunked zeros count differs"
    );

    require(
        chunked_statistics.sha256 ==
        statistics.sha256,
        "chunked SHA-256 differs"
    );

    require(
        approximately_equal(
            chunked_statistics.shannon_entropy,
            statistics.shannon_entropy
        ),
        "chunked Shannon entropy differs"
    );

    /*
     * Degenerate all-zero stream.
     */
    const std::array<std::uint8_t, 2>
        zero_data{0x00, 0x00};

    bioentropy::BitstreamStatisticsAccumulator
        zero_accumulator;

    zero_accumulator.update(zero_data);

    const auto zero_statistics =
        zero_accumulator.finalize();

    require(
        zero_statistics.ones == 0,
        "all-zero stream contains ones"
    );

    require(
        zero_statistics.zeros == 16,
        "incorrect zero count for all-zero stream"
    );

    require(
        approximately_equal(
            zero_statistics.bias,
            0.5
        ),
        "incorrect all-zero bias"
    );

    require(
        approximately_equal(
            zero_statistics.shannon_entropy,
            0.0
        ),
        "all-zero entropy must equal zero"
    );

    std::cout
        << "BitstreamStatistics tests passed.\n";

    return EXIT_SUCCESS;
}
