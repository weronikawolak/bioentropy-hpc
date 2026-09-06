#include "bioentropy/core/ExperimentConfig.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "FAILED: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

std::filesystem::path write_config(
    const std::string& name,
    const std::string& conditioning_block
) {
    const auto path =
        std::filesystem::temp_directory_path()
        / name;

    std::ofstream output(path);

    if (!output) {
        throw std::runtime_error(
            "failed to create temporary YAML"
        );
    }

    output
        << "experiment:\n"
        << "  id: conditioning-test\n"
        << "  replicate_id: 0\n"
        << "  master_seed: "
        << "0123456789abcdef"
        << "0123456789abcdef"
        << "0123456789abcdef"
        << "0123456789abcdef\n"
        << "source:\n"
        << "  type: chacha20_reference\n"
        << "  output_bits: 1024\n"
        << "  parameters:\n"
        << "    initial_counter: 0\n";

    output << conditioning_block;

    output
        << "execution:\n"
        << "  chunk_bytes: 64\n";

    output.close();

    return path;
}

void test_default_is_raw() {
    const auto path =
        write_config(
            "bioentropy-conditioning-default.yaml",
            ""
        );

    const auto config =
        bioentropy::
        ExperimentConfig::from_yaml(path);

    require(
        config.conditioning.mode
            == bioentropy::
               ConditioningMode::Raw,
        "missing conditioning section "
        "must default to raw"
    );

    std::filesystem::remove(path);
}

void test_ascon_xof128() {
    const auto path =
        write_config(
            "bioentropy-conditioning-ascon.yaml",
            "conditioning:\n"
            "  mode: ascon_xof128\n"
        );

    const auto config =
        bioentropy::
        ExperimentConfig::from_yaml(path);

    require(
        config.conditioning.mode
            == bioentropy::
               ConditioningMode::AsconXof128,
        "ascon_xof128 was not parsed"
    );

    std::filesystem::remove(path);
}

void test_invalid_mode_rejected() {
    const auto path =
        write_config(
            "bioentropy-conditioning-invalid.yaml",
            "conditioning:\n"
            "  mode: definitely_not_valid\n"
        );

    bool rejected = false;

    try {
        static_cast<void>(
            bioentropy::
            ExperimentConfig::from_yaml(path)
        );
    } catch (
        const std::exception&
    ) {
        rejected = true;
    }

    std::filesystem::remove(path);

    require(
        rejected,
        "invalid conditioning mode "
        "was not rejected"
    );
}

}  // namespace

int main() {
    test_default_is_raw();
    test_ascon_xof128();
    test_invalid_mode_rejected();

    std::cout
        << "Experiment conditioning "
        << "configuration tests passed\n";

    return EXIT_SUCCESS;
}
