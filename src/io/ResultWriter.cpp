#include "bioentropy/io/ResultWriter.hpp"

#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>
#include <sstream>
#include <nlohmann/json.hpp>

namespace bioentropy {

namespace {

std::string build_filename(
    const std::string& experiment_id,
    std::uint32_t replicate_id
) {
    std::ostringstream stream;

    stream
        << experiment_id
        << "_rep"
        << std::setw(4)
        << std::setfill('0')
        << replicate_id
        << ".json";

    return stream.str();
}

} // namespace

std::filesystem::path ResultWriter::write_json(
    const ExperimentResult& result,
    const std::filesystem::path& output_directory
) {
    std::filesystem::create_directories(
        output_directory
    );

    const std::filesystem::path output_path =
        output_directory
        /
        build_filename(
            result.experiment_id,
            result.replicate_id
        );

    nlohmann::json document;

    document["schema_version"] = 1;

    document["experiment"] = {
        {"id", result.experiment_id},
        {"replicate_id", result.replicate_id}
    };

    document["source"] = {
        {"name", result.source_name},
        {"output_bits", result.output_bits}
    };

    document["execution"] = {
        {"chunk_bytes", result.chunk_bytes}
    };

    document["reproducibility"] = {
        {"derived_seed", result.derived_seed},
        {"bitstream_sha256", result.statistics.sha256}
    };

    document["statistics"] = {
        {"total_bytes", result.statistics.total_bytes},
        {"total_bits", result.statistics.total_bits},
        {"zeros", result.statistics.zeros},
        {"ones", result.statistics.ones},
        {"probability_zero", result.statistics.probability_zero},
        {"probability_one", result.statistics.probability_one},
        {"bias", result.statistics.bias},
        {"shannon_entropy", result.statistics.shannon_entropy}
    };

    std::ofstream output(output_path);

    if (!output) {
        throw std::runtime_error(
            "failed to open result file: "
            + output_path.string()
        );
    }

    output
        << std::setw(2)
        << document
        << '\n';

    if (!output) {
        throw std::runtime_error(
            "failed to write result file: "
            + output_path.string()
        );
    }

    return output_path;
}

} // namespace bioentropy
