#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace bioentropy {

class AsconXof128Conditioner {
public:
    [[nodiscard]]
    std::vector<std::uint8_t> condition(
        std::span<const std::uint8_t> input,
        std::size_t output_bytes
    ) const;

    void condition(
        std::span<const std::uint8_t> input,
        std::span<std::uint8_t> output
    ) const;
};

}  // namespace bioentropy
