#include "bioentropy/sources/RandomnessSourceFactory.hpp"

#include "bioentropy/sources/CellularAutomatonSource.hpp"
#include "bioentropy/sources/ChaCha20ReferenceSource.hpp"
#include "bioentropy/sources/DNASequenceSource.hpp"
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

        return std::make_unique<
            LogisticMapSource
        >(
            *logistic,
            seed
        );
    }

    if (
        config.type ==
        "cellular_automaton"
    ) {
        const auto* cellular =
            std::get_if<
                CellularAutomatonConfig
            >(
                &config.parameters
            );

        if (cellular == nullptr) {
            throw std::invalid_argument(
                "invalid parameters for "
                "cellular automaton source"
            );
        }

        return std::make_unique<
            CellularAutomatonSource
        >(
            *cellular,
            seed
        );
    }

    if (
        config.type ==
        "chacha20_reference"
    ) {
        const auto* chacha =
            std::get_if<
                ChaCha20ReferenceConfig
            >(
                &config.parameters
            );

        if (chacha == nullptr) {
            throw std::invalid_argument(
                "invalid parameters for "
                "ChaCha20 reference source"
            );
        }

        return std::make_unique<
            ChaCha20ReferenceSource
        >(
            *chacha,
            seed
        );
    }


    if (
        config.type ==
        "dna_sequence"
    ) {
        const auto* dna =
            std::get_if<DNASequenceConfig>(
                &config.parameters
            );

        if (dna == nullptr) {
            throw std::invalid_argument(
                "invalid parameters for "
                "DNA sequence source"
            );
        }

        return std::make_unique<
            DNASequenceSource
        >(
            *dna
        );
    }

    throw std::invalid_argument(
        "unsupported randomness source: "
        + config.type
    );
}

} // namespace bioentropy
