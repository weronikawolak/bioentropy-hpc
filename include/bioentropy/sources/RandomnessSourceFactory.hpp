#pragma once

#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <memory>

namespace bioentropy {

std::unique_ptr<RandomnessSource>
create_randomness_source(
    const SourceConfig& config,
    const Seed256& seed
);

} // namespace bioentropy
