#include "bioentropy/crypto/DnaSubsequenceCipher2012.hpp"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>

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

bool near(
    const double first,
    const double second,
    const double tolerance = 1.0e-12
) {
    return std::abs(
        first - second
    ) <= tolerance;
}

}  // namespace

int main() {
    using bioentropy::
        DnaBase;

    using bioentropy::
        DnaSubsequenceCipher2012;

    using bioentropy::
        DnaSubsequenceKey2012;

    using bioentropy::
        Logistic2DState2012;

    /*
     * Published mapping:
     *
     * 00 -> G
     * 01 -> A
     * 10 -> T
     * 11 -> C
     */
    require(
        DnaSubsequenceCipher2012::
            encode_pair(0b00)
        == DnaBase::G,
        "00 must encode as G"
    );

    require(
        DnaSubsequenceCipher2012::
            encode_pair(0b01)
        == DnaBase::A,
        "01 must encode as A"
    );

    require(
        DnaSubsequenceCipher2012::
            encode_pair(0b10)
        == DnaBase::T,
        "10 must encode as T"
    );

    require(
        DnaSubsequenceCipher2012::
            encode_pair(0b11)
        == DnaBase::C,
        "11 must encode as C"
    );

    /*
     * Published validation example:
     *
     * 75 decimal
     * = 01001011
     * = A G T C
     */
    const auto encoded_75 =
        DnaSubsequenceCipher2012::
            encode_byte(75);

    require(
        encoded_75[0]
            == DnaBase::A,
        "75 base 0 mismatch"
    );

    require(
        encoded_75[1]
            == DnaBase::G,
        "75 base 1 mismatch"
    );

    require(
        encoded_75[2]
            == DnaBase::T,
        "75 base 2 mismatch"
    );

    require(
        encoded_75[3]
            == DnaBase::C,
        "75 base 3 mismatch"
    );

    require(
        DnaSubsequenceCipher2012::
            decode_byte(encoded_75)
        == 75,
        "published 75 round-trip failed"
    );

    /*
     * Exhaustive byte-level round-trip.
     */
    for (
        unsigned int value = 0;
        value <= 255;
        ++value
    ) {
        const auto byte =
            static_cast<std::uint8_t>(
                value
            );

        require(
            DnaSubsequenceCipher2012::
                decode_byte(
                    DnaSubsequenceCipher2012::
                        encode_byte(byte)
                )
            == byte,
            "byte round-trip failed"
        );
    }

    /*
     * Watson-Crick complements.
     */
    require(
        DnaSubsequenceCipher2012::
            complement(DnaBase::A)
        == DnaBase::T,
        "A complement mismatch"
    );

    require(
        DnaSubsequenceCipher2012::
            complement(DnaBase::T)
        == DnaBase::A,
        "T complement mismatch"
    );

    require(
        DnaSubsequenceCipher2012::
            complement(DnaBase::C)
        == DnaBase::G,
        "C complement mismatch"
    );

    require(
        DnaSubsequenceCipher2012::
            complement(DnaBase::G)
        == DnaBase::C,
        "G complement mismatch"
    );

    /*
     * First 2D Logistic step using the
     * paper's experimental parameters.
     */
    const DnaSubsequenceKey2012 key;

    const Logistic2DState2012 initial{
        key.x0,
        key.y0
    };

    const auto next =
        DnaSubsequenceCipher2012::
            logistic_2d_step(
                initial,
                key
            );

    require(
        near(
            next.x,
            0.162625
        ),
        "2D Logistic x step mismatch"
    );

    require(
        near(
            next.y,
            0.77835
        ),
        "2D Logistic y step mismatch"
    );

    /*
     * Basic 1D Logistic reference.
     */
    require(
        near(
            DnaSubsequenceCipher2012::
                logistic_step(
                    0.25,
                    4.0
                ),
            0.75
        ),
        "1D Logistic step mismatch"
    );

    std::cout
        << "DNA subsequence cipher 2012 "
        << "primitive tests passed\n";

    return EXIT_SUCCESS;
}
