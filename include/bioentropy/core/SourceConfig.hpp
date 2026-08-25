#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <variant>

namespace bioentropy {

enum class LogisticInitialStateMode {
    Explicit,
    DerivedFromSeed
};

enum class LogisticExtractionMethod {
    Threshold
};

struct LogisticMapConfig {
    double r{};
    LogisticInitialStateMode initial_state_mode{
        LogisticInitialStateMode::DerivedFromSeed
    };

    std::optional<double> x0;

    std::uint64_t burn_in{0};

    LogisticExtractionMethod extraction{
        LogisticExtractionMethod::Threshold
    };
};

using SourceParameters = std::variant<
    LogisticMapConfig
>;

struct SourceConfig {
    std::string type;
    std::uint64_t output_bits{};
    SourceParameters parameters{LogisticMapConfig{}};
};

} // namespace bioentropy
