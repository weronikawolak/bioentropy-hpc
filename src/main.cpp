#include "bioentropy/core/ExperimentConfig.hpp"
#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/metrics/BitstreamStatistics.hpp"
#include "bioentropy/sources/RandomnessSourceFactory.hpp"

#include <algorithm>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <limits>
#include <span>
#include <string>
#include <vector>

namespace {

constexpr std::size_t PREVIEW_BYTES = 16;

void print_usage(const char* program_name) {
    std::cout
        << "BioEntropy HPC Framework\n\n"
        << "Usage:\n"
        << "  " << program_name
        << " --config <path>\n\n"
        << "Options:\n"
        << "  --config <path>   Path to experiment YAML configuration\n"
        << "  --help            Show this help message\n";
}

void print_preview(
    const std::vector<std::uint8_t>& data
) {
    std::cout
        << std::hex
        << std::setfill('0');

    for (const auto byte : data) {
        std::cout
            << std::setw(2)
            << static_cast<unsigned int>(byte);
    }

    std::cout
        << std::dec
        << '\n';
}

} // namespace

int main(int argc, char* argv[]) {
    if (
        argc == 2 &&
        std::string(argv[1]) == "--help"
    ) {
        print_usage(argv[0]);
        return 0;
    }

    if (
        argc != 3 ||
        std::string(argv[1]) != "--config"
    ) {
        print_usage(argv[0]);
        return 1;
    }

    const std::filesystem::path config_path =
        argv[2];

    try {
        const auto config =
            bioentropy::ExperimentConfig::from_yaml(
                config_path
            );

        const auto derived_seed =
            bioentropy::SeedManager::derive(
                config.master_seed,
                config.experiment_id,
                config.replicate_id
            );

        auto source =
            bioentropy::create_randomness_source(
                config.source,
                derived_seed
            );

        const std::uint64_t output_bytes =
            config.source.output_bits / 8U;

        if (
            config.execution.chunk_bytes >
            static_cast<std::uint64_t>(
                std::numeric_limits<std::size_t>::max()
            )
        ) {
            throw std::runtime_error(
                "execution.chunk_bytes exceeds platform size limit"
            );
        }

        const std::size_t chunk_capacity =
            static_cast<std::size_t>(
                std::min(
                    output_bytes,
                    config.execution.chunk_bytes
                )
            );

        std::vector<std::uint8_t>
            buffer(chunk_capacity);

        std::vector<std::uint8_t>
            preview;

        preview.reserve(PREVIEW_BYTES);

        bioentropy::BitstreamStatisticsAccumulator
            statistics_accumulator;

        std::uint64_t remaining_bytes =
            output_bytes;

        while (remaining_bytes > 0) {
            const std::size_t current_chunk_size =
                static_cast<std::size_t>(
                    std::min<std::uint64_t>(
                        remaining_bytes,
                        buffer.size()
                    )
                );

            std::span<std::uint8_t> chunk(
                buffer.data(),
                current_chunk_size
            );

            source->generate(chunk);

            statistics_accumulator.update(
                std::span<const std::uint8_t>(
                    chunk.data(),
                    chunk.size()
                )
            );

            if (preview.size() < PREVIEW_BYTES) {
                const std::size_t needed =
                    PREVIEW_BYTES - preview.size();

                const std::size_t copy_count =
                    std::min(
                        needed,
                        chunk.size()
                    );

                preview.insert(
                    preview.end(),
                    chunk.begin(),
                    chunk.begin()
                    + static_cast<std::ptrdiff_t>(
                        copy_count
                    )
                );
            }

            remaining_bytes -=
                static_cast<std::uint64_t>(
                    current_chunk_size
                );
        }

        const auto statistics =
            statistics_accumulator.finalize();

        std::cout
            << "BioEntropy HPC Framework\n";

        std::cout
            << "------------------------\n";

        std::cout
            << "Experiment ID : "
            << config.experiment_id
            << '\n';

        std::cout
            << "Replicate ID  : "
            << config.replicate_id
            << '\n';

        std::cout
            << "Source        : "
            << source->name()
            << '\n';

        std::cout
            << "Deterministic : "
            << (
                source->deterministic()
                    ? "yes"
                    : "no"
            )
            << '\n';

        std::cout
            << "Output bits   : "
            << config.source.output_bits
            << '\n';

        std::cout
            << "Chunk bytes   : "
            << config.execution.chunk_bytes
            << '\n';

        std::cout
            << "Derived seed  : "
            << bioentropy::SeedManager::to_hex(
                derived_seed
            )
            << '\n';

        std::cout
            << "Preview       : ";

        print_preview(preview);

        std::cout
            << "\nBasic statistics\n"
            << "----------------\n";

        std::cout
            << "Bytes         : "
            << statistics.total_bytes
            << '\n';

        std::cout
            << "Bits          : "
            << statistics.total_bits
            << '\n';

        std::cout
            << "Zeros         : "
            << statistics.zeros
            << '\n';

        std::cout
            << "Ones          : "
            << statistics.ones
            << '\n';

        std::cout
            << std::fixed
            << std::setprecision(10);

        std::cout
            << "P(0)          : "
            << statistics.probability_zero
            << '\n';

        std::cout
            << "P(1)          : "
            << statistics.probability_one
            << '\n';

        std::cout
            << "Bias          : "
            << statistics.bias
            << '\n';

        std::cout
            << "Shannon H     : "
            << statistics.shannon_entropy
            << " bits/bit\n";

        std::cout
            << "SHA-256       : "
            << statistics.sha256
            << '\n';

        std::cout
            << "\nExperiment completed successfully.\n";

    } catch (const std::exception& exception) {
        std::cerr
            << "ERROR: "
            << exception.what()
            << '\n';

        return 2;
    }

    return 0;
}
