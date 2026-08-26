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
        "unsupported logistic initial_state.mode: " + value
    );
}

LogisticExtractionMethod parse_extraction_method(
    const std::string& value
) {
    if (value == "threshold") {
        return LogisticExtractionMethod::Threshold;
    }

    throw std::invalid_argument(
        "unsupported logistic extraction method: " + value
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

    LogisticMapConfig config{};

    config.r =
        parameters["r"].as<double>();

    config.burn_in =
        parameters["burn_in"].as<std::uint64_t>();

    config.extraction =
        parse_extraction_method(
            parameters["extraction"].as<std::string>()
        );

    const YAML::Node initial_state =
        parameters["initial_state"];

    if (!initial_state) {
        throw std::invalid_argument(
            "missing source.parameters.initial_state section"
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
    }
}

} // namespace bioentropy
