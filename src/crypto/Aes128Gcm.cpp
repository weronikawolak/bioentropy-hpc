#include "bioentropy/crypto/Aes128Gcm.hpp"

#include <openssl/evp.h>

#include <limits>
#include <memory>
#include <stdexcept>

namespace bioentropy {

namespace {

struct ContextDeleter {
    void operator()(EVP_CIPHER_CTX* ctx) const noexcept {
        EVP_CIPHER_CTX_free(ctx);
    }
};

using ContextPtr =
    std::unique_ptr<
        EVP_CIPHER_CTX,
        ContextDeleter
    >;

ContextPtr make_context() {
    ContextPtr ctx(
        EVP_CIPHER_CTX_new()
    );

    if (!ctx) {
        throw std::runtime_error(
            "EVP_CIPHER_CTX_new failed"
        );
    }

    return ctx;
}

int checked_size(std::size_t size) {
    if (
        size >
        static_cast<std::size_t>(
            std::numeric_limits<int>::max()
        )
    ) {
        throw std::length_error(
            "AES-GCM input exceeds EVP size limit"
        );
    }

    return static_cast<int>(size);
}

void require_success(
    int result,
    const char* message
) {
    if (result != 1) {
        throw std::runtime_error(message);
    }
}

} // namespace

std::vector<std::uint8_t>
Aes128Gcm::encrypt(
    std::span<const std::uint8_t> plaintext,
    std::span<const std::uint8_t> associated_data,
    const Key& key,
    const Nonce& nonce
) const {
    auto ctx = make_context();

    require_success(
        EVP_EncryptInit_ex(
            ctx.get(),
            EVP_aes_128_gcm(),
            nullptr,
            nullptr,
            nullptr
        ),
        "AES-GCM cipher setup failed"
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            ctx.get(),
            EVP_CTRL_AEAD_SET_IVLEN,
            static_cast<int>(NonceBytes),
            nullptr
        ),
        "AES-GCM IV length setup failed"
    );

    require_success(
        EVP_EncryptInit_ex(
            ctx.get(),
            nullptr,
            nullptr,
            key.data(),
            nonce.data()
        ),
        "AES-GCM key/nonce setup failed"
    );

    int produced = 0;

    if (!associated_data.empty()) {
        require_success(
            EVP_EncryptUpdate(
                ctx.get(),
                nullptr,
                &produced,
                associated_data.data(),
                checked_size(
                    associated_data.size()
                )
            ),
            "AES-GCM AAD processing failed"
        );
    }

    std::vector<std::uint8_t> output(
        plaintext.size() + TagBytes
    );

    int ciphertext_size = 0;

    if (!plaintext.empty()) {
        require_success(
            EVP_EncryptUpdate(
                ctx.get(),
                output.data(),
                &produced,
                plaintext.data(),
                checked_size(
                    plaintext.size()
                )
            ),
            "AES-GCM encryption failed"
        );

        ciphertext_size += produced;
    }

    int final_size = 0;

    require_success(
        EVP_EncryptFinal_ex(
            ctx.get(),
            output.data() + ciphertext_size,
            &final_size
        ),
        "AES-GCM finalization failed"
    );

    ciphertext_size += final_size;

    output.resize(
        static_cast<std::size_t>(
            ciphertext_size
        ) + TagBytes
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            ctx.get(),
            EVP_CTRL_AEAD_GET_TAG,
            static_cast<int>(TagBytes),
            output.data() + ciphertext_size
        ),
        "AES-GCM tag retrieval failed"
    );

    return output;
}

std::optional<std::vector<std::uint8_t>>
Aes128Gcm::decrypt(
    std::span<const std::uint8_t> ciphertext_and_tag,
    std::span<const std::uint8_t> associated_data,
    const Key& key,
    const Nonce& nonce
) const {
    if (
        ciphertext_and_tag.size()
        < TagBytes
    ) {
        return std::nullopt;
    }

    const std::size_t ciphertext_size =
        ciphertext_and_tag.size() - TagBytes;

    const auto ciphertext =
        ciphertext_and_tag.first(
            ciphertext_size
        );

    const auto tag =
        ciphertext_and_tag.last(
            TagBytes
        );

    auto ctx = make_context();

    require_success(
        EVP_DecryptInit_ex(
            ctx.get(),
            EVP_aes_128_gcm(),
            nullptr,
            nullptr,
            nullptr
        ),
        "AES-GCM decrypt setup failed"
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            ctx.get(),
            EVP_CTRL_AEAD_SET_IVLEN,
            static_cast<int>(NonceBytes),
            nullptr
        ),
        "AES-GCM IV length setup failed"
    );

    require_success(
        EVP_DecryptInit_ex(
            ctx.get(),
            nullptr,
            nullptr,
            key.data(),
            nonce.data()
        ),
        "AES-GCM decrypt key/nonce setup failed"
    );

    int produced = 0;

    if (!associated_data.empty()) {
        require_success(
            EVP_DecryptUpdate(
                ctx.get(),
                nullptr,
                &produced,
                associated_data.data(),
                checked_size(
                    associated_data.size()
                )
            ),
            "AES-GCM decrypt AAD failed"
        );
    }

    std::vector<std::uint8_t>
        plaintext(ciphertext_size);

    int plaintext_size = 0;

    if (!ciphertext.empty()) {
        require_success(
            EVP_DecryptUpdate(
                ctx.get(),
                plaintext.data(),
                &produced,
                ciphertext.data(),
                checked_size(
                    ciphertext.size()
                )
            ),
            "AES-GCM decryption failed"
        );

        plaintext_size += produced;
    }

    require_success(
        EVP_CIPHER_CTX_ctrl(
            ctx.get(),
            EVP_CTRL_AEAD_SET_TAG,
            static_cast<int>(TagBytes),
            const_cast<std::uint8_t*>(
                tag.data()
            )
        ),
        "AES-GCM tag setup failed"
    );

    int final_size = 0;

    const int result =
        EVP_DecryptFinal_ex(
            ctx.get(),
            plaintext.data()
                + plaintext_size,
            &final_size
        );

    if (result != 1) {
        return std::nullopt;
    }

    plaintext_size += final_size;

    plaintext.resize(
        static_cast<std::size_t>(
            plaintext_size
        )
    );

    return plaintext;
}

} // namespace bioentropy
