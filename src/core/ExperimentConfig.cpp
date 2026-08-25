#include "bioentropy/core/ExperimentConfig.hpp"

#include <algorithm>
#include <cctype>
#include <stdexcept>

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
        root = YAML::LoadFile(config_path.string());
    } catch (const YAML::Exception& exception) {
        throw std::runtime_error(
            "Failed to parse YAML configuration: "
            + std::string(exception.what())
        );
    }

    ExperimentConfig config{};

    try {
        const YAML::Node experiment = root["experiment"];
        const YAML::Node source = root["source"];

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
            experiment["replicate_id"].as<std::uint32_t>();

        config.master_seed =
            experiment["master_seed"].as<std::string>();

        config.source.type =
            source["type"].as<std::string>();

        config.source.output_bits =
            source["output_bits"].as<std::uint64_t>();

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

    if (!is_valid_hex_seed(master_seed)) {
        throw std::invalid_argument(
            "experiment.master_seed must contain exactly "
            "64 hexadecimal characters (256 bits)"
        );
    }
}

} // namespace bioentropy
