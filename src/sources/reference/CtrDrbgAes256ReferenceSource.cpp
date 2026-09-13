#include "bioentropy/sources/CtrDrbgAes256ReferenceSource.hpp"

#include <openssl/evp.h>

#include <algorithm>
#include <array>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace bioentropy {

namespace {

struct CipherContextDeleter {
    void operator()(
        EVP_CIPHER_CTX* context
    ) const noexcept {
        EVP_CIPHER_CTX_free(context);
    }
};

using CipherContextPtr =
    std::unique_ptr<
        EVP_CIPHER_CTX,
        CipherContextDeleter
    >;

constexpr std::string_view
    SeedDomain =
        "BIOENTROPY-HPC-CTR-DRBG-AES256-NODF-v1";

} // namespace


CtrDrbgAes256::CtrDrbgAes256(
    const SeedMaterial& entropy_input
) {
    reset(entropy_input);
}


void CtrDrbgAes256::reset(
    const SeedMaterial& entropy_input
) {
    key_.fill(0);
    v_.fill(0);

    update(entropy_input);

    reseed_counter_ = 1;
}


void CtrDrbgAes256::increment_v() {
    /*
     * V is a 128-bit big-endian integer in SP 800-90A.
     */
    for (
        std::size_t i = v_.size();
        i > 0;
        --i
    ) {
        auto& byte = v_[i - 1];

        ++byte;

        if (byte != 0) {
            break;
        }
    }
}


void CtrDrbgAes256::encrypt_blocks(
    std::span<const std::uint8_t> input,
    std::span<std::uint8_t> output
) const {
    if (
        input.size() != output.size()
        || input.size() % BlockBytes != 0
    ) {
        throw std::invalid_argument(
            "CTR_DRBG AES input must contain "
            "complete 16-byte blocks"
        );
    }

    if (input.empty()) {
        return;
    }

    CipherContextPtr context(
        EVP_CIPHER_CTX_new()
    );

    if (!context) {
        throw std::runtime_error(
            "EVP_CIPHER_CTX_new failed"
        );
    }

    if (
        EVP_EncryptInit_ex(
            context.get(),
            EVP_aes_256_ecb(),
            nullptr,
            key_.data(),
            nullptr
        ) != 1
    ) {
        throw std::runtime_error(
            "AES-256 ECB initialization failed"
        );
    }

    if (
        EVP_CIPHER_CTX_set_padding(
            context.get(),
            0
        ) != 1
    ) {
        throw std::runtime_error(
            "failed to disable AES padding"
        );
    }

    int produced = 0;

    if (
        EVP_EncryptUpdate(
            context.get(),
            output.data(),
            &produced,
            input.data(),
            static_cast<int>(
                input.size()
            )
        ) != 1
    ) {
        throw std::runtime_error(
            "AES-256 ECB encryption failed"
        );
    }

    if (
        produced
        != static_cast<int>(
            input.size()
        )
    ) {
        throw std::runtime_error(
            "unexpected AES output length"
        );
    }

    int final_size = 0;

    if (
        EVP_EncryptFinal_ex(
            context.get(),
            output.data() + produced,
            &final_size
        ) != 1
    ) {
        throw std::runtime_error(
            "AES-256 ECB finalization failed"
        );
    }

    if (final_size != 0) {
        throw std::runtime_error(
            "unexpected AES final output"
        );
    }
}


void CtrDrbgAes256::update(
    const SeedMaterial& provided_data
) {
    SeedMaterial counter_blocks{};

    for (
        std::size_t block = 0;
        block < 3;
        ++block
    ) {
        increment_v();

        std::copy(
            v_.begin(),
            v_.end(),
            counter_blocks.begin()
                + static_cast<std::ptrdiff_t>(
                    block * BlockBytes
                )
        );
    }

    SeedMaterial temp{};

    encrypt_blocks(
        counter_blocks,
        temp
    );

    for (
        std::size_t i = 0;
        i < temp.size();
        ++i
    ) {
        temp[i] ^= provided_data[i];
    }

    std::copy_n(
        temp.begin(),
        KeyBytes,
        key_.begin()
    );

    std::copy_n(
        temp.begin()
            + static_cast<std::ptrdiff_t>(
                KeyBytes
            ),
        BlockBytes,
        v_.begin()
    );
}


