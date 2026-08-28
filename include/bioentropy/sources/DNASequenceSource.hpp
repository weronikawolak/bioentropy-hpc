#pragma once

#include "bioentropy/core/SourceConfig.hpp"
#include "bioentropy/sources/RandomnessSource.hpp"

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace bioentropy {

class DNASequenceSource final
    : public RandomnessSource {
public:
    explicit DNASequenceSource(
        DNASequenceConfig config
    );

    std::string_view name() const noexcept override;

    bool deterministic() const noexcept override;

    void reset() override;

    void generate(
        std::span<std::uint8_t> output
    ) override;

private:
    DNASequenceConfig config_;

    std::vector<std::uint8_t> encoded_;
    std::size_t position_{0};

    static std::string load_sequence(
        const std::string& path
    );

    static std::string sha256_hex(
        std::string_view sequence
    );

    static std::uint8_t nucleotide_value(
        char nucleotide
    );

    void load_and_encode();
};

} // namespace bioentropy
