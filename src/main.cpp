#include "bioentropy/core/ExperimentConfig.hpp"
#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/sources/RandomnessSourceFactory.hpp"

#include <algorithm>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace {

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
    const std::vector<std::uint8_t>& data,
    std::size_t max_bytes
) {
    const std::size_t count =
        std::min(data.size(), max_bytes);

    std::cout << std::hex << std::setfill('0');

    for (std::size_t i = 0; i < count; ++i) {
        std::cout
            << std::setw(2)
            << static_cast<unsigned int>(data[i]);
    }

    std::cout << std::dec << '\n';
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        print_usage(argv[0]);
        return 0;
    }

    if (argc != 3 || std::string(argv[1]) != "--config") {
        print_usage(argv[0]);
        return 1;
    }

    const std::filesystem::path config_path = argv[2];

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

        const std::size_t output_bytes =
            static_cast<std::size_t>(
                config.source.output_bits / 8
            );

        std::vector<std::uint8_t> output(
            output_bytes
        );

        source->generate(output);

        std::cout << "BioEntropy HPC Framework\n";
        std::cout << "------------------------\n";

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
            << (source->deterministic() ? "yes" : "no")
            << '\n';

        std::cout
            << "Output bits   : "
            << config.source.output_bits
            << '\n';

        std::cout
            << "Derived seed  : "
            << bioentropy::SeedManager::to_hex(
                   derived_seed
               )
            << '\n';

        std::cout
            << "Preview       : ";

        print_preview(output, 16);

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
