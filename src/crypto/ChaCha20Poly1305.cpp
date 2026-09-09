#include "bioentropy/crypto/ChaCha20Poly1305.hpp"

#include <openssl/evp.h>

#include <limits>
#include <memory>
#include <stdexcept>

namespace bioentropy {

namespace {

struct ContextDeleter {
    void operator()(
        EVP_CIPHER_CTX* context
    ) const noexcept {
        EVP_CIPHER_CTX_free(context);
    }
};

using ContextPtr =
    std::unique_ptr<
        EVP_CIPHER_CTX,
        ContextDeleter
    >;

ContextPtr make_context() {
    ContextPtr context(
        EVP_CIPHER_CTX_new()
    );

    if (!context) {
        throw std::runtime_error(
            "EVP_CIPHER_CTX_new failed"
        );
    }

    return context;
}

int checked_size(
    std::size_t size
) {
    if (
        size >
        static_cast<std::size_t>(
            std::numeric_limits<int>::max()
        )
    ) {
        throw std::length_error(
            "ChaCha20-Poly1305 input exceeds "
            "OpenSSL EVP size limit"
        );
    }

    return static_cast<int>(size);
}

void require_success(
    int result,
    const char* operation
) {
    if (result != 1) {
        throw std::runtime_error(
            operation
        );
    }
}

} // namespace

std::vector<std::uint8_t>
ChaCha20Poly1305::encrypt(
    std::span<const std::uint8_t> plaintext,
    std::span<const std::uint8_t> associated_data,
    const Key& key,
    const Nonce& nonce
) const {
    auto context =
        make_context();

    require_success(
        EVP_EncryptInit_ex(
            context.get(),
            EVP_chacha20_poly1305(),
            nullptr,
            nullptr,
            nullptr
        ),
        "EVP_EncryptInit_ex cipher setup failed"
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            context.get(),
            EVP_CTRL_AEAD_SET_IVLEN,
            static_cast<int>(NonceBytes),
            nullptr
        ),
        "EVP_CTRL_AEAD_SET_IVLEN failed"
    );

    require_success(
        EVP_EncryptInit_ex(
            context.get(),
            nullptr,
            nullptr,
            key.data(),
            nonce.data()
        ),
        "EVP_EncryptInit_ex key/nonce failed"
    );

    int produced = 0;

    if (!associated_data.empty()) {
        require_success(
            EVP_EncryptUpdate(
                context.get(),
                nullptr,
                &produced,
                associated_data.data(),
                checked_size(
                    associated_data.size()
                )
            ),
            "ChaCha20-Poly1305 AAD processing failed"
        );
    }

    std::vector<std::uint8_t>
        output(
            plaintext.size()
            + TagBytes
        );

    int ciphertext_size = 0;

    if (!plaintext.empty()) {
        require_success(
            EVP_EncryptUpdate(
                context.get(),
                output.data(),
                &produced,
                plaintext.data(),
                checked_size(
                    plaintext.size()
                )
            ),
            "ChaCha20-Poly1305 encryption failed"
        );

        ciphertext_size += produced;
    }

    int final_size = 0;

    require_success(
        EVP_EncryptFinal_ex(
            context.get(),
            output.data()
                + ciphertext_size,
            &final_size
        ),
        "ChaCha20-Poly1305 finalization failed"
    );

    ciphertext_size += final_size;

    output.resize(
        static_cast<std::size_t>(
            ciphertext_size
        )
        + TagBytes
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            context.get(),
            EVP_CTRL_AEAD_GET_TAG,
            static_cast<int>(TagBytes),
            output.data()
                + ciphertext_size
        ),
        "ChaCha20-Poly1305 tag retrieval failed"
    );

    return output;
}

std::optional<std::vector<std::uint8_t>>
ChaCha20Poly1305::decrypt(
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
        ciphertext_and_tag.size()
        - TagBytes;

    const auto ciphertext =
        ciphertext_and_tag.first(
            ciphertext_size
        );

    const auto tag =
        ciphertext_and_tag.last(
            TagBytes
        );

    auto context =
        make_context();

    require_success(
        EVP_DecryptInit_ex(
            context.get(),
            EVP_chacha20_poly1305(),
            nullptr,
            nullptr,
            nullptr
        ),
        "EVP_DecryptInit_ex cipher setup failed"
    );

    require_success(
        EVP_CIPHER_CTX_ctrl(
            context.get(),
            EVP_CTRL_AEAD_SET_IVLEN,
            static_cast<int>(NonceBytes),
            nullptr
        ),
        "EVP_CTRL_AEAD_SET_IVLEN failed"
    );

    require_success(
        EVP_DecryptInit_ex(
            context.get(),
            nullptr,
            nullptr,
            key.data(),
            nonce.data()
        ),
        "EVP_DecryptInit_ex key/nonce failed"
    );

    int produced = 0;

    if (!associated_data.empty()) {
        require_success(
            EVP_DecryptUpdate(
                context.get(),
                nullptr,
                &produced,
                associated_data.data(),
                checked_size(
                    associated_data.size()
                )
            ),
            "ChaCha20-Poly1305 AAD processing failed"
        );
    }

    std::vector<std::uint8_t>
        plaintext(
            ciphertext_size
        );

    int plaintext_size = 0;

    if (!ciphertext.empty()) {
        require_success(
            EVP_DecryptUpdate(
                context.get(),
                plaintext.data(),
                &produced,
                ciphertext.data(),
                checked_size(
                    ciphertext.size()
                )
            ),
            "ChaCha20-Poly1305 decryption failed"
        );

        plaintext_size += produced;
    }

    require_success(
        EVP_CIPHER_CTX_ctrl(
            context.get(),
            EVP_CTRL_AEAD_SET_TAG,
            static_cast<int>(TagBytes),
            const_cast<std::uint8_t*>(
                tag.data()
            )
        ),
        "ChaCha20-Poly1305 tag setup failed"
    );

    int final_size = 0;

    const int result =
        EVP_DecryptFinal_ex(
            context.get(),
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
