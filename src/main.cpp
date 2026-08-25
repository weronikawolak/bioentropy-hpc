#include "bioentropy/core/ExperimentConfig.hpp"
#include "bioentropy/core/SeedManager.hpp"

#include <exception>
#include <filesystem>
#include <iostream>
#include <string>

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

        std::cout << "BioEntropy HPC Framework\n";
        std::cout << "------------------------\n";
        std::cout << "Experiment ID : "
                  << config.experiment_id << '\n';

        std::cout << "Replicate ID  : "
                  << config.replicate_id << '\n';

        std::cout << "Source        : "
                  << config.source.type << '\n';

        std::cout << "Output bits   : "
                  << config.source.output_bits << '\n';

        std::cout << "Derived seed  : "
                  << bioentropy::SeedManager::to_hex(
                         derived_seed
                     )
                  << '\n';

        std::cout
            << "\nConfiguration validated successfully.\n";

    } catch (const std::exception& exception) {
        std::cerr
            << "ERROR: "
            << exception.what()
            << '\n';

        return 2;
    }

    return 0;
}
