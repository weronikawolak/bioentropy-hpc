#pragma once

#include "bioentropy/core/SourceConfig.hpp"

#include <cstdint>
#include <filesystem>
#include <string>

namespace bioentropy {

struct ExperimentConfig {
    std::string experiment_id;
    std::uint32_t replicate_id;
    std::string master_seed;

    SourceConfig source;

    static ExperimentConfig from_yaml(
        const std::filesystem::path& config_path
    );

    void validate() const;
};

} // namespace bioentropy
