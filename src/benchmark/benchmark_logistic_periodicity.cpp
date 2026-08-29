#include "bioentropy/analysis/BrentCycleDetection.hpp"

#include <mpfr.h>
#include <yaml-cpp/yaml.h>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

__extension__
using UInt128 =
    unsigned __int128;

constexpr std::uint64_t
    FixedScale =
        std::uint64_t{1} << 29U;


/*
 * ---------------------------------------------------------
 * FLOAT64
 * ---------------------------------------------------------
 */

struct Float64Orbit {
    double r{};
    double x{};

    void step() {
        x =
            (r * x)
            * (1.0 - x);
    }

    bool same_state(
        const Float64Orbit& other
    ) const noexcept {
        return x == other.x;
    }
};


/*
 * ---------------------------------------------------------
 * FLOAT32
 * ---------------------------------------------------------
 */

struct Float32Orbit {
    float r{};
    float x{};

    void step() {
        x =
            (r * x)
            * (1.0F - x);
    }

    bool same_state(
        const Float32Orbit& other
    ) const noexcept {
        return x == other.x;
    }
};


/*
 * ---------------------------------------------------------
 * FIXED Q3.29
 * ---------------------------------------------------------
 */

struct FixedQ3_29Orbit {
    std::uint64_t r{};
    std::uint64_t x{};

    void step() {
        const UInt128 numerator =
            static_cast<UInt128>(r)
            * static_cast<UInt128>(x)
            * static_cast<UInt128>(
                FixedScale - x
            );

        const UInt128 denominator =
            static_cast<UInt128>(
                FixedScale
            )
            * static_cast<UInt128>(
                FixedScale
            );

        x =
            static_cast<std::uint64_t>(
                numerator
                / denominator
            );
    }

    bool same_state(
        const FixedQ3_29Orbit& other
    ) const noexcept {
        return x == other.x;
    }
};


/*
 * ---------------------------------------------------------
 * MPFR-256
 * ---------------------------------------------------------
 */

class Mpfr256Orbit {
public:
    static constexpr mpfr_prec_t
        PrecisionBits = 256;

    Mpfr256Orbit(
        const std::string& r_literal,
        const std::string& x_literal
    ) {
        initialize();

        if (
            mpfr_set_str(
                r_,
                r_literal.c_str(),
                10,
                MPFR_RNDN
            ) != 0
        ) {
            throw std::runtime_error(
                "cannot parse MPFR r"
            );
        }

        if (
            mpfr_set_str(
                x_,
                x_literal.c_str(),
                10,
                MPFR_RNDN
            ) != 0
        ) {
            throw std::runtime_error(
                "cannot parse MPFR x0"
            );
        }
    }

    Mpfr256Orbit(
        const Mpfr256Orbit& other
    ) {
        initialize();

        mpfr_set(
            r_,
            other.r_,
            MPFR_RNDN
        );

        mpfr_set(
            x_,
            other.x_,
            MPFR_RNDN
        );
    }

    Mpfr256Orbit&
    operator=(
        const Mpfr256Orbit& other
    ) {
        if (this == &other) {
            return *this;
        }

        mpfr_set(
            r_,
            other.r_,
            MPFR_RNDN
        );

        mpfr_set(
            x_,
            other.x_,
            MPFR_RNDN
        );

        return *this;
    }

    ~Mpfr256Orbit() {
        mpfr_clear(r_);
        mpfr_clear(x_);
        mpfr_clear(one_minus_x_);
        mpfr_clear(product_);
    }

    void step() {
        mpfr_ui_sub(
            one_minus_x_,
            1UL,
            x_,
            MPFR_RNDN
        );

        mpfr_mul(
            product_,
            r_,
            x_,
            MPFR_RNDN
        );

        mpfr_mul(
            x_,
            product_,
            one_minus_x_,
            MPFR_RNDN
        );
    }

    bool same_state(
        const Mpfr256Orbit& other
    ) const noexcept {
        return
            mpfr_equal_p(
                x_,
                other.x_
            ) != 0;
    }

private:
    mpfr_t r_;
    mpfr_t x_;

    mpfr_t one_minus_x_;
    mpfr_t product_;

    void initialize() {
        mpfr_init2(
            r_,
            PrecisionBits
        );

        mpfr_init2(
            x_,
            PrecisionBits
        );

        mpfr_init2(
            one_minus_x_,
            PrecisionBits
        );

        mpfr_init2(
            product_,
            PrecisionBits
        );
    }
};


template <typename Orbit>
void apply_burn_in(
    Orbit& orbit,
    const std::uint64_t burn_in
) {
    for (
        std::uint64_t i = 0;
        i < burn_in;
        ++i
    ) {
        orbit.step();
    }
}


template <typename Orbit>
bioentropy::analysis::
CycleDetectionResult
detect(
    const Orbit& start,
    const std::uint64_t max_steps
) {
    return
        bioentropy::analysis::
            brent_cycle_detection(
                start,
                [](
                    Orbit& state
                ) {
                    state.step();
                },
                [](
                    const Orbit& a,
                    const Orbit& b
                ) {
                    return
                        a.same_state(b);
                },
                max_steps
            );
}


