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
    } else {
        throw std::invalid_argument(
            "unsupported source type: "
            + source.type
        );
    }
}

} // namespace bioentropy
