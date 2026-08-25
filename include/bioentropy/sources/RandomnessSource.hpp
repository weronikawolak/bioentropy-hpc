#pragma once

#include <cstdint>
#include <span>
#include <string_view>

namespace bioentropy {

class RandomnessSource {
public:
    virtual ~RandomnessSource() = default;

    virtual std::string_view name() const noexcept = 0;

    virtual bool deterministic() const noexcept = 0;

    virtual void reset() = 0;

    virtual void generate(
        std::span<std::uint8_t> output
    ) = 0;
};

} // namespace bioentropy
