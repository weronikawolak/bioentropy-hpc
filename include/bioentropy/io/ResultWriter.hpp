#pragma once

#include "bioentropy/core/ExperimentResult.hpp"

#include <filesystem>

namespace bioentropy {

class ResultWriter {
public:
    static std::filesystem::path write_json(
        const ExperimentResult& result,
        const std::filesystem::path& output_directory
    );
};

} // namespace bioentropy
