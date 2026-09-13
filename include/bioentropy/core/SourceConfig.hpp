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

enum class Chen4DExtractionMethod {
    ThresholdPerCoordinate
};

struct Chen4DDcsConfig {
    double r{5.0};

    double x0{0.1};
    double y0{0.2};
    double z0{0.3};
    double w0{0.4};

    std::uint64_t burn_in{1000};

    Chen4DExtractionMethod extraction{
        Chen4DExtractionMethod::ThresholdPerCoordinate
    };

    double threshold{0.5};
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

struct CtrDrbgAes256ReferenceConfig {
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
    Chen4DDcsConfig,
    CellularAutomatonConfig,
    ChaCha20ReferenceConfig,
    DNASequenceConfig,
    CtrDrbgAes256ReferenceConfig
>;

struct SourceConfig {
    std::string type;

    std::uint64_t output_bits{};

    SourceParameters parameters{
        LogisticMapConfig{}
    };
};

} // namespace bioentropy
