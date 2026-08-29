#include "bioentropy/conditioning/AsconXof128Conditioner.hpp"

extern "C" {
#include "crypto_hash.h"
}

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>

namespace {

void require(
    const bool condition,
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

std::vector<std::uint8_t> make_input(
    const std::size_t size
) {
    std::vector<std::uint8_t> input(size);

    for (std::size_t i = 0; i < size; ++i) {
        input[i] =
            static_cast<std::uint8_t>(i);
    }

    return input;
}

void test_against_reference_crypto_hash(
    const std::size_t input_size
) {
    const auto input =
        make_input(input_size);

    std::array<unsigned char, 64>
        reference{};

    const auto* input_ptr =
        input.empty()
            ? nullptr
            : input.data();

    const int rc = crypto_hash(
        reference.data(),
        input_ptr,
        input.size()
    );

    require(
        rc == 0,
        "reference crypto_hash failed"
    );

    const bioentropy::
        AsconXof128Conditioner conditioner;

    const auto actual =
        conditioner.condition(
            input,
            reference.size()
        );

    require(
        actual.size() == reference.size(),
        "unexpected output length"
    );

    require(
        std::equal(
            actual.begin(),
            actual.end(),
            reference.begin(),
            reference.end()
        ),
        "variable-length adapter differs "
        "from reference crypto_hash"
    );
}

void test_reference_equivalence() {
    for (
        const std::size_t input_size :
        {
            0UL,
            1UL,
            7UL,
            8UL,
            9UL,
            64UL,
            1024UL
        }
    ) {
        test_against_reference_crypto_hash(
            input_size
        );
    }
}

void test_variable_output_prefix_property() {
    const auto input =
        make_input(137);

    const bioentropy::
        AsconXof128Conditioner conditioner;

    const auto short_output =
        conditioner.condition(
            input,
            17
        );

    const auto long_output =
        conditioner.condition(
            input,
            129
        );

    require(
        short_output.size() == 17,
        "17-byte output has wrong size"
    );

    require(
        long_output.size() == 129,
        "129-byte output has wrong size"
    );

    require(
        std::equal(
            short_output.begin(),
            short_output.end(),
            long_output.begin()
        ),
        "XOF prefix property failed"
    );
}

void test_determinism() {
    const auto input =
        make_input(257);

    const bioentropy::
        AsconXof128Conditioner conditioner;

    const auto first =
        conditioner.condition(
            input,
            256
        );

    const auto second =
        conditioner.condition(
            input,
            256
        );

    require(
        first == second,
        "conditioning is not deterministic"
    );
}

void test_input_sensitivity() {
    auto input_a =
        make_input(128);

    auto input_b =
        input_a;

    input_b[63] ^= 0x01;

    const bioentropy::
        AsconXof128Conditioner conditioner;

    const auto output_a =
        conditioner.condition(
            input_a,
            128
        );

    const auto output_b =
        conditioner.condition(
            input_b,
            128
        );

    require(
        output_a != output_b,
        "different inputs produced "
        "identical conditioned output"
    );
}

void test_empty_output() {
    const auto input =
        make_input(64);

    const bioentropy::
        AsconXof128Conditioner conditioner;

    const auto output =
        conditioner.condition(
            input,
            0
        );

    require(
        output.empty(),
        "zero-length request returned data"
    );
}

}  // namespace

int main() {
    test_reference_equivalence();
    test_variable_output_prefix_property();
    test_determinism();
    test_input_sensitivity();
    test_empty_output();

    std::cout
        << "Ascon-XOF128 conditioner tests passed\n";

    return EXIT_SUCCESS;
}
