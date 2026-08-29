#include "bioentropy/conditioning/AsconXof128Conditioner.hpp"
#include "bioentropy/core/ExperimentConfig.hpp"
#include "bioentropy/core/ExperimentResult.hpp"
#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/io/ResultWriter.hpp"
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
#include <stdexcept>
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
        /*
         * Load and validate experiment configuration.
         */
        const auto config =
            bioentropy::ExperimentConfig::from_yaml(
                config_path
            );

        /*
         * Derive the deterministic 256-bit seed for this
         * experiment and replicate.
         */
        const auto derived_seed =
            bioentropy::SeedManager::derive(
                config.master_seed,
                config.experiment_id,
                config.replicate_id
            );

        const std::string derived_seed_hex =
            bioentropy::SeedManager::to_hex(
                derived_seed
            );

        /*
         * Construct the configured randomness source.
         */
        auto source =
            bioentropy::create_randomness_source(
                config.source,
                derived_seed
            );

        /*
         * output_bits is validated to be divisible by 8,
         * therefore the complete stream consists of bytes.
         */
        const std::uint64_t output_bytes =
            config.source.output_bits / 8U;

        /*
         * Protect the platform-dependent size_t conversion.
         */
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

        /*
         * The buffer contains only one chunk of the stream.
         * This keeps memory usage independent of the total
         * experiment output size.
         */
        const std::size_t chunk_capacity =
            static_cast<std::size_t>(
                std::min(
                    output_bytes,
                    config.execution.chunk_bytes
                )
            );

        std::vector<std::uint8_t>
            buffer(chunk_capacity);

        /*
         * Store only the first bytes for a reproducibility
         * preview displayed in the terminal.
         */
        std::vector<std::uint8_t>
            preview;

        preview.reserve(PREVIEW_BYTES);

        /*
         * RAW remains fully streaming.
         *
         * For Ascon-XOF128 we preserve the complete raw
         * source stream, condition it to exactly the same
         * number of bytes, and calculate final statistics
         * on the conditioned stream.
         */
        bioentropy::BitstreamStatisticsAccumulator
            statistics_accumulator;

        bioentropy::BitstreamStatisticsAccumulator
            raw_input_statistics_accumulator;

        const bool use_ascon_conditioning =
            config.conditioning.mode ==
            bioentropy::ConditioningMode::AsconXof128;

        std::vector<std::uint8_t>
            raw_stream;

        if (use_ascon_conditioning) {
            raw_stream.reserve(
                static_cast<std::size_t>(
                    output_bytes
                )
            );
        }

        std::uint64_t remaining_bytes =
            output_bytes;

        /*
         * Streaming source-generation loop.
         */
        while (remaining_bytes > 0) {
            const std::size_t current_chunk_size =
                static_cast<std::size_t>(
                    std::min<std::uint64_t>(
                        remaining_bytes,
                        static_cast<std::uint64_t>(
                            buffer.size()
                        )
                    )
                );

            std::span<std::uint8_t> chunk(
                buffer.data(),
                current_chunk_size
            );

            source->generate(chunk);

            if (use_ascon_conditioning) {
                /*
                 * Preserve source provenance before
                 * conditioning.
                 */
                raw_input_statistics_accumulator.update(
                    std::span<const std::uint8_t>(
                        chunk.data(),
                        chunk.size()
                    )
                );

                raw_stream.insert(
                    raw_stream.end(),
                    chunk.begin(),
                    chunk.end()
                );
            } else {
                /*
                 * Existing RAW behavior.
                 */
                statistics_accumulator.update(
                    std::span<const std::uint8_t>(
                        chunk.data(),
                        chunk.size()
                    )
                );

                if (
                    preview.size()
                    < PREVIEW_BYTES
                ) {
                    const std::size_t needed =
                        PREVIEW_BYTES
                        - preview.size();

                    const std::size_t copy_count =
                        std::min(
                            needed,
                            chunk.size()
                        );

                    preview.insert(
                        preview.end(),
                        chunk.begin(),
                        chunk.begin()
                            + static_cast<
                                std::ptrdiff_t
                            >(
                                copy_count
                            )
                    );
                }
            }

            remaining_bytes -=
                static_cast<std::uint64_t>(
                    current_chunk_size
                );
        }

        std::string
            pre_conditioning_sha256;

        if (use_ascon_conditioning) {
            const auto raw_statistics =
                raw_input_statistics_accumulator
                    .finalize();

            pre_conditioning_sha256 =
                raw_statistics.sha256;

            const bioentropy::
                AsconXof128Conditioner
                    conditioner;

            const auto conditioned =
                conditioner.condition(
                    std::span<
                        const std::uint8_t
                    >(
                        raw_stream.data(),
                        raw_stream.size()
                    ),
                    raw_stream.size()
                );

            statistics_accumulator.update(
                std::span<
                    const std::uint8_t
                >(
                    conditioned.data(),
                    conditioned.size()
                )
            );

            const std::size_t preview_size =
                std::min(
                    PREVIEW_BYTES,
                    conditioned.size()
                );

            preview.insert(
                preview.end(),
                conditioned.begin(),
                conditioned.begin()
                    + static_cast<
                        std::ptrdiff_t
                    >(
                        preview_size
                    )
            );
        }

        /*
         * Final statistics always describe the stream
         * actually evaluated by the experiment:
         *
         * RAW source output or conditioned XOF output.
         */
        const auto statistics =
            statistics_accumulator.finalize();

        /*
         * Build the persistent experiment result.
         */
        bioentropy::ExperimentResult result;

        result.experiment_id =
            config.experiment_id;

        result.replicate_id =
            config.replicate_id;

        result.source_name =
            std::string(
                source->name()
            );

        result.output_bits =
            config.source.output_bits;


        result.source_config =
            config.source;

        result.conditioning_config =
            config.conditioning;

        if (
            !pre_conditioning_sha256.empty()
        ) {
            result.pre_conditioning_sha256 =
                pre_conditioning_sha256;
        }

        result.chunk_bytes =
            config.execution.chunk_bytes;

        result.derived_seed =
            derived_seed_hex;

        result.statistics =
            statistics;

        /*
         * Persist machine-readable results.
         */
        const auto result_path =
            bioentropy::ResultWriter::write_json(
                result,
                "results/metrics"
            );

        /*
         * Human-readable console summary.
         */
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
            << "Conditioning  : "
            << (
                config.conditioning.mode ==
                bioentropy::
                    ConditioningMode::AsconXof128
                    ? "ascon_xof128"
                    : "raw"
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
            << derived_seed_hex
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
            << "Result file   : "
            << result_path.string()
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