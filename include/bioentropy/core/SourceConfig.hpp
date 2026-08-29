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

enum class LogisticArithmeticMode {
    Float32,
    Float64,
    FixedQ3_29,
    Mpfr256
};

struct LogisticMapConfig {
    double r{};

    /*
     * Original decimal representation from YAML.
     *
     * Used by arbitrary-precision backends so that
     * parameters are not first quantized to binary64.
     */
    std::string r_literal;

    LogisticArithmeticMode arithmetic_mode{
        LogisticArithmeticMode::Float64
    };

    LogisticInitialStateMode initial_state_mode{
        LogisticInitialStateMode::DerivedFromSeed
    };

    std::optional<double> x0;
    std::optional<std::string> x0_literal;

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

enum class DNAMapping {
    ACGT2Bit
};

struct DNASequenceConfig {
    std::string sequence_file;

    std::string assembly_accession;
    std::string sequence_accession;

    std::uint64_t window_start_nt{0};
    std::uint64_t window_length_nt{0};

    DNAMapping mapping{
        DNAMapping::ACGT2Bit
    };

    std::string expected_sequence_sha256;
};

using SourceParameters = std::variant<
    LogisticMapConfig,
    CellularAutomatonConfig,
    ChaCha20ReferenceConfig,
    DNASequenceConfig
>;

struct SourceConfig {
    std::string type;

    std::uint64_t output_bits{};

    SourceParameters parameters{
        LogisticMapConfig{}
    };
};

} // namespace bioentropy
