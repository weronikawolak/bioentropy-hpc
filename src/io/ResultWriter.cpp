#include "bioentropy/io/ResultWriter.hpp"

#include "bioentropy/core/SourceConfig.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

#include <nlohmann/json.hpp>

namespace bioentropy {

namespace {

std::string logistic_initial_state_mode_to_string(
    LogisticInitialStateMode mode
) {
    switch (mode) {
        case LogisticInitialStateMode::Explicit:
            return "explicit";

        case LogisticInitialStateMode::DerivedFromSeed:
            return "derived_from_seed";
    }

    throw std::invalid_argument(
        "unknown logistic initial state mode"
    );
}

std::string logistic_extraction_to_string(
    LogisticExtractionMethod method
) {
    switch (method) {
        case LogisticExtractionMethod::Threshold:
            return "threshold";
    }

    throw std::invalid_argument(
        "unknown logistic extraction method"
    );
}

nlohmann::json source_parameters_to_json(
    const SourceConfig& source
) {
    if (source.type == "logistic") {
        const auto* config =
            std::get_if<LogisticMapConfig>(
                &source.parameters
            );

        if (config == nullptr) {
            throw std::invalid_argument(
                "invalid logistic source configuration"
            );
        }

        nlohmann::json initial_state = {
            {
                "mode",
                logistic_initial_state_mode_to_string(
                    config->initial_state_mode
                )
            }
        };

        if (config->x0.has_value()) {
            initial_state["x0"] =
                *config->x0;
        }

        return {
            {
                "r",
                config->r
            },
            {
                "burn_in",
                config->burn_in
            },
            {
                "extraction",
                logistic_extraction_to_string(
                    config->extraction
                )
            },
            {
                "initial_state",
                initial_state
            }
        };
    }

    if (source.type == "cellular_automaton") {
        const auto* config =
            std::get_if<CellularAutomatonConfig>(
                &source.parameters
            );

        if (config == nullptr) {
            throw std::invalid_argument(
                "invalid cellular automaton "
                "source configuration"
            );
        }

        return {
            {
                "rule",
                static_cast<std::uint16_t>(
                    config->rule
                )
            },
            {
                "cells",
                config->cells
            }
        };
    }


    if (source.type == "chacha20_reference") {
        const auto* config =
            std::get_if<
                ChaCha20ReferenceConfig
            >(
                &source.parameters
            );

        if (config == nullptr) {
            throw std::invalid_argument(
                "invalid ChaCha20 reference "
                "source configuration"
            );
        }

        return {
            {
                "initial_counter",
                config->initial_counter
            },
            {
                "key_derivation_domain",
                "BIOENTROPY-HPC-CHACHA20-KEY-v1"
            },
            {
                "nonce_derivation_domain",
                "BIOENTROPY-HPC-CHACHA20-NONCE-v1"
            },
            {
                "iv_layout",
                "counter64_le || nonce64"
            }
        };
    }


    if (source.type == "dna_sequence") {
        const auto* config =
            std::get_if<DNASequenceConfig>(
                &source.parameters
            );

        if (config == nullptr) {
            throw std::invalid_argument(
                "invalid DNA source configuration"
            );
        }

        return {
            {
                "sequence_file",
                config->sequence_file
            },
            {
                "assembly_accession",
                config->assembly_accession
            },
            {
                "sequence_accession",
                config->sequence_accession
            },
            {
                "window_start_nt",
                config->window_start_nt
            },
            {
                "window_length_nt",
                config->window_length_nt
            },
            {
                "mapping",
                "acgt_2bit"
            },
            {
                "mapping_definition",
                "A=00,C=01,G=10,T=11"
            },
            {
                "expected_sequence_sha256",
                config->expected_sequence_sha256
            },
            {
                "uses_experiment_seed",
                false
            }
        };
    }

    throw std::invalid_argument(
        "unsupported source type while "
        "serializing result: "
        + source.type
    );
}

} // namespace

std::filesystem::path
ResultWriter::write_json(
    const ExperimentResult& result,
    const std::filesystem::path& output_directory
) {
    if (result.source_config.type.empty()) {
        throw std::invalid_argument(
            "experiment result does not contain "
            "source configuration"
        );
    }

    if (
        result.source_config.type !=
        result.source_name
    ) {
        throw std::invalid_argument(
            "source name and source configuration "
            "type do not match"
        );
    }

    if (
        result.source_config.output_bits !=
        result.output_bits
    ) {
        throw std::invalid_argument(
            "source output_bits and experiment "
            "result output_bits do not match"
        );
    }

    std::filesystem::create_directories(
        output_directory
    );

    std::ostringstream filename;

    filename
        << result.experiment_id
        << "_rep"
        << std::setw(4)
        << std::setfill('0')
        << result.replicate_id
        << ".json";

    const std::filesystem::path output_path =
        output_directory /
        filename.str();

    const nlohmann::json document = {
        {
            "schema_version",
            1
        },
        {
            "experiment",
            {
                {
                    "id",
                    result.experiment_id
                },
                {
                    "replicate_id",
                    result.replicate_id
                }
            }
        },
        {
            "source",
            {
                {
                    "name",
                    result.source_name
                },
                {
                    "output_bits",
                    result.output_bits
                },
                {
                    "parameters",
                    source_parameters_to_json(
                        result.source_config
                    )
                }
            }
        },
        {
            "execution",
            {
                {
                    "chunk_bytes",
                    result.chunk_bytes
                }
            }
        },
        {
            "reproducibility",
            {
                {
                    "derived_seed",
                    result.derived_seed
                },
                {
                    "bitstream_sha256",
                    result.statistics.sha256
                }
            }
        },
        {
            "statistics",
            {
                {
                    "total_bytes",
                    result.statistics.total_bytes
                },
                {
                    "total_bits",
                    result.statistics.total_bits
                },
                {
                    "zeros",
                    result.statistics.zeros
                },
                {
                    "ones",
                    result.statistics.ones
                },
                {
                    "probability_zero",
                    result.statistics.probability_zero
                },
                {
                    "probability_one",
                    result.statistics.probability_one
                },
                {
                    "bias",
                    result.statistics.bias
                },
                {
                    "shannon_entropy",
                    result.statistics.shannon_entropy
                }
            }
        }
    };

    std::ofstream output_file(
        output_path,
        std::ios::out |
        std::ios::trunc
    );

    if (!output_file) {
        throw std::runtime_error(
            "failed to open result file: "
            + output_path.string()
        );
    }

    output_file
        << std::setw(2)
        << document
        << '\n';

    if (!output_file) {
        throw std::runtime_error(
            "failed to write result file: "
            + output_path.string()
        );
    }

    return output_path;
}

} // namespace bioentropy
