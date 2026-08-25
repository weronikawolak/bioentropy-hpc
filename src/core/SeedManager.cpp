#include "bioentropy/core/SeedManager.hpp"

#include <array>
#include <cstddef>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>

#include <openssl/evp.h>

namespace bioentropy {

namespace {

constexpr std::string_view DOMAIN_SEPARATOR =
    "BIOENTROPY-HPC-SEED-v1";

std::uint8_t hex_value(char c) {
    if (c >= '0' && c <= '9') {
        return static_cast<std::uint8_t>(c - '0');
    }

    if (c >= 'a' && c <= 'f') {
        return static_cast<std::uint8_t>(10 + c - 'a');
    }

    if (c >= 'A' && c <= 'F') {
        return static_cast<std::uint8_t>(10 + c - 'A');
    }

    throw std::invalid_argument(
        "master seed contains a non-hexadecimal character"
    );
}

Seed256 decode_master_seed(const std::string& hex) {
    if (hex.size() != 64) {
        throw std::invalid_argument(
            "master seed must contain exactly 64 hexadecimal characters"
        );
    }

    Seed256 result{};

    for (std::size_t i = 0; i < result.size(); ++i) {
        const auto high = hex_value(hex[2 * i]);
        const auto low = hex_value(hex[2 * i + 1]);

        result[i] = static_cast<std::uint8_t>(
            (high << 4U) | low
        );
    }

    return result;
}

std::array<std::uint8_t, 8> encode_u64_be(std::uint64_t value) {
    std::array<std::uint8_t, 8> output{};

    for (std::size_t i = 0; i < output.size(); ++i) {
        output[output.size() - 1 - i] =
            static_cast<std::uint8_t>(value & 0xFFU);

        value >>= 8U;
    }

    return output;
}

std::array<std::uint8_t, 4> encode_u32_be(std::uint32_t value) {
    std::array<std::uint8_t, 4> output{};

    for (std::size_t i = 0; i < output.size(); ++i) {
        output[output.size() - 1 - i] =
            static_cast<std::uint8_t>(value & 0xFFU);

        value >>= 8U;
    }

    return output;
}

void update_digest(
    EVP_MD_CTX* context,
    const void* data,
    std::size_t size
) {
    if (EVP_DigestUpdate(context, data, size) != 1) {
        throw std::runtime_error(
            "EVP_DigestUpdate failed"
        );
    }
}

} // namespace

Seed256 SeedManager::derive(
    const std::string& master_seed_hex,
    std::string_view experiment_id,
    std::uint32_t replicate_id
) {
    if (experiment_id.empty()) {
        throw std::invalid_argument(
            "experiment_id must not be empty"
        );
    }

    const Seed256 master_seed =
        decode_master_seed(master_seed_hex);

    const auto experiment_id_size =
        encode_u64_be(
            static_cast<std::uint64_t>(
                experiment_id.size()
            )
        );

    const auto replicate =
        encode_u32_be(replicate_id);

    std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)>
        context(EVP_MD_CTX_new(), &EVP_MD_CTX_free);

    if (!context) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    if (
        EVP_DigestInit_ex(
            context.get(),
            EVP_sha256(),
            nullptr
        ) != 1
    ) {
        throw std::runtime_error(
            "EVP_DigestInit_ex failed"
        );
    }

    update_digest(
        context.get(),
        DOMAIN_SEPARATOR.data(),
        DOMAIN_SEPARATOR.size()
    );

    update_digest(
        context.get(),
        master_seed.data(),
        master_seed.size()
    );

    update_digest(
        context.get(),
        experiment_id_size.data(),
        experiment_id_size.size()
    );

    update_digest(
        context.get(),
        experiment_id.data(),
        experiment_id.size()
    );

    update_digest(
        context.get(),
        replicate.data(),
        replicate.size()
    );

    Seed256 derived_seed{};
    unsigned int digest_length = 0;

    if (
        EVP_DigestFinal_ex(
            context.get(),
            derived_seed.data(),
            &digest_length
        ) != 1
    ) {
        throw std::runtime_error(
            "EVP_DigestFinal_ex failed"
        );
    }

    if (digest_length != derived_seed.size()) {
        throw std::runtime_error(
            "unexpected SHA-256 output length"
        );
    }

    return derived_seed;
}

std::string SeedManager::to_hex(const Seed256& seed) {
    std::ostringstream stream;

    stream << std::hex << std::setfill('0');

    for (const auto byte : seed) {
        stream << std::setw(2)
               << static_cast<unsigned int>(byte);
    }

    return stream.str();
}

} // namespace bioentropy
