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

enum class CellularAutomatonRule : std::uint16_t {
    Rule30 = 30,
    Rule90 = 90
};

struct CellularAutomatonConfig {
    CellularAutomatonRule rule{
        CellularAutomatonRule::Rule30
    };

    std::uint64_t cells{256};
};

struct ChaCha20ReferenceConfig {
    std::uint64_t initial_counter{0};
};

using SourceParameters = std::variant<
    LogisticMapConfig,
    CellularAutomatonConfig,
    ChaCha20ReferenceConfig
>;

struct SourceConfig {
    std::string type;

    std::uint64_t output_bits{};

    SourceParameters parameters{
        LogisticMapConfig{}
    };
};

} // namespace bioentropy
