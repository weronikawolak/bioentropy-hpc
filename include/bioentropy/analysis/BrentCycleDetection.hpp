#pragma once

#include <cstdint>
#include <limits>
#include <utility>

namespace bioentropy::analysis {

struct CycleDetectionResult {
    bool detected{false};

    /*
     * Transient length relative to the
     * supplied starting state.
     */
    std::uint64_t mu{0};

    /*
     * Exact cycle length.
     */
    std::uint64_t lambda{0};

    /*
     * Number of state-transition evaluations
     * performed by the detector.
     */
    std::uint64_t step_evaluations{0};
};

template <
    typename State,
    typename Step,
    typename Equal
>
CycleDetectionResult
brent_cycle_detection(
    const State& start,
    Step step,
    Equal equal,
    const std::uint64_t max_detection_steps
) {
    CycleDetectionResult result{};

    if (max_detection_steps == 0) {
        return result;
    }

    std::uint64_t evaluations = 0;

    State tortoise = start;
    State hare = start;

    step(hare);
    ++evaluations;

    std::uint64_t power = 1;
    std::uint64_t lambda = 1;

    /*
     * Phase 1:
     * detect repetition and determine lambda.
     */
    while (!equal(tortoise, hare)) {
        if (
            evaluations >=
            max_detection_steps
        ) {
            result.step_evaluations =
                evaluations;

            return result;
        }

        if (power == lambda) {
            tortoise = hare;

            if (
                power <=
                std::numeric_limits<
                    std::uint64_t
                >::max() / 2U
            ) {
                power *= 2U;
            }

            lambda = 0;
        }

        step(hare);
        ++evaluations;
        ++lambda;
    }

    /*
     * Phase 2:
     * determine mu.
     *
     * A cycle has already been proven at this
     * point, therefore these additional
     * evaluations are not part of the search
     * limit but are still reported.
     */
    tortoise = start;
    hare = start;

    for (
        std::uint64_t i = 0;
        i < lambda;
        ++i
    ) {
        step(hare);
        ++evaluations;
    }

    std::uint64_t mu = 0;

    while (!equal(tortoise, hare)) {
        step(tortoise);
        step(hare);

        evaluations += 2U;
        ++mu;
    }

    result.detected = true;
    result.mu = mu;
    result.lambda = lambda;
    result.step_evaluations =
        evaluations;

    return result;
}

}  // namespace bioentropy::analysis
