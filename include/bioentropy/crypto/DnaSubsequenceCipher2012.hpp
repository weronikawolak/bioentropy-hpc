#pragma once

#include <array>
#include <cstdint>

namespace bioentropy {

enum class DnaBase : std::uint8_t {
    A,
    T,
    G,
    C
};

struct DnaSubsequenceKey2012 {
    double x0{0.95};
    double mu1{3.2};
    double gamma1{0.17};

    double y0{0.25};
    double mu2{3.3};
    double gamma2{0.14};
};

struct Logistic2DState2012 {
    double x{};
    double y{};
};

class DnaSubsequenceCipher2012 {
public:
    using EncodedByte =
        std::array<DnaBase, 4>;

    [[nodiscard]]
    static DnaBase encode_pair(
        std::uint8_t two_bits
    );

    [[nodiscard]]
    static std::uint8_t decode_pair(
        DnaBase base
    );

    [[nodiscard]]
    static DnaBase complement(
        DnaBase base
    );

    [[nodiscard]]
    static EncodedByte encode_byte(
        std::uint8_t value
    );

    [[nodiscard]]
    static std::uint8_t decode_byte(
        const EncodedByte& sequence
    );

    [[nodiscard]]
    static Logistic2DState2012
    logistic_2d_step(
        const Logistic2DState2012& state,
        const DnaSubsequenceKey2012& key
    );

    [[nodiscard]]
    static double logistic_step(
        double x,
        double mu
    );
};

}  // namespace bioentropy
