#pragma once

#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <cstdint>
#include <span>
#include <string_view>

namespace bioentropy {

class LogisticMapSource final : public RandomnessSource {
public:
    LogisticMapSource(
        LogisticMapConfig config,
        Seed256 seed
    );

    std::string_view name() const noexcept override;

    bool deterministic() const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

    double initial_state() const noexcept;

private:
    LogisticMapConfig config_;
    Seed256 seed_;

    double initial_state_{};
    double state_{};

    static double derive_initial_state(
        const Seed256& seed
    );

    void validate_config() const;

    void advance();
};

} // namespace bioentropy
