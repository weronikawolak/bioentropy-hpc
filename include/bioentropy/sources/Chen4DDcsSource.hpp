#pragma once

#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <cstdint>
#include <span>
#include <string_view>

namespace bioentropy {

class Chen4DDcsSource final :
    public RandomnessSource {
public:
    explicit Chen4DDcsSource(
        Chen4DDcsConfig config
    );

    std::string_view
    name() const noexcept override;

    bool
    deterministic() const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

private:
    Chen4DDcsConfig config_;

    double exp_r_{};

    double x_{};
    double y_{};
    double z_{};
    double w_{};

    void validate_config() const;

    void advance();

    static double mod1(
        double value
    );
};

} // namespace bioentropy
