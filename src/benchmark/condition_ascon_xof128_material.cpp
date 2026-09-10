#include "bioentropy/conditioning/AsconXof128Conditioner.hpp"

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

int main(
    int argc,
    char* argv[]
) {
    if (argc != 4) {
        std::cerr
            << "Usage: "
            << argv[0]
            << " <input.bin>"
            << " <output.bin>"
            << " <output_bytes>\n";

        return 2;
    }

    try {
        const std::string input_path =
            argv[1];

        const std::string output_path =
            argv[2];

        const std::size_t output_bytes =
            static_cast<std::size_t>(
                std::stoull(argv[3])
            );

        std::ifstream input(
            input_path,
            std::ios::binary
        );

        if (!input) {
            throw std::runtime_error(
                "cannot open input file"
            );
        }

        const std::vector<std::uint8_t>
            data{
                std::istreambuf_iterator<char>(
                    input
                ),
                std::istreambuf_iterator<char>()
            };

        const bioentropy::
            AsconXof128Conditioner conditioner;

        const auto conditioned =
            conditioner.condition(
                data,
                output_bytes
            );

        if (
            conditioned.size()
            != output_bytes
        ) {
            throw std::runtime_error(
                "unexpected conditioned length"
            );
        }

        std::ofstream output(
            output_path,
            std::ios::binary
            | std::ios::trunc
        );

        if (!output) {
            throw std::runtime_error(
                "cannot open output file"
            );
        }

        output.write(
            reinterpret_cast<const char*>(
                conditioned.data()
            ),
            static_cast<std::streamsize>(
                conditioned.size()
            )
        );

        if (!output) {
            throw std::runtime_error(
                "failed to write output"
            );
        }

        std::cout
            << "input_bytes="
            << data.size()
            << '\n'
            << "output_bytes="
            << conditioned.size()
            << '\n';

        return 0;
    }
    catch (
        const std::exception& error
    ) {
        std::cerr
            << "ERROR: "
            << error.what()
            << '\n';

        return 1;
    }
}
