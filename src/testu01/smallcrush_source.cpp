#include "bioentropy/core/ExperimentConfig.hpp"
#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"
#include "bioentropy/sources/RandomnessSourceFactory.hpp"

extern "C" {
#include <testu01/bbattery.h>
#include <testu01/unif01.h>
}

#include <array>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {

constexpr std::size_t BUFFER_BYTES =
    1024U * 1024U;

static_assert(
    BUFFER_BYTES % 4U == 0U
);

bioentropy::RandomnessSource*
    active_source = nullptr;

std::array<
    std::uint8_t,
    BUFFER_BYTES
> buffer{};

std::size_t buffer_offset =
    BUFFER_BYTES;

std::uint64_t words_returned = 0;


void refill_buffer()
{
    if (active_source == nullptr) {
        throw std::runtime_error(
            "TestU01 source not initialized"
        );
    }

    active_source->generate(
        std::span<std::uint8_t>(
            buffer.data(),
            buffer.size()
        )
    );

    buffer_offset = 0;
}


unsigned int next_testu01_word()
{
    if (
        buffer_offset + 4U
        > buffer.size()
    ) {
        refill_buffer();
    }

    /*
     * Preserve stream bit order:
     *
     * byte 0 -> bits 31..24
     * byte 1 -> bits 23..16
     * byte 2 -> bits 15..8
     * byte 3 -> bits 7..0
     */
    const std::uint32_t word =
        (
            static_cast<std::uint32_t>(
                buffer[buffer_offset]
            ) << 24U
        )
        |
        (
            static_cast<std::uint32_t>(
                buffer[buffer_offset + 1U]
            ) << 16U
        )
        |
        (
            static_cast<std::uint32_t>(
                buffer[buffer_offset + 2U]
            ) << 8U
        )
        |
        static_cast<std::uint32_t>(
            buffer[buffer_offset + 3U]
        );

    buffer_offset += 4U;
    ++words_returned;

    return static_cast<unsigned int>(
        word
    );
}


void print_usage(
    const char* program
)
{
    std::cerr
        << "Usage:\n  "
        << program
        << " --config <experiment.yaml>\n";
}

} // namespace


int main(
    int argc,
    char** argv
)
{
    try {
        if (
            argc != 3
            || std::string(argv[1])
                != "--config"
        ) {
            print_usage(argv[0]);
            return 1;
        }

        const auto config =
            bioentropy::ExperimentConfig::
                from_yaml(
                    argv[2]
                );

        /*
         * A frozen DNA window is finite.
         *
         * SmallCrush requires far more data than one
         * genomic window, therefore we explicitly refuse
         * to cycle/repeat DNA data.
         */
        if (
            config.source.type
            == "dna_sequence"
        ) {
            throw std::invalid_argument(
                "SmallCrush adapter refuses finite "
                "DNA windows; repeating a genomic "
                "window would create an artificial "
                "periodicity"
            );
        }

        const auto seed =
            bioentropy::SeedManager::derive(
                config.master_seed,
                config.experiment_id,
                config.replicate_id
            );

        const auto seed_hex =
            bioentropy::SeedManager::to_hex(
                seed
            );

        auto source =
            bioentropy::
                create_randomness_source(
                    config.source,
                    seed
                );

        active_source =
            source.get();

        buffer_offset =
            buffer.size();

        words_returned = 0;

        std::string name =
            "BioEntropy/"
            + std::string(
                source->name()
            );

        std::cout
            << "BioEntropy TestU01 adapter\n"
            << "--------------------------\n"
            << "Source        : "
            << source->name()
            << '\n'
            << "Replicate ID  : "
            << config.replicate_id
            << '\n'
            << "Derived seed  : "
            << seed_hex
            << '\n'
            << "Word packing  : "
            << "4 consecutive bytes, "
            << "big-endian/MSB-first\n"
            << "Buffer bytes  : "
            << buffer.size()
            << '\n'
            << "Battery       : SmallCrush\n"
            << std::flush;

        /*
         * TestU01 permits only one external generator
         * of this type at a time.
         */
        unif01_Gen* generator =
            unif01_CreateExternGenBits(
                name.data(),
                &next_testu01_word
            );

        if (generator == nullptr) {
            throw std::runtime_error(
                "unif01_CreateExternGenBits failed"
            );
        }

        bbattery_SmallCrush(
            generator
        );

        unif01_DeleteExternGenBits(
            generator
        );

        active_source = nullptr;

        std::cout
            << "\nBioEntropy adapter summary\n"
            << "--------------------------\n"
            << "32-bit words consumed : "
            << words_returned
            << '\n'
            << "bytes consumed        : "
            << words_returned * 4ULL
            << '\n';

        return 0;
    }
    catch (
        const std::exception& exception
    ) {
        active_source = nullptr;

        std::cerr
            << "ERROR: "
            << exception.what()
            << '\n';

        return 1;
    }
}
