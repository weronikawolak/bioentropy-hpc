#include "bioentropy/sources/RandomnessSourceFactory.hpp"

#include "bioentropy/sources/LogisticMapSource.hpp"

#include <memory>
#include <stdexcept>

namespace bioentropy {

std::unique_ptr<RandomnessSource>
create_randomness_source(
    const SourceConfig& config,
    const Seed256& seed
) {
    if (config.type == "logistic") {
        const auto* logistic =
            std::get_if<LogisticMapConfig>(
                &config.parameters
            );

        if (logistic == nullptr) {
            throw std::invalid_argument(
                "invalid parameters for logistic source"
            );
        }

        return std::make_unique<LogisticMapSource>(
            *logistic,
            seed
        );
    }

    throw std::invalid_argument(
        "unsupported randomness source: "
        + config.type
    );
}

} // namespace bioentropy
