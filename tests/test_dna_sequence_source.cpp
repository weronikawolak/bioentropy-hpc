#include "bioentropy/sources/DNASequenceSource.hpp"

#include <array>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace {

void require(
    bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "TEST FAILURE: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

} // namespace

int main() {
    const std::filesystem::path path =
        std::filesystem::temp_directory_path()
        / "bioentropy_dna_source_test.dna";

    {
        std::ofstream output(path);

        output
            << "ACGTTCGATGCATAGC\n";
    }

    bioentropy::DNASequenceConfig config{};

    config.sequence_file =
        path.string();

    config.assembly_accession =
        "TEST-ASSEMBLY";

    config.sequence_accession =
        "TEST-SEQUENCE";

    config.window_start_nt = 0;

    config.window_length_nt = 16;

    config.mapping =
        bioentropy::DNAMapping::ACGT2Bit;

    config.expected_sequence_sha256 =
        "390eb1e8f4984f38e796da8c83fbbe1a"
        "0325e12931e06f81b0a3b956d448bd76";

    bioentropy::DNASequenceSource source(
        config
    );

    std::array<std::uint8_t, 4>
        output{};

    source.generate(output);

    const std::array<std::uint8_t, 4>
        expected{
            0x1B,
            0xD8,
            0xE4,
            0xC9
        };

    require(
        output == expected,
        "DNA 2-bit mapping mismatch"
    );

    source.reset();

    std::array<std::uint8_t, 1>
        first{};

    std::array<std::uint8_t, 3>
        second{};

    source.generate(first);
    source.generate(second);

    require(
        first[0] == expected[0],
        "DNA chunk 1 mismatch"
    );

    for (
        std::size_t i = 0;
        i < second.size();
        ++i
    ) {
        require(
            second[i] ==
            expected[i + 1],
            "DNA chunk 2 mismatch"
        );
    }

    source.reset();

    std::array<std::uint8_t, 4>
        repeated{};

    source.generate(repeated);

    require(
        repeated == expected,
        "DNA reset reproducibility mismatch"
    );

    std::filesystem::remove(path);

    std::cout
        << "DNASequenceSource tests passed.\n";

    return EXIT_SUCCESS;
}
