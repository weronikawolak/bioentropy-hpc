#include "bioentropy/sources/CellularAutomatonSource.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

#include <openssl/evp.h>

namespace bioentropy {

namespace {

constexpr std::string_view CA_SEED_DOMAIN =
    "BIOENTROPY-HPC-CA-INIT-v1";

std::array<std::uint8_t, 4>
encode_u32_be(std::uint32_t value) {
    return {
        static_cast<std::uint8_t>(
            (value >> 24U) & 0xFFU
        ),
        static_cast<std::uint8_t>(
            (value >> 16U) & 0xFFU
        ),
        static_cast<std::uint8_t>(
            (value >> 8U) & 0xFFU
        ),
        static_cast<std::uint8_t>(
            value & 0xFFU
        )
    };
}

std::array<std::uint8_t, 32>
derive_seed_block(
    const Seed256& seed,
    std::uint32_t counter
) {
    EVP_MD_CTX* context =
        EVP_MD_CTX_new();

    if (context == nullptr) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    const auto counter_bytes =
        encode_u32_be(counter);

    std::array<std::uint8_t, 32>
        digest{};

    unsigned int digest_length = 0;

    bool success = true;

    success =
        success &&
        EVP_DigestInit_ex(
            context,
            EVP_sha256(),
            nullptr
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            context,
            CA_SEED_DOMAIN.data(),
            CA_SEED_DOMAIN.size()
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            context,
            seed.data(),
            seed.size()
        ) == 1;

    success =
        success &&
        EVP_DigestUpdate(
            context,
            counter_bytes.data(),
            counter_bytes.size()
        ) == 1;

    success =
        success &&
        EVP_DigestFinal_ex(
            context,
            digest.data(),
            &digest_length
        ) == 1;

    EVP_MD_CTX_free(context);

    if (
        !success ||
        digest_length != digest.size()
    ) {
        throw std::runtime_error(
            "failed to derive cellular automaton "
            "initial-state block"
        );
    }

    return digest;
}

} // namespace

CellularAutomatonSource::
CellularAutomatonSource(
    CellularAutomatonConfig config,
    Seed256 seed
)
    : config_(std::move(config)),
      seed_(seed) {

    validate_config();

    cells_.resize(
        static_cast<std::size_t>(
            config_.cells
        )
    );

    next_cells_.resize(
        cells_.size()
    );

    reset();
}

std::string_view
CellularAutomatonSource::name() const noexcept {
    return "cellular_automaton";
}

bool
CellularAutomatonSource::deterministic() const noexcept {
    return true;
}

void
CellularAutomatonSource::validate_config() const {
    if (
        config_.rule != CellularAutomatonRule::Rule30 &&
        config_.rule != CellularAutomatonRule::Rule90
    ) {
        throw std::invalid_argument(
            "cellular automaton rule must be 30 or 90"
        );
    }

    if (
        config_.cells != 256 &&
        config_.cells != 1024
    ) {
        throw std::invalid_argument(
            "cellular automaton cells must be 256 or 1024"
        );
    }

    if (config_.cells % 8 != 0) {
        throw std::invalid_argument(
            "cellular automaton cell count "
            "must be divisible by 8"
        );
    }
}

std::vector<std::uint8_t>
CellularAutomatonSource::expand_seed(
    const Seed256& seed,
    std::size_t output_bytes
) {
    std::vector<std::uint8_t> output;

    output.reserve(output_bytes);

    std::uint32_t counter = 0;

    while (output.size() < output_bytes) {
        const auto block =
            derive_seed_block(
                seed,
                counter
            );

        const std::size_t remaining =
            output_bytes - output.size();

        const std::size_t copy_count =
            std::min(
                remaining,
                block.size()
            );

        output.insert(
            output.end(),
            block.begin(),
            block.begin()
                + static_cast<std::ptrdiff_t>(
                    copy_count
                )
        );

        ++counter;
    }

    return output;
}

void
CellularAutomatonSource::initialize_cells() {
    const std::size_t state_bytes =
        cells_.size() / 8U;

    const auto initial_bytes =
        expand_seed(
            seed_,
            state_bytes
        );

    std::size_t cell_index = 0;

    for (const auto byte : initial_bytes) {
        for (int bit = 7; bit >= 0; --bit) {
            cells_[cell_index] =
                static_cast<std::uint8_t>(
                    (byte >> bit) & 0x01U
                );

            ++cell_index;
        }
    }
}

void
CellularAutomatonSource::evolve() {
    const std::size_t count =
        cells_.size();

    const auto rule =
        static_cast<std::uint16_t>(
            config_.rule
        );

    for (std::size_t i = 0; i < count; ++i) {
        const std::uint8_t left =
            cells_[
                (i + count - 1U) % count
            ];

        const std::uint8_t center =
            cells_[i];

        const std::uint8_t right =
            cells_[
                (i + 1U) % count
            ];

        const std::uint8_t neighborhood =
            static_cast<std::uint8_t>(
                (left << 2U) |
                (center << 1U) |
                right
            );

        next_cells_[i] =
            static_cast<std::uint8_t>(
                (rule >> neighborhood)
                & 0x01U
            );
    }

    cells_.swap(next_cells_);
}

void
CellularAutomatonSource::reset() {
    initialize_cells();

    /*
     * Generation 0 is the deterministic initial state.
     * It is not emitted directly.
     */
    evolve();

    output_cell_index_ = 0;
}

void
CellularAutomatonSource::generate(
    std::span<std::uint8_t> output
) {
    for (auto& output_byte : output) {
        output_byte = 0;

        for (int bit = 0; bit < 8; ++bit) {
            if (
                output_cell_index_ ==
                cells_.size()
            ) {
                evolve();

                output_cell_index_ = 0;
            }

            output_byte =
                static_cast<std::uint8_t>(
                    output_byte << 1U
                );

            output_byte =
                static_cast<std::uint8_t>(
                    output_byte |
                    cells_[output_cell_index_]
                );

            ++output_cell_index_;
        }
    }
}

} // namespace bioentropy