void write_result(
    std::ofstream& output,
    const std::string& mode,
    const std::string& r,
    const std::string& x0,
    const std::uint64_t burn_in,
    const std::uint64_t max_steps,
    const bioentropy::analysis::
        CycleDetectionResult& result
) {
    output
        << mode << '\t'
        << r << '\t'
        << x0 << '\t'
        << burn_in << '\t'
        << max_steps << '\t'
        << (
            result.detected
                ? "true"
                : "false"
        )
        << '\t';

    if (result.detected) {
        output
            << result.mu
            << '\t'
            << result.lambda;
    } else {
        output
            << "NA"
            << '\t'
            << "NA";
    }

    output
        << '\t'
        << result.step_evaluations
        << '\n';
}

}  // namespace


int main(
    int argc,
    char** argv
) {
    const std::filesystem::path
        config_path =
            argc >= 2
                ? argv[1]
                : (
                    "configs/generated/"
                    "logistic-precision-smoke/"
                    "logistic-float64.yaml"
                );

    const std::uint64_t
        max_detection_steps =
            argc >= 3
                ? std::stoull(argv[2])
                : 10'000'000ULL;

    const YAML::Node config =
        YAML::LoadFile(
            config_path.string()
        );

    const YAML::Node parameters =
        config["source"]["parameters"];

    const YAML::Node initial_state =
        parameters["initial_state"];

    if (
        !initial_state
        || !initial_state["x0"]
    ) {
        throw std::runtime_error(
            "periodicity probe currently requires "
            "explicit logistic x0"
        );
    }

    const std::string r_literal =
        parameters["r"].Scalar();

    const std::string x0_literal =
        initial_state["x0"].Scalar();

    const double r_double =
        parameters["r"].as<double>();

    const double x0_double =
        initial_state["x0"]
            .as<double>();

    const std::uint64_t burn_in =
        parameters["burn_in"]
            ? parameters["burn_in"]
                .as<std::uint64_t>()
            : 0U;

    const std::filesystem::path
        output_path =
            "results/aggregated/"
            "logistic_periodicity_smoke.tsv";

    std::filesystem::create_directories(
        output_path.parent_path()
    );

    std::ofstream output(
        output_path
    );

    if (!output) {
        throw std::runtime_error(
            "cannot open periodicity output"
        );
    }

    output
        << "arithmetic\t"
        << "r\t"
        << "x0\t"
        << "burn_in\t"
        << "max_detection_steps\t"
        << "cycle_detected\t"
        << "post_burn_in_mu\t"
        << "cycle_length_lambda\t"
        << "step_evaluations\n";

    /*
     * float32
     */
    {
        Float32Orbit orbit{
            static_cast<float>(
                r_double
            ),
            static_cast<float>(
                x0_double
            )
        };

        apply_burn_in(
            orbit,
            burn_in
        );

        const auto result =
            detect(
                orbit,
                max_detection_steps
            );

        write_result(
            output,
            "float32",
            r_literal,
            x0_literal,
            burn_in,
            max_detection_steps,
            result
        );

        std::cout
            << "float32: "
            << (
                result.detected
                    ? "cycle detected"
                    : "no cycle within limit"
            );

        if (result.detected) {
            std::cout
                << " mu="
                << result.mu
                << " lambda="
                << result.lambda;
        }

        std::cout << '\n';
    }

    /*
     * float64
     */
    {
        Float64Orbit orbit{
            r_double,
            x0_double
        };

        apply_burn_in(
            orbit,
            burn_in
        );

        const auto result =
            detect(
                orbit,
                max_detection_steps
            );

        write_result(
            output,
            "float64",
            r_literal,
            x0_literal,
            burn_in,
            max_detection_steps,
            result
        );

        std::cout
            << "float64: "
            << (
                result.detected
                    ? "cycle detected"
                    : "no cycle within limit"
            );

        if (result.detected) {
            std::cout
                << " mu="
                << result.mu
                << " lambda="
                << result.lambda;
        }

        std::cout << '\n';
    }

    /*
     * fixed Q3.29
     */
    {
        FixedQ3_29Orbit orbit{
            static_cast<std::uint64_t>(
                r_double
                * static_cast<double>(
                    FixedScale
                )
            ),
            static_cast<std::uint64_t>(
                x0_double
                * static_cast<double>(
                    FixedScale
                )
            )
        };

        apply_burn_in(
            orbit,
            burn_in
        );

        const auto result =
            detect(
                orbit,
                max_detection_steps
            );

        write_result(
            output,
            "fixed_q3_29",
            r_literal,
            x0_literal,
            burn_in,
            max_detection_steps,
            result
        );

        std::cout
            << "fixed_q3_29: "
            << (
                result.detected
                    ? "cycle detected"
                    : "no cycle within limit"
            );

        if (result.detected) {
            std::cout
                << " mu="
                << result.mu
                << " lambda="
                << result.lambda;
        }

        std::cout << '\n';
    }

    /*
     * MPFR-256
     */
    {
        Mpfr256Orbit orbit(
            r_literal,
            x0_literal
        );

        apply_burn_in(
            orbit,
            burn_in
        );

        const auto result =
            detect(
                orbit,
                max_detection_steps
            );

        write_result(
            output,
            "mpfr_256",
            r_literal,
            x0_literal,
            burn_in,
            max_detection_steps,
            result
        );

        std::cout
            << "mpfr_256: "
            << (
                result.detected
                    ? "cycle detected"
                    : "no cycle within limit"
            );

        if (result.detected) {
            std::cout
                << " mu="
                << result.mu
                << " lambda="
                << result.lambda;
        }

        std::cout << '\n';
    }

    std::cout
        << "\nSaved: "
        << output_path.string()
        << '\n';

    return 0;
}
