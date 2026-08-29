#include <array>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string_view>

namespace {

struct State {
    double x;
    double y;
    double z;
    double w;

    bool operator==(
        const State& other
    ) const noexcept {
        return
            x == other.x
            && y == other.y
            && z == other.z
            && w == other.w;
    }
};

struct ProbeResult {
    bool detected{false};

    std::uint64_t mu{0};
    std::uint64_t lambda{0};

    std::uint64_t search_transitions{0};
    std::uint64_t total_evaluations{0};
};

double mod1(
    const double value
) {
    return value - std::floor(value);
}

class ChenTransition {
public:
    explicit ChenTransition(
        const double r
    )
        : exp_r_(
            std::exp(r)
        ) {
    }

    State operator()(
        const State& state
    ) const {
        const double next_x =
            mod1(
                (
                    (1.7 + exp_r_)
                    * state.x
                )
                +
                (
                    0.1
                    * state.y
                )
            );

        const double next_y =
            mod1(
                (
                    (0.4 + exp_r_)
                    * state.y
                )
                -
                (
                    0.2
                    * state.z
                )
            );

        const double next_z =
            mod1(
                (
                    0.3
                    * state.x
                )
                +
                (
                    (0.5 + exp_r_)
                    * state.z
                )
            );

        const double next_w =
            mod1(
                (
                    0.1
                    * state.y
                )
                +
                (
                    (1.8 + exp_r_)
                    * state.w
                )
            );

        return {
            next_x,
            next_y,
            next_z,
            next_w
        };
    }

private:
    double exp_r_;
};

ProbeResult brent_cycle_detection(
    const State& initial_state,
    const ChenTransition& transition,
    const std::uint64_t max_search_transitions
) {
    ProbeResult result{};

    if (max_search_transitions == 0) {
        return result;
    }

    std::uint64_t power = 1;
    std::uint64_t lambda = 1;

    State tortoise =
        initial_state;

    State hare =
        transition(initial_state);

    result.search_transitions = 1;
    result.total_evaluations = 1;

    while (
        !(tortoise == hare)
        &&
        result.search_transitions
            < max_search_transitions
    ) {
        if (power == lambda) {
            tortoise = hare;

            if (
                power
                <= (
                    std::numeric_limits<
                        std::uint64_t
                    >::max()
                    / 2U
                )
            ) {
                power *= 2U;
            }

            lambda = 0;
        }

        hare =
            transition(hare);

        ++lambda;
        ++result.search_transitions;
        ++result.total_evaluations;
    }

    if (!(tortoise == hare)) {
        return result;
    }

    result.detected = true;
    result.lambda = lambda;

    /*
     * Locate mu after an exact collision has been found.
     */
    State first =
        initial_state;

    State second =
        initial_state;

    for (
        std::uint64_t i = 0;
        i < lambda;
        ++i
    ) {
        second =
            transition(second);

        ++result.total_evaluations;
    }

    std::uint64_t mu = 0;

    while (!(first == second)) {
        first =
            transition(first);

        second =
            transition(second);

        result.total_evaluations += 2U;

        ++mu;
    }

    result.mu = mu;

    return result;
}

State apply_burn_in(
    State state,
    const ChenTransition& transition,
    const std::uint64_t burn_in
) {
    for (
        std::uint64_t i = 0;
        i < burn_in;
        ++i
    ) {
        state =
            transition(state);
    }

    return state;
}

void print_result(
    const std::string_view label,
    const ProbeResult& result,
    const std::uint64_t bound
) {
    std::cout
        << label
        << '\n';

    std::cout
        << "  detected           : "
        << (
            result.detected
                ? "yes"
                : "no"
        )
        << '\n';

    if (result.detected) {
        std::cout
            << "  mu                 : "
            << result.mu
            << '\n';

        std::cout
            << "  lambda             : "
            << result.lambda
            << '\n';
    } else {
        std::cout
            << "  statement          : "
            << "no exact recurrence detected "
            << "within "
            << bound
            << " transitions"
            << '\n';
    }

    std::cout
        << "  search transitions : "
        << result.search_transitions
        << '\n';

    std::cout
        << "  total evaluations  : "
        << result.total_evaluations
        << '\n';
}

} // namespace

int main() {
    constexpr double r =
        5.0;

    constexpr std::uint64_t
        burn_in =
            1000;

    constexpr std::uint64_t
        max_search_transitions =
            10'000'000;

    const State initial_state{
        0.1,
        0.2,
        0.3,
        0.4
    };

    const ChenTransition
        transition(r);

    const State after_burn =
        apply_burn_in(
            initial_state,
            transition,
            burn_in
        );

    std::cout
        << "Chen 4D-DCS exact binary64 periodicity probe\n"
        << "============================================\n";

    std::cout
        << std::setprecision(17);

    std::cout
        << "r                    : "
        << r
        << '\n';

    std::cout
        << "initial state        : "
        << initial_state.x
        << ", "
        << initial_state.y
        << ", "
        << initial_state.z
        << ", "
        << initial_state.w
        << '\n';

    std::cout
        << "burn-in              : "
        << burn_in
        << '\n';

    std::cout
        << "search bound         : "
        << max_search_transitions
        << '\n';

    std::cout
        << "equality              : "
        << "exact binary64 x/y/z/w equality\n";

    std::cout
        << "modulo semantics      : "
        << "v - floor(v)\n\n";

    const auto from_initial =
        brent_cycle_detection(
            initial_state,
            transition,
            max_search_transitions
        );

    print_result(
        "From initial state:",
        from_initial,
        max_search_transitions
    );

    std::cout << '\n';

    const auto after_burn_result =
        brent_cycle_detection(
            after_burn,
            transition,
            max_search_transitions
        );

    print_result(
        "After burn-in 1000:",
        after_burn_result,
        max_search_transitions
    );

    return 0;
}
