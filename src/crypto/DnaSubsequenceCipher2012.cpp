#include "bioentropy/crypto/DnaSubsequenceCipher2012.hpp"

#include <stdexcept>

namespace bioentropy {

DnaBase
DnaSubsequenceCipher2012::encode_pair(
    const std::uint8_t two_bits
) {
    switch (two_bits) {
        case 0b00:
            return DnaBase::G;

        case 0b01:
            return DnaBase::A;

        case 0b10:
            return DnaBase::T;

        case 0b11:
            return DnaBase::C;
    }

    throw std::invalid_argument(
        "DNA pair must contain exactly two bits"
    );
}

std::uint8_t
DnaSubsequenceCipher2012::decode_pair(
    const DnaBase base
) {
    switch (base) {
        case DnaBase::G:
            return 0b00;

        case DnaBase::A:
            return 0b01;

        case DnaBase::T:
            return 0b10;

        case DnaBase::C:
            return 0b11;
    }

    throw std::invalid_argument(
        "unknown DNA base"
    );
}

DnaBase
DnaSubsequenceCipher2012::complement(
    const DnaBase base
) {
    switch (base) {
        case DnaBase::A:
            return DnaBase::T;

        case DnaBase::T:
            return DnaBase::A;

        case DnaBase::C:
            return DnaBase::G;

        case DnaBase::G:
            return DnaBase::C;
    }

    throw std::invalid_argument(
        "unknown DNA base"
    );
}

DnaSubsequenceCipher2012::EncodedByte
DnaSubsequenceCipher2012::encode_byte(
    const std::uint8_t value
) {
    EncodedByte result{};

    result[0] =
        encode_pair(
            static_cast<std::uint8_t>(
                (value >> 6U) & 0x03U
            )
        );

    result[1] =
        encode_pair(
            static_cast<std::uint8_t>(
                (value >> 4U) & 0x03U
            )
        );

    result[2] =
        encode_pair(
            static_cast<std::uint8_t>(
                (value >> 2U) & 0x03U
            )
        );

    result[3] =
        encode_pair(
            static_cast<std::uint8_t>(
                value & 0x03U
            )
        );

    return result;
}

std::uint8_t
DnaSubsequenceCipher2012::decode_byte(
    const EncodedByte& sequence
) {
    return static_cast<std::uint8_t>(
        (
            decode_pair(sequence[0])
            << 6U
        )
        |
        (
            decode_pair(sequence[1])
            << 4U
        )
        |
        (
            decode_pair(sequence[2])
            << 2U
        )
        |
        decode_pair(sequence[3])
    );
}

Logistic2DState2012
DnaSubsequenceCipher2012::logistic_2d_step(
    const Logistic2DState2012& state,
    const DnaSubsequenceKey2012& key
) {
    const double x = state.x;
    const double y = state.y;

    const double next_x =
        key.mu1
        * x
        * (1.0 - x)
        +
        key.gamma1
        * y
        * y;

    const double next_y =
        key.mu2
        * y
        * (1.0 - y)
        +
        key.gamma2
        * (
            x * x
            + x * y
        );

    return {
        next_x,
        next_y
    };
}

double
DnaSubsequenceCipher2012::logistic_step(
    const double x,
    const double mu
) {
    return (
        mu
        * x
        * (1.0 - x)
    );
}

}  // namespace bioentropy
