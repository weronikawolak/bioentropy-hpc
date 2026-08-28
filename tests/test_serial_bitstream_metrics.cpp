#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>

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

void require_close(
    double actual,
    double expected,
    double tolerance,
    const char* message
) {
    if (
        std::abs(
            actual - expected
        ) > tolerance
    ) {
        std::cerr
            << "TEST FAILURE: "
            << message
            << "\nexpected: "
            << expected
            << "\nactual:   "
            << actual
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

} // namespace

int main() {
    /*
     * 0x39 =
     *
     * 0 0 1 1 1 0 0 1
     *
     * Runs:
     *
     * 00 | 111 | 00 | 1
     *
     * runs        = 4
     * longest run = 3
     *
     * n0 = 4
     * n1 = 4
     *
     * E[R] = 5
     *
     * lag-1 Pearson correlation = 1/6
     */
    const std::array<std::uint8_t, 1>
        data{
            0x39
        };

    bioentropy::
    BitstreamStatisticsAccumulator
        accumulator;

    accumulator.update(data);

    const auto result =
        accumulator.finalize();

    require(
        result.total_bits == 8,
        "total bits mismatch"
    );

    require(
        result.zeros == 4,
        "zero count mismatch"
    );

    require(
        result.ones == 4,
        "one count mismatch"
    );

    require(
        result.runs == 4,
        "run count mismatch"
    );

    require(
        result.longest_run == 3,
        "longest run mismatch"
    );

    require_close(
        result.expected_runs,
        5.0,
        1e-12,
        "expected runs mismatch"
    );

    require(
        result.runs_z_score_defined,
        "runs z-score should be defined"
    );

    require_close(
        result.runs_z_score,
        -0.7637626158259734,
        1e-12,
        "runs z-score mismatch"
    );

    require(
        result.autocorrelation_lag1_defined,
        "lag-1 autocorrelation "
        "should be defined"
    );

    require_close(
        result.autocorrelation_lag1,
        1.0 / 6.0,
        1e-12,
        "lag-1 autocorrelation mismatch"
    );

    /*
     * Chunk-boundary test.
     *
     * Stream:
     *
     * 00111001 00111001
     *
     * must give identical metrics whether supplied
     * as one update or two.
     */
    const std::array<std::uint8_t, 2>
        two_bytes{
            0x39,
            0x39
        };

    bioentropy::
    BitstreamStatisticsAccumulator
        contiguous;

    contiguous.update(
        two_bytes
    );

    const auto
        contiguous_result =
            contiguous.finalize();

    bioentropy::
    BitstreamStatisticsAccumulator
        chunked;

    const std::array<std::uint8_t, 1>
        first{
            0x39
        };

    const std::array<std::uint8_t, 1>
        second{
            0x39
        };

    chunked.update(first);
    chunked.update(second);

    const auto
        chunked_result =
            chunked.finalize();

    require(
        contiguous_result.runs
        == chunked_result.runs,
        "chunked run count mismatch"
    );

    require(
        contiguous_result.longest_run
        == chunked_result.longest_run,
        "chunked longest run mismatch"
    );

    require_close(
        contiguous_result.expected_runs,
        chunked_result.expected_runs,
        1e-12,
        "chunked expected runs mismatch"
    );

    require_close(
        contiguous_result.runs_z_score,
        chunked_result.runs_z_score,
        1e-12,
        "chunked runs z-score mismatch"
    );

    require_close(
        contiguous_result.autocorrelation_lag1,
        chunked_result.autocorrelation_lag1,
        1e-12,
        "chunked autocorrelation mismatch"
    );

    require(
        contiguous_result.sha256
        == chunked_result.sha256,
        "chunked SHA mismatch"
    );

    /*
     * Constant stream:
     *
     * autocorrelation and runs z-score are
     * mathematically undefined because variance
     * is zero.
     */
    const std::array<std::uint8_t, 1>
        zeros{
            0x00
        };

    bioentropy::
    BitstreamStatisticsAccumulator
        constant;

    constant.update(zeros);

    const auto constant_result =
        constant.finalize();

    require(
        constant_result.runs == 1,
        "constant stream must have one run"
    );

    require(
        constant_result.longest_run == 8,
        "constant longest run mismatch"
    );

    require(
        !constant_result
            .autocorrelation_lag1_defined,
        "constant stream autocorrelation "
        "must be undefined"
    );

    require(
        !constant_result
            .runs_z_score_defined,
        "constant stream runs z-score "
        "must be undefined"
    );

    std::cout
        << "Serial bitstream metric tests passed.\n";

    return EXIT_SUCCESS;
}
