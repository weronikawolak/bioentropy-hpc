#pragma once

#include "bioentropy/core/SourceConfig.hpp"

#include <cstdint>
#include <filesystem>
#include <string>

namespace bioentropy {

enum class ConditioningMode {
    Raw,
    AsconXof128
};

struct ConditioningConfig {
    ConditioningMode mode{
        ConditioningMode::Raw
    };
};


struct ExecutionConfig {
    std::uint64_t chunk_bytes{1'048'576};
};

struct ExperimentConfig {
    std::string experiment_id;
    std::uint32_t replicate_id;
    std::string master_seed;

    SourceConfig source;
    ConditioningConfig conditioning;
    ExecutionConfig execution;

    static ExperimentConfig from_yaml(
        const std::filesystem::path& config_path
    );

    void validate() const;
};

} // namespace bioentropy
