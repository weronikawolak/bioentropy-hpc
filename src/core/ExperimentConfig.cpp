#include "bioentropy/core/ExperimentConfig.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <stdexcept>
#include <string>

#include <yaml-cpp/yaml.h>

namespace bioentropy {

namespace {

bool is_valid_hex_seed(const std::string& seed) {
    if (seed.size() != 64) {
        return false;
    }

    return std::all_of(
        seed.begin(),
        seed.end(),
        [](unsigned char c) {
            return std::isxdigit(c) != 0;
        }
    );
}

ConditioningMode parse_conditioning_mode(
    const std::string& value
) {
    if (value == "raw") {
        return ConditioningMode::Raw;
    }

    if (value == "ascon_xof128") {
        return ConditioningMode::AsconXof128;
    }

    throw std::invalid_argument(
        "unsupported conditioning mode: "
        + value
    );
}

LogisticInitialStateMode parse_initial_state_mode(
    const std::string& value
) {
    if (value == "explicit") {
        return LogisticInitialStateMode::Explicit;
    }

    if (value == "derived_from_seed") {
        return LogisticInitialStateMode::DerivedFromSeed;
    }

    throw std::invalid_argument(
        "unsupported logistic initial_state.mode: "
        + value
    );
}

LogisticExtractionMethod parse_extraction_method(
    const std::string& value
) {
    if (value == "threshold") {
        return LogisticExtractionMethod::Threshold;
    }

    throw std::invalid_argument(
        "unsupported logistic extraction method: "
        + value
    );
}

LogisticArithmeticMode
parse_logistic_arithmetic_mode(
    const std::string& value
) {
    if (value == "float32") {
        return LogisticArithmeticMode::Float32;
    }

    if (value == "float64") {
        return LogisticArithmeticMode::Float64;
    }

    if (value == "fixed_q3_29") {
        return LogisticArithmeticMode::FixedQ3_29;
    }

    if (value == "mpfr_256") {
        return LogisticArithmeticMode::Mpfr256;
    }

    throw std::invalid_argument(
        "unsupported logistic arithmetic mode: "
        + value
    );
}

LogisticMapConfig parse_logistic_config(
    const YAML::Node& parameters
) {
    if (!parameters) {
        throw std::invalid_argument(
            "missing source.parameters section for logistic source"
        );
    }

    if (!parameters["r"]) {
        throw std::invalid_argument(
            "missing logistic parameter: r"
        );
    }

    LogisticMapConfig config{};

    config.r =
        parameters["r"].as<double>();

    config.r_literal =
        parameters["r"].Scalar();

    const YAML::Node arithmetic =
        parameters["arithmetic"];

    if (arithmetic) {
        if (!arithmetic["mode"]) {
            throw std::invalid_argument(
                "missing logistic arithmetic.mode"
            );
        }

        config.arithmetic_mode =
            parse_logistic_arithmetic_mode(
                arithmetic["mode"]
                    .as<std::string>()
            );
    }

    if (parameters["burn_in"]) {
        config.burn_in =
            parameters["burn_in"].as<std::uint64_t>();
    }

    if (parameters["extraction"]) {
        config.extraction =
            parse_extraction_method(
                parameters["extraction"].as<std::string>()
            );
    }

    const YAML::Node initial_state =
        parameters["initial_state"];

    if (!initial_state) {
        throw std::invalid_argument(
            "missing source.parameters.initial_state section"
        );
    }

    if (!initial_state["mode"]) {
        throw std::invalid_argument(
            "missing logistic initial_state.mode"
        );
    }

    config.initial_state_mode =
        parse_initial_state_mode(
            initial_state["mode"].as<std::string>()
        );

    if (
        config.initial_state_mode ==
        LogisticInitialStateMode::Explicit
    ) {
        if (!initial_state["x0"]) {
            throw std::invalid_argument(
                "explicit logistic initial state requires x0"
            );
        }

        config.x0 =
            initial_state["x0"].as<double>();

        config.x0_literal =
            initial_state["x0"].Scalar();
    }

    return config;
}

CellularAutomatonRule parse_ca_rule(
    std::uint16_t rule
) {
    if (rule == 30) {
        return CellularAutomatonRule::Rule30;
    }

    if (rule == 90) {
        return CellularAutomatonRule::Rule90;
    }

    throw std::invalid_argument(
        "cellular automaton rule must be 30 or 90"
    );
}

CellularAutomatonConfig parse_ca_config(
    const YAML::Node& parameters
) {
    if (!parameters) {
        throw std::invalid_argument(
            "missing source.parameters section "
            "for cellular automaton source"
        );
    }

    if (!parameters["rule"]) {
        throw std::invalid_argument(
            "missing cellular automaton parameter: rule"
        );
    }

    if (!parameters["cells"]) {
        throw std::invalid_argument(
            "missing cellular automaton parameter: cells"
        );
    }

    CellularAutomatonConfig config{};

    config.rule =
        parse_ca_rule(
            parameters["rule"].as<std::uint16_t>()
        );

    config.cells =
        parameters["cells"].as<std::uint64_t>();

    return config;
}


ChaCha20ReferenceConfig
parse_chacha20_reference_config(
    const YAML::Node& parameters
) {
    ChaCha20ReferenceConfig config{};

    if (
        parameters &&
        parameters["initial_counter"]
    ) {
        config.initial_counter =
            parameters["initial_counter"]
                .as<std::uint64_t>();
    }

    return config;
}



DNAMapping parse_dna_mapping(
    const std::string& value
) {
    if (value == "acgt_2bit") {
        return DNAMapping::ACGT2Bit;
    }

    throw std::invalid_argument(
        "unsupported DNA mapping: "
        + value
    );
}

DNASequenceConfig parse_dna_sequence_config(
    const YAML::Node& parameters
) {
    if (!parameters) {
        throw std::invalid_argument(
            "missing source.parameters section "
            "for DNA source"
        );
    }

    const char* required[] = {
        "sequence_file",
        "assembly_accession",
        "sequence_accession",
        "window_start_nt",
        "window_length_nt",
        "mapping"
    };

    for (const char* field : required) {
        if (!parameters[field]) {
            throw std::invalid_argument(
                std::string(
                    "missing DNA parameter: "
                ) + field
            );
        }
    }

    DNASequenceConfig config{};

    config.sequence_file =
        parameters["sequence_file"]
            .as<std::string>();

    config.assembly_accession =
        parameters["assembly_accession"]
            .as<std::string>();

    config.sequence_accession =
        parameters["sequence_accession"]
            .as<std::string>();

    config.window_start_nt =
        parameters["window_start_nt"]
            .as<std::uint64_t>();

    config.window_length_nt =
        parameters["window_length_nt"]
            .as<std::uint64_t>();

    config.mapping =
        parse_dna_mapping(
            parameters["mapping"]
                .as<std::string>()
        );

    if (
        parameters[
            "expected_sequence_sha256"
        ]
    ) {
        config.expected_sequence_sha256 =
            parameters[
                "expected_sequence_sha256"
            ].as<std::string>();
    }

    return config;
}


} // namespace

ExperimentConfig ExperimentConfig::from_yaml(
    const std::filesystem::path& config_path
) {
    if (!std::filesystem::exists(config_path)) {
        throw std::runtime_error(
            "Configuration file does not exist: "
            + config_path.string()
        );
    }

    YAML::Node root;

    try {
        root =
            YAML::LoadFile(
                config_path.string()
            );
    } catch (const YAML::Exception& exception) {
        throw std::runtime_error(
            "Failed to parse YAML configuration: "
            + std::string(exception.what())
        );
    }

    ExperimentConfig config{};

    try {
        const YAML::Node experiment =
            root["experiment"];

        const YAML::Node source =
            root["source"];

        const YAML::Node conditioning =
            root["conditioning"];

        const YAML::Node execution =
            root["execution"];

        if (!experiment) {
            throw std::runtime_error(
                "Missing required section: experiment"
            );
        }

        if (!source) {
            throw std::runtime_error(
                "Missing required section: source"
            );
        }

        config.experiment_id =
            experiment["id"].as<std::string>();

        config.replicate_id =
            experiment["replicate_id"]
                .as<std::uint32_t>();

        config.master_seed =
            experiment["master_seed"]
                .as<std::string>();

        config.source.type =
            source["type"].as<std::string>();

        config.source.output_bits =
            source["output_bits"]
                .as<std::uint64_t>();

        if (conditioning) {
            if (!conditioning["mode"]) {
                throw std::invalid_argument(
                    "missing conditioning.mode"
                );
            }

            config.conditioning.mode =
                parse_conditioning_mode(
                    conditioning["mode"]
                        .as<std::string>()
                );
        }

        if (
            execution &&
            execution["chunk_bytes"]
        ) {
            config.execution.chunk_bytes =
                execution["chunk_bytes"]
                    .as<std::uint64_t>();
        }

        if (config.source.type == "logistic") {
            config.source.parameters =
                parse_logistic_config(
                    source["parameters"]
                );
        } else if (
            config.source.type ==
            "cellular_automaton"
        ) {
            config.source.parameters =
                parse_ca_config(
                    source["parameters"]
                );
        } else if (
            config.source.type ==
            "chacha20_reference"
        ) {
            config.source.parameters =
                parse_chacha20_reference_config(
                    source["parameters"]
                );
        } else if (
            config.source.type ==
            "dna_sequence"
        ) {
            config.source.parameters =
                parse_dna_sequence_config(
                    source["parameters"]
                );
        } else {
            throw std::invalid_argument(
                "unsupported source type: "
                + config.source.type
            );
        }

    } catch (const YAML::Exception& exception) {
        throw std::runtime_error(
            "Invalid configuration structure: "
            + std::string(exception.what())
        );
    }

    config.validate();

    return config;
}

void ExperimentConfig::validate() const {
    if (experiment_id.empty()) {
        throw std::invalid_argument(
            "experiment.id must not be empty"
        );
    }

    if (!is_valid_hex_seed(master_seed)) {
        throw std::invalid_argument(
            "experiment.master_seed must contain exactly "
            "64 hexadecimal characters (256 bits)"
        );
    }

    if (source.type.empty()) {
        throw std::invalid_argument(
            "source.type must not be empty"
        );
    }

    if (source.output_bits == 0) {
        throw std::invalid_argument(
            "source.output_bits must be greater than zero"
        );
    }

    if (source.output_bits % 8 != 0) {
        throw std::invalid_argument(
            "source.output_bits must be divisible by 8"
        );
    }

    if (execution.chunk_bytes == 0) {
        throw std::invalid_argument(
            "execution.chunk_bytes must be greater than zero"
        );
    }

    if (source.type == "logistic") {
        const auto* logistic =
            std::get_if<LogisticMapConfig>(
                &source.parameters
            );

        if (logistic == nullptr) {
            throw std::invalid_argument(
                "logistic source has invalid parameters"
            );
        }

        if (
            !std::isfinite(logistic->r) ||
            logistic->r <= 0.0 ||
            logistic->r > 4.0
        ) {
            throw std::invalid_argument(
                "logistic parameter r must satisfy 0 < r <= 4"
            );
        }

        if (
            logistic->initial_state_mode ==
            LogisticInitialStateMode::Explicit
        ) {
            if (!logistic->x0.has_value()) {
                throw std::invalid_argument(
                    "explicit logistic initial state requires x0"
                );
            }

            if (
                !std::isfinite(*logistic->x0) ||
                *logistic->x0 <= 0.0 ||
                *logistic->x0 >= 1.0
            ) {
                throw std::invalid_argument(
                    "logistic x0 must satisfy 0 < x0 < 1"
                );
            }
        }
    } else if (
        source.type ==
        "cellular_automaton"
    ) {
        const auto* ca =
            std::get_if<CellularAutomatonConfig>(
                &source.parameters
            );

        if (ca == nullptr) {
            throw std::invalid_argument(
                "cellular automaton has invalid parameters"
            );
        }

        if (
            ca->rule != CellularAutomatonRule::Rule30 &&
            ca->rule != CellularAutomatonRule::Rule90
        ) {
            throw std::invalid_argument(
                "cellular automaton rule must be 30 or 90"
            );
        }

        if (
            ca->cells != 256 &&
            ca->cells != 1024
        ) {
            throw std::invalid_argument(
                "cellular automaton cells must be 256 or 1024"
            );
        }

        if (ca->cells % 8 != 0) {
            throw std::invalid_argument(
                "cellular automaton cell count "
                "must be divisible by 8"
            );
        }
    } else if (
        source.type ==
        "chacha20_reference"
    ) {
        const auto* chacha =
            std::get_if<
                ChaCha20ReferenceConfig
            >(
                &source.parameters
            );

        if (chacha == nullptr) {
            throw std::invalid_argument(
                "ChaCha20 reference source "
                "has invalid parameters"
            );
        }
    } else if (
        source.type ==
        "dna_sequence"
    ) {
        const auto* dna =
            std::get_if<DNASequenceConfig>(
                &source.parameters
            );

        if (dna == nullptr) {
            throw std::invalid_argument(
                "DNA source has invalid parameters"
            );
        }

        if (dna->sequence_file.empty()) {
            throw std::invalid_argument(
                "DNA sequence_file must not be empty"
            );
        }

        if (dna->assembly_accession.empty()) {
            throw std::invalid_argument(
                "DNA assembly_accession "
                "must not be empty"
            );
        }

        if (dna->sequence_accession.empty()) {
            throw std::invalid_argument(
                "DNA sequence_accession "
                "must not be empty"
            );
        }

        if (dna->window_length_nt == 0) {
            throw std::invalid_argument(
                "DNA window_length_nt "
                "must be greater than zero"
            );
        }

        if (dna->window_length_nt % 4 != 0) {
            throw std::invalid_argument(
                "DNA window_length_nt must "
                "be divisible by 4"
            );
        }

        if (
            dna->window_length_nt >
            UINT64_MAX / 2
        ) {
            throw std::invalid_argument(
                "DNA window_length_nt is too large"
            );
        }

        const std::uint64_t expected_bits =
            dna->window_length_nt * 2;

        if (
            source.output_bits !=
            expected_bits
        ) {
            throw std::invalid_argument(
                "DNA output_bits must equal "
                "2 * window_length_nt"
            );
        }

        if (
            !dna->expected_sequence_sha256.empty() &&
            dna->expected_sequence_sha256.size() != 64
        ) {
            throw std::invalid_argument(
                "DNA expected_sequence_sha256 "
                "must contain 64 hexadecimal "
                "characters"
            );
        }
    } else {
        throw std::invalid_argument(
            "unsupported source type: "
            + source.type
        );
    }
}

} // namespace bioentropy
