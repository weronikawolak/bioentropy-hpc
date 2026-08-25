#include "bioentropy/sources/LogisticMapSource.hpp"

#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace bioentropy {

LogisticMapSource::LogisticMapSource(
    LogisticMapConfig config,
    Seed256 seed
)
    : config_(std::move(config)),
      seed_(seed) {

    validate_config();
    reset();
}

std::string_view LogisticMapSource::name() const noexcept {
    return "logistic";
}

bool LogisticMapSource::deterministic() const noexcept {
    return true;
}

double LogisticMapSource::initial_state() const noexcept {
    return initial_state_;
}

double LogisticMapSource::derive_initial_state(
    const Seed256& seed
) {
    std::uint64_t value = 0;

    for (std::size_t i = 0; i < 8; ++i) {
        value =
            (value << 8U) |
            static_cast<std::uint64_t>(seed[i]);
    }

    /*
     * Keep the upper 53 bits because IEEE-754 binary64
     * can represent integers exactly up to 2^53.
     */
    std::uint64_t mantissa =
        value >> 11U;

    /*
     * Ensure x0 is strictly greater than zero.
     */
    if (mantissa == 0) {
        mantissa = 1;
    }

    /*
     * Exact scaling by 2^-53.
     *
     * Result:
     *     0 < x0 < 1
     */
    return std::ldexp(
        static_cast<double>(mantissa),
        -53
    );
}

void LogisticMapSource::validate_config() const {
    if (
        !std::isfinite(config_.r) ||
        config_.r <= 0.0 ||
        config_.r > 4.0
    ) {
        throw std::invalid_argument(
            "logistic parameter r must satisfy 0 < r <= 4"
        );
    }

    if (
        config_.initial_state_mode ==
        LogisticInitialStateMode::Explicit
    ) {
        if (!config_.x0.has_value()) {
            throw std::invalid_argument(
                "explicit logistic initial state requires x0"
            );
        }

        if (
            !std::isfinite(*config_.x0) ||
            *config_.x0 <= 0.0 ||
            *config_.x0 >= 1.0
        ) {
            throw std::invalid_argument(
                "logistic x0 must satisfy 0 < x0 < 1"
            );
        }
    }
}

void LogisticMapSource::advance() {
    /*
     * Parenthesization is intentional.
     *
     * Do not rewrite this expression or enable fast-math
     * in publication builds without documenting the change.
     */
    state_ =
        (config_.r * state_) *
        (1.0 - state_);
}

void LogisticMapSource::reset() {
    if (
        config_.initial_state_mode ==
        LogisticInitialStateMode::Explicit
    ) {
        initial_state_ =
            *config_.x0;
    } else {
        initial_state_ =
            derive_initial_state(seed_);
    }

    state_ = initial_state_;

    for (
        std::uint64_t iteration = 0;
        iteration < config_.burn_in;
        ++iteration
    ) {
        advance();
    }
}

void LogisticMapSource::generate(
    std::span<std::uint8_t> output
) {
    for (auto& byte : output) {
        byte = 0;

        for (int bit_index = 0; bit_index < 8; ++bit_index) {
            advance();

            byte = static_cast<std::uint8_t>(
                byte << 1U
            );

            if (state_ >= 0.5) {
                byte =
                    static_cast<std::uint8_t>(
                        byte | 0x01U
                    );
            }
        }
    }
}

} // namespace bioentropy
