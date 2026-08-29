#include "bioentropy/sources/LogisticMapSource.hpp"

#include <mpfr.h>

#include <memory>

#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace bioentropy {

/*
 * GCC/Clang 128-bit integer extension used only
 * for exact Q3.29 intermediate arithmetic.
 */
__extension__ using UInt128 = unsigned __int128;


struct LogisticMapSource::MpfrState {
    static constexpr mpfr_prec_t
        PrecisionBits = 256;

    mpfr_t r;
    mpfr_t x;
    mpfr_t one_minus_x;
    mpfr_t product;

    MpfrState() {
        mpfr_init2(
            r,
            PrecisionBits
        );

        mpfr_init2(
            x,
            PrecisionBits
        );

        mpfr_init2(
            one_minus_x,
            PrecisionBits
        );

        mpfr_init2(
            product,
            PrecisionBits
        );
    }

    ~MpfrState() {
        mpfr_clear(r);
        mpfr_clear(x);
        mpfr_clear(one_minus_x);
        mpfr_clear(product);
    }
};

LogisticMapSource::~LogisticMapSource() =
    default;

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
     * Do not rewrite these expressions or enable fast-math
     * in publication builds without documenting the change.
     *
     * Float64 preserves the original implementation.
     *
     * Float32 explicitly rounds both the state and the map
     * parameter to IEEE-754 binary32 on each iteration.
     */
    if (
        config_.arithmetic_mode ==
        LogisticArithmeticMode::Mpfr256
    ) {
        if (!mpfr_state_) {
            throw std::runtime_error(
                "MPFR logistic state is not initialized"
            );
        }

        /*
         * x[n+1] = r*x[n]*(1-x[n])
         *
         * All operations use 256-bit MPFR precision
         * with round-to-nearest.
         */
        mpfr_ui_sub(
            mpfr_state_->one_minus_x,
            1UL,
            mpfr_state_->x,
            MPFR_RNDN
        );

        mpfr_mul(
            mpfr_state_->product,
            mpfr_state_->r,
            mpfr_state_->x,
            MPFR_RNDN
        );

        mpfr_mul(
            mpfr_state_->x,
            mpfr_state_->product,
            mpfr_state_->one_minus_x,
            MPFR_RNDN
        );

        /*
         * state_ is only the binary64 observation used
         * by the common threshold/external interface.
         *
         * The next MPFR iteration continues from the
         * full-precision mpfr_state_->x value.
         */
        state_ =
            mpfr_get_d(
                mpfr_state_->x,
                MPFR_RNDN
            );

        return;
    }

    if (
        config_.arithmetic_mode ==
        LogisticArithmeticMode::FixedQ3_29
    ) {
        /*
         * Unsigned Q3.29 reproduction profile.
         *
         * Scale:
         *
         *     S = 2^29
         *
         * Quantization:
         *
         *     R = floor(r * S)
         *     X = floor(x * S)
         *
         * Recurrence:
         *
         *     X_next =
         *       floor(
         *         R * X * (S - X)
         *         / S^2
         *       )
         *
         * unsigned __int128 is used only for the
         * intermediate product. The persistent state
         * remains exactly representable as double because
         * Q3.29 values are binary rationals well within the
         * 53-bit binary64 significand.
         */
        constexpr std::uint64_t scale =
            std::uint64_t{1} << 29U;

        const std::uint64_t r_fixed =
            static_cast<std::uint64_t>(
                config_.r *
                static_cast<double>(
                    scale
                )
            );

        const std::uint64_t x_fixed =
            static_cast<std::uint64_t>(
                state_ *
                static_cast<double>(
                    scale
                )
            );

        if (x_fixed > scale) {
            throw std::runtime_error(
                "fixed-point logistic state "
                "escaped expected range"
            );
        }

        const UInt128 numerator =
            static_cast<UInt128>(
                r_fixed
            )
            * static_cast<UInt128>(
                x_fixed
            )
            * static_cast<UInt128>(
                scale - x_fixed
            );

        const UInt128 denominator =
            static_cast<UInt128>(
                scale
            )
            * static_cast<UInt128>(
                scale
            );

        const std::uint64_t next_fixed =
            static_cast<std::uint64_t>(
                numerator / denominator
            );

        state_ =
            static_cast<double>(
                next_fixed
            )
            / static_cast<double>(
                scale
            );

        return;
    }

    if (
        config_.arithmetic_mode ==
        LogisticArithmeticMode::Float32
    ) {
        const float r =
            static_cast<float>(
                config_.r
            );

        const float x =
            static_cast<float>(
                state_
            );

        const float next =
            (r * x) *
            (1.0F - x);

        state_ =
            static_cast<double>(
                next
            );

        return;
    }

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

    if (
        config_.arithmetic_mode ==
        LogisticArithmeticMode::Mpfr256
    ) {
        mpfr_state_ =
            std::make_unique<MpfrState>();

        int r_status = 0;

        if (!config_.r_literal.empty()) {
            r_status =
                mpfr_set_str(
                    mpfr_state_->r,
                    config_.r_literal.c_str(),
                    10,
                    MPFR_RNDN
                );
        } else {
            mpfr_set_d(
                mpfr_state_->r,
                config_.r,
                MPFR_RNDN
            );
        }

        if (r_status != 0) {
            throw std::runtime_error(
                "failed to parse MPFR logistic r"
            );
        }

        int x_status = 0;

        if (
            config_.initial_state_mode ==
                LogisticInitialStateMode::Explicit
            &&
            config_.x0_literal.has_value()
        ) {
            x_status =
                mpfr_set_str(
                    mpfr_state_->x,
                    config_.x0_literal->c_str(),
                    10,
                    MPFR_RNDN
                );
        } else {
            mpfr_set_d(
                mpfr_state_->x,
                initial_state_,
                MPFR_RNDN
            );
        }

        if (x_status != 0) {
            throw std::runtime_error(
                "failed to parse MPFR logistic x0"
            );
        }

        state_ =
            mpfr_get_d(
                mpfr_state_->x,
                MPFR_RNDN
            );
    } else {
        mpfr_state_.reset();
    }

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
