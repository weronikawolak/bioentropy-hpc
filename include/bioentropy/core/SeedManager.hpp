#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace bioentropy {

using Seed256 = std::array<std::uint8_t, 32>;

class SeedManager {
public:
    static Seed256 derive(
        const std::string& master_seed_hex,
        std::string_view experiment_id,
        std::uint32_t replicate_id
    );

    static std::string to_hex(const Seed256& seed);
};

} // namespace bioentropy
