#include "bioentropy/analysis/BrentCycleDetection.hpp"

#include <cstdint>
#include <cstdlib>
#include <iostream>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "FAILED: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

}  // namespace

int main() {
    /*
     * Pure 7-state cycle:
     *
     * 0 -> 1 -> ... -> 6 -> 0
     */
    {
        const auto result =
            bioentropy::analysis::
                brent_cycle_detection(
                    std::uint64_t{0},
                    [](
                        std::uint64_t& x
                    ) {
                        x =
                            (x + 1U)
                            % 7U;
                    },
                    [](
                        const std::uint64_t a,
                        const std::uint64_t b
                    ) {
                        return a == b;
                    },
                    1000
                );

        require(
            result.detected,
            "7-state cycle not detected"
        );

        require(
            result.mu == 0,
            "wrong mu for pure cycle"
        );

        require(
            result.lambda == 7,
            "wrong lambda for pure cycle"
        );
    }

    /*
     * Transient:
     *
     * 0 -> 1 -> 2 -> 3 -> 3 ...
     *
     * mu = 3
     * lambda = 1
     */
    {
        const auto result =
            bioentropy::analysis::
                brent_cycle_detection(
                    std::uint64_t{0},
                    [](
                        std::uint64_t& x
                    ) {
                        if (x < 3U) {
                            ++x;
                        }
                    },
                    [](
                        const std::uint64_t a,
                        const std::uint64_t b
                    ) {
                        return a == b;
                    },
                    1000
                );

        require(
            result.detected,
            "fixed-point cycle not detected"
        );

        require(
            result.mu == 3,
            "wrong transient length"
        );

        require(
            result.lambda == 1,
            "wrong fixed-point cycle length"
        );
    }

    /*
     * No repetition inside the search bound.
     */
    {
        const auto result =
            bioentropy::analysis::
                brent_cycle_detection(
                    std::uint64_t{0},
                    [](
                        std::uint64_t& x
                    ) {
                        ++x;
                    },
                    [](
                        const std::uint64_t a,
                        const std::uint64_t b
                    ) {
                        return a == b;
                    },
                    100
                );

        require(
            !result.detected,
            "false cycle detection"
        );
    }

    std::cout
        << "Brent cycle detection tests passed.\n";

    return EXIT_SUCCESS;
}
