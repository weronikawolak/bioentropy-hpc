#pragma once

#include "bioentropy/metrics/BitstreamStatistics.hpp"

#include <cstdint>
#include <string>

namespace bioentropy {

struct ExperimentResult {
    std::string experiment_id;
    std::uint32_t replicate_id{};

    std::string source_name;

    std::uint64_t output_bits{};
    std::uint64_t chunk_bytes{};

    std::string derived_seed;

    BitstreamStatistics statistics;
};

} // namespace bioentropy
