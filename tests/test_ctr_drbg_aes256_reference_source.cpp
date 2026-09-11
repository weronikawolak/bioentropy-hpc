#include "bioentropy/sources/CtrDrbgAes256ReferenceSource.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>

namespace {

void require(
    bool condition,
    const char* message
) {
    if (!condition) {
        std::cerr
            << "FAILED: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}


void test_nist_cavp_known_answer() {
    const bioentropy::CtrDrbgAes256::
        SeedMaterial entropy = {
            0xdf, 0x5d, 0x73, 0xfa,
            0xa4, 0x68, 0x64, 0x9e,
            0xdd, 0xa3, 0x3b, 0x5c,
            0xca, 0x79, 0xb0, 0xb0,

            0x56, 0x00, 0x41, 0x9c,
            0xcb, 0x7a, 0x87, 0x9d,
            0xdf, 0xec, 0x9d, 0xb3,
            0x2e, 0xe4, 0x94, 0xe5,

            0x53, 0x1b, 0x51, 0xde,
            0x16, 0xa3, 0x0f, 0x76,
            0x92, 0x62, 0x47, 0x4c,
            0x73, 0xbe, 0xc0, 0x10
        };

    const std::array<std::uint8_t, 64>
        expected = {
            0xd1, 0xc0, 0x7c, 0xd9,
            0x5a, 0xf8, 0xa7, 0xf1,
            0x10, 0x12, 0xc8, 0x4c,
            0xe4, 0x8b, 0xb8, 0xcb,

            0x87, 0x18, 0x9e, 0x99,
            0xd4, 0x0f, 0xcc, 0xb1,
            0x77, 0x1c, 0x61, 0x9b,
            0xdf, 0x82, 0xab, 0x22,

            0x80, 0xb1, 0xdc, 0x2f,
            0x25, 0x81, 0xf3, 0x91,
            0x64, 0xf7, 0xac, 0x0c,
            0x51, 0x04, 0x94, 0xb3,

            0xa4, 0x3c, 0x41, 0xb7,
            0xdb, 0x17, 0x51, 0x4c,
            0x87, 0xb1, 0x07, 0xae,
            0x79, 0x3e, 0x01, 0xc5
        };

    bioentropy::CtrDrbgAes256
        drbg(entropy);

    std::array<std::uint8_t, 64>
        output{};

    /*
     * CAVP vector compares ReturnedBits from
     * the second Generate request.
     */
    drbg.generate(output);
    drbg.generate(output);

    require(
        output == expected,
        "NIST CAVP AES-256 no-df KAT mismatch"
    );
}


void test_reference_source_reset() {
    bioentropy::Seed256 seed{};

    for (
        std::size_t i = 0;
        i < seed.size();
        ++i
    ) {
        seed[i] =
            static_cast<std::uint8_t>(
                i
            );
    }

    bioentropy::
        CtrDrbgAes256ReferenceSource
            source(seed);

    std::array<std::uint8_t, 128>
        first{};

    std::array<std::uint8_t, 128>
        second{};

    source.generate(first);

    source.reset();

    source.generate(second);

    require(
        first == second,
        "reset did not reproduce CTR_DRBG stream"
    );
}


void test_chunk_invariance() {
    bioentropy::Seed256 seed{};

    for (
        std::size_t i = 0;
        i < seed.size();
        ++i
    ) {
        seed[i] =
            static_cast<std::uint8_t>(
                0xa0 + i
            );
    }

    constexpr std::size_t Size =
        100000;

    bioentropy::
        CtrDrbgAes256ReferenceSource
            one_shot(seed);

    bioentropy::
        CtrDrbgAes256ReferenceSource
            chunked(seed);

    std::vector<std::uint8_t>
        expected(Size);

    std::vector<std::uint8_t>
        actual(Size);

    one_shot.generate(expected);

    std::size_t offset = 0;

    const std::array<
        std::size_t,
        7
    > chunks = {
        1,
        17,
        257,
        4096,
        3,
        65535,
        123
    };

    std::size_t chunk_index = 0;

    while (offset < actual.size()) {
        const auto wanted =
            chunks[
                chunk_index
                % chunks.size()
            ];

        const auto count =
            std::min(
                wanted,
                actual.size() - offset
            );

        chunked.generate(
            std::span<std::uint8_t>(
                actual.data() + offset,
                count
            )
        );

        offset += count;
        ++chunk_index;
    }

    require(
        actual == expected,
        "CTR_DRBG source depends on caller chunking"
    );
}

} // namespace


int main() {
    test_nist_cavp_known_answer();
    test_reference_source_reset();
    test_chunk_invariance();

    std::cout
        << "CTR_DRBG AES-256 reference tests passed\n";

    return EXIT_SUCCESS;
}
