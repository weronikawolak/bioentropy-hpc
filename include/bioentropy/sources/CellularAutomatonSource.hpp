#pragma once

#include "bioentropy/core/SeedManager.hpp"
#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace bioentropy {

class CellularAutomatonSource final
    : public RandomnessSource {
public:
    CellularAutomatonSource(
        CellularAutomatonConfig config,
        Seed256 seed
    );

    std::string_view name() const noexcept override;

    bool deterministic() const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

private:
    CellularAutomatonConfig config_;
    Seed256 seed_;

    std::vector<std::uint8_t> cells_;
    std::vector<std::uint8_t> next_cells_;

    std::size_t output_cell_index_{0};

    void validate_config() const;

    void initialize_cells();

    void evolve();

    static std::vector<std::uint8_t>
    expand_seed(
        const Seed256& seed,
        std::size_t output_bytes
    );
};

} // namespace bioentropy
