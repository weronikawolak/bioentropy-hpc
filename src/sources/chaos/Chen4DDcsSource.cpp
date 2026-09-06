#include "bioentropy/sources/Chen4DDcsSource.hpp"

#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <utility>

namespace bioentropy {

Chen4DDcsSource::Chen4DDcsSource(
    Chen4DDcsConfig config
)
    : config_(
        std::move(config)
    ) {
    validate_config();

    exp_r_ =
        std::exp(config_.r);

    reset();
}

std::string_view
Chen4DDcsSource::name() const noexcept {
    return "chen_4d_dcs";
}

bool
Chen4DDcsSource::deterministic() const noexcept {
    return true;
}

double Chen4DDcsSource::mod1(
    const double value
) {
    /*
     * Mathematical modulo 1.
     *
     * This intentionally differs from std::fmod
     * for negative arguments. The resulting
     * digital state is always in [0, 1).
     */
    return
        value
        - std::floor(value);
}

void
Chen4DDcsSource::validate_config() const {
    if (
        !std::isfinite(config_.r)
        || config_.r < 0.0
        || config_.r > 10.0
    ) {
        throw std::invalid_argument(
            "Chen 4D-DCS r must satisfy "
            "0 <= r <= 10"
        );
    }

    const auto valid_state =
        [](
            const double value
        ) {
            return
                std::isfinite(value)
                && value >= 0.0
                && value < 1.0;
        };

    if (
        !valid_state(config_.x0)
        || !valid_state(config_.y0)
        || !valid_state(config_.z0)
        || !valid_state(config_.w0)
    ) {
        throw std::invalid_argument(
            "Chen 4D-DCS initial states "
            "must satisfy 0 <= state < 1"
        );
    }

    if (
        !std::isfinite(
            config_.threshold
        )
        || config_.threshold <= 0.0
        || config_.threshold >= 1.0
    ) {
        throw std::invalid_argument(
            "Chen 4D-DCS threshold must "
            "satisfy 0 < threshold < 1"
        );
    }
}

void Chen4DDcsSource::advance() {
    /*
     * Chen et al. (2026), 4D-DCS, Equation (5).
     *
     * All four new coordinates are calculated
     * from the same old state. Do not perform
     * in-place sequential coordinate updates.
     *
     * Parenthesization is intentional.
     */
    const double old_x = x_;
    const double old_y = y_;
    const double old_z = z_;
    const double old_w = w_;

    const double next_x =
        mod1(
            (
                (1.7 + exp_r_)
                * old_x
            )
            +
            (
                0.1
                * old_y
            )
        );

    const double next_y =
        mod1(
            (
                (0.4 + exp_r_)
                * old_y
            )
            -
            (
                0.2
                * old_z
            )
        );

    const double next_z =
        mod1(
            (
                0.3
                * old_x
            )
            +
            (
                (0.5 + exp_r_)
                * old_z
            )
        );

    const double next_w =
        mod1(
            (
                0.1
                * old_y
            )
            +
            (
                (1.8 + exp_r_)
                * old_w
            )
        );

    x_ = next_x;
    y_ = next_y;
    z_ = next_z;
    w_ = next_w;
}

void Chen4DDcsSource::reset() {
    x_ = config_.x0;
    y_ = config_.y0;
    z_ = config_.z0;
    w_ = config_.w0;

    for (
        std::uint64_t iteration = 0;
        iteration < config_.burn_in;
        ++iteration
    ) {
        advance();
    }
}

void Chen4DDcsSource::generate(
    std::span<std::uint8_t> output
) {
    /*
     * Project-defined extraction profile.
     *
     * One state transition produces four bits:
     *
     *     x, y, z, w
     *
     * coordinate >= threshold -> 1
     * coordinate <  threshold -> 0
     *
     * Two iterations form one byte:
     *
     * bit 7..4 = x,y,z,w from iteration n
     * bit 3..0 = x,y,z,w from iteration n+1
     */
    for (
        std::size_t byte_index = 0;
        byte_index < output.size();
        ++byte_index
    ) {
        std::uint8_t byte = 0;

        for (
            std::size_t half = 0;
            half < 2;
            ++half
        ) {
            advance();

            const double coordinates[4] = {
                x_,
                y_,
                z_,
                w_
            };

            for (
                std::size_t coordinate = 0;
                coordinate < 4;
                ++coordinate
            ) {
                if (
                    coordinates[coordinate]
                    >= config_.threshold
                ) {
                    const std::size_t bit =
                        7U
                        - (
                            half * 4U
                            + coordinate
                        );

                    byte =
                        static_cast<std::uint8_t>(
                            byte
                            | (
                                std::uint8_t{1}
                                << bit
                            )
                        );
                }
            }
        }

        output[byte_index] = byte;
    }
}

} // namespace bioentropy