void CtrDrbgAes256::generate(
    std::span<std::uint8_t> output
) {
    if (
        output.size()
        > MaxRequestBytes
    ) {
        throw std::invalid_argument(
            "CTR_DRBG request exceeds "
            "65536 bytes"
        );
    }

    if (output.empty()) {
        return;
    }

    const std::size_t blocks =
        (
            output.size()
            + BlockBytes - 1
        ) / BlockBytes;

    std::vector<std::uint8_t>
        counter_blocks(
            blocks * BlockBytes
        );

    for (
        std::size_t block = 0;
        block < blocks;
        ++block
    ) {
        increment_v();

        std::copy(
            v_.begin(),
            v_.end(),
            counter_blocks.begin()
                + static_cast<std::ptrdiff_t>(
                    block * BlockBytes
                )
        );
    }

    std::vector<std::uint8_t>
        encrypted(
            counter_blocks.size()
        );

    encrypt_blocks(
        counter_blocks,
        encrypted
    );

    std::copy_n(
        encrypted.begin(),
        output.size(),
        output.begin()
    );

    /*
     * SP 800-90A post-generation Update with
     * zero provided_data when no additional_input
     * was supplied.
     */
    SeedMaterial no_additional_input{};

    update(
        no_additional_input
    );

    ++reseed_counter_;
}


CtrDrbgAes256ReferenceSource::
CtrDrbgAes256ReferenceSource(
    Seed256 seed
)
    : seed_(seed),
      drbg_(
          derive_seed_material(seed_)
      ) {}


std::string_view
CtrDrbgAes256ReferenceSource::name()
    const noexcept {
    return "ctr_drbg_aes256_reference";
}


bool
CtrDrbgAes256ReferenceSource::deterministic()
    const noexcept {
    return true;
}


CtrDrbgAes256::SeedMaterial
CtrDrbgAes256ReferenceSource::
derive_seed_material(
    const Seed256& seed
) {
    /*
     * Experiment Seed256 is deterministically expanded
     * to the 384-bit seed_material required by the
     * AES-256 CTR_DRBG no-df construction.
     *
     * This does NOT create additional entropy.
     */
    EVP_MD_CTX* raw_context =
        EVP_MD_CTX_new();

    if (!raw_context) {
        throw std::runtime_error(
            "EVP_MD_CTX_new failed"
        );
    }

    std::unique_ptr<
        EVP_MD_CTX,
        decltype(&EVP_MD_CTX_free)
    > context(
        raw_context,
        EVP_MD_CTX_free
    );

    if (
        EVP_DigestInit_ex(
            context.get(),
            EVP_sha384(),
            nullptr
        ) != 1
    ) {
        throw std::runtime_error(
            "SHA-384 initialization failed"
        );
    }

    if (
        EVP_DigestUpdate(
            context.get(),
            SeedDomain.data(),
            SeedDomain.size()
        ) != 1
    ) {
        throw std::runtime_error(
            "SHA-384 domain update failed"
        );
    }

    if (
        EVP_DigestUpdate(
            context.get(),
            seed.data(),
            seed.size()
        ) != 1
    ) {
        throw std::runtime_error(
            "SHA-384 seed update failed"
        );
    }

    CtrDrbgAes256::SeedMaterial material{};

    unsigned int size = 0;

    if (
        EVP_DigestFinal_ex(
            context.get(),
            material.data(),
            &size
        ) != 1
    ) {
        throw std::runtime_error(
            "SHA-384 finalization failed"
        );
    }

    if (
        size != material.size()
    ) {
        throw std::runtime_error(
            "unexpected SHA-384 output length"
        );
    }

    return material;
}


void
CtrDrbgAes256ReferenceSource::reset() {
    drbg_.reset(
        derive_seed_material(
            seed_
        )
    );

    buffer_offset_ =
        request_buffer_.size();
}


void
CtrDrbgAes256ReferenceSource::refill() {
    drbg_.generate(
        request_buffer_
    );

    buffer_offset_ = 0;
}


void
CtrDrbgAes256ReferenceSource::generate(
    std::span<std::uint8_t> output
) {
    std::size_t written = 0;

    while (
        written < output.size()
    ) {
        if (
            buffer_offset_
            == request_buffer_.size()
        ) {
            refill();
        }

        const std::size_t available =
            request_buffer_.size()
            - buffer_offset_;

        const std::size_t required =
            output.size()
            - written;

        const std::size_t count =
            std::min(
                available,
                required
            );

        std::copy_n(
            request_buffer_.begin()
                + static_cast<
                    std::ptrdiff_t
                >(
                    buffer_offset_
                ),
            count,
            output.begin()
                + static_cast<
                    std::ptrdiff_t
                >(
                    written
                )
        );

        buffer_offset_ += count;
        written += count;
    }
}

} // namespace bioentropy
