#include "bioentropy/conditioning/AsconXof128Conditioner.hpp"

#include "ascon_xof128_variable.h"

#include <stdexcept>

namespace bioentropy {

std::vector<std::uint8_t>
AsconXof128Conditioner::condition(
    std::span<const std::uint8_t> input,
    const std::size_t output_bytes
) const {
    std::vector<std::uint8_t> output(
        output_bytes
    );

    condition(
        input,
        std::span<std::uint8_t>(output)
    );

    return output;
}

void AsconXof128Conditioner::condition(
    std::span<const std::uint8_t> input,
    std::span<std::uint8_t> output
) const {
    const int result =
        bioentropy_ascon_xof128(
            output.data(),
            output.size(),
            input.data(),
            input.size()
        );

    if (result != 0) {
        throw std::runtime_error(
            "Ascon-XOF128 conditioning failed"
        );
    }
}

}  // namespace bioentropy
