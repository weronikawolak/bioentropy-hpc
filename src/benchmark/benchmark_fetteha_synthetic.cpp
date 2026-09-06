#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace {

constexpr std::size_t width = 256;
constexpr std::size_t height = 256;
constexpr std::size_t trials = 50;

using Image = std::vector<std::uint8_t>;

Image make_black() {
    return Image(width * height, 0U);
}

Image make_white() {
    return Image(width * height, 255U);
}

Image make_checkerboard() {
    Image image(width * height);

    for (std::size_t y = 0; y < height; ++y) {
        for (std::size_t x = 0; x < width; ++x) {
            const bool white =
                ((x / 8U) + (y / 8U)) % 2U != 0U;

            image[y * width + x] =
                white ? 255U : 0U;
        }
    }

    return image;
}

Image make_gradient() {
    Image image(width * height);

    for (std::size_t y = 0; y < height; ++y) {
        for (std::size_t x = 0; x < width; ++x) {
            image[y * width + x] =
                static_cast<std::uint8_t>(x);
        }
    }

    return image;
}

double entropy(
    const Image& image
) {
    std::array<std::uint64_t, 256> counts{};

    for (const auto value : image) {
        ++counts[value];
    }

    double result = 0.0;

    for (const auto count : counts) {
        if (count == 0U) {
            continue;
        }

        const double p =
            static_cast<double>(count)
            / static_cast<double>(image.size());

        result -= p * std::log2(p);
    }

    return result;
}

double npcr(
    const Image& first,
    const Image& second
) {
    std::size_t changed = 0;

    for (std::size_t i = 0; i < first.size(); ++i) {
        if (first[i] != second[i]) {
            ++changed;
        }
    }

    return (
        100.0
        * static_cast<double>(changed)
        / static_cast<double>(first.size())
    );
}

double uaci(
    const Image& first,
    const Image& second
) {
    double total = 0.0;

    for (std::size_t i = 0; i < first.size(); ++i) {
        total += std::abs(
            static_cast<int>(first[i])
            - static_cast<int>(second[i])
        );
    }

    return (
        100.0
        * total
        / (
            255.0
            * static_cast<double>(first.size())
        )
    );
}

Image perturb_plus_one(
    const Image& input,
    const std::size_t index
) {
    Image output = input;

    /*
     * Standard one-pixel modification.
     *
     * This changes raw P by +1 mod 16.
     */
    output[index] =
        output[index] == 255U
            ? 0U
            : static_cast<std::uint8_t>(
                output[index] + 1U
            );

    return output;
}

Image perturb_preserve_p(
    const Image& input,
    const std::size_t index
) {
    Image output = input;

    /*
     * Diagnostic one-pixel modification
     * preserving pixel_sum mod 16.
     *
     * Change intensity by exactly 16.
     */
    if (output[index] <= 239U) {
        output[index] =
            static_cast<std::uint8_t>(
                output[index] + 16U
            );
    } else {
        output[index] =
            static_cast<std::uint8_t>(
                output[index] - 16U
            );
    }

    return output;
}

}  // namespace

int main() {
    using bioentropy::FettehaDnaCipher2023;

    const FettehaDnaCipher2023::Key key{
        0xfc, 0x93, 0x22, 0x49,
        0x33, 0x3c, 0x5f, 0xd1,
        0x3b, 0xab, 0xc5, 0x1b,
        0xe9, 0x9e, 0x2e, 0x39,
        0x28, 0x68, 0x27, 0xb5,
        0x33, 0x00, 0xcc, 0xa7,
        0x38, 0x22, 0x7f, 0x90,
        0x9b, 0xe8, 0x5b, 0xda
    };

    struct Workload {
        std::string name;
        Image image;
    };

    const std::array<Workload, 4> workloads{{
        {"black", make_black()},
        {"white", make_white()},
        {"checkerboard", make_checkerboard()},
        {"gradient", make_gradient()}
    }};

    std::filesystem::create_directories(
        "results/aggregated"
    );

    std::ofstream output(
        "results/aggregated/"
        "fetteha_synthetic_probe.tsv"
    );

    if (!output) {
        std::cerr << "Cannot open output TSV\n";
        return 1;
    }

    output
        << "image\tmode\ttrial\tchanged_index\t"
        << "raw_p_base\traw_p_modified\t"
        << "effective_p_base\teffective_p_modified\t"
        << "cipher_entropy_base\t"
        << "npcr_percent\tuaci_percent\n";

    output << std::setprecision(12);

    for (const auto& workload : workloads) {
        const auto encrypted_base =
            FettehaDnaCipher2023::encrypt(
                workload.image,
                key
            );

        const auto base_entropy =
            entropy(encrypted_base.ciphertext);

        const auto effective_base =
            FettehaDnaCipher2023::
                effective_pass_count(
                    encrypted_base.p
                );

        for (
            std::size_t trial = 0;
            trial < trials;
            ++trial
        ) {
            /*
             * Odd multiplier -> deterministic
             * non-repeating positions in this
             * first 50-trial window.
             */
            const std::size_t index =
                (
                    trial * 1319U
                    + 17U
                )
                % workload.image.size();

            for (
                const std::string mode :
                {
                    "single_pixel_plus1",
                    "single_pixel_preserve_p"
                }
            ) {
                const Image modified =
                    mode == "single_pixel_plus1"
                        ? perturb_plus_one(
                            workload.image,
                            index
                        )
                        : perturb_preserve_p(
                            workload.image,
                            index
                        );

                const auto encrypted_modified =
                    FettehaDnaCipher2023::encrypt(
                        modified,
                        key
                    );

                output
                    << workload.name << '\t'
                    << mode << '\t'
                    << trial << '\t'
                    << index << '\t'
                    << static_cast<unsigned>(
                        encrypted_base.p
                    ) << '\t'
                    << static_cast<unsigned>(
                        encrypted_modified.p
                    ) << '\t'
                    << static_cast<unsigned>(
                        effective_base
                    ) << '\t'
                    << static_cast<unsigned>(
                        FettehaDnaCipher2023::
                            effective_pass_count(
                                encrypted_modified.p
                            )
                    ) << '\t'
                    << base_entropy << '\t'
                    << npcr(
                        encrypted_base.ciphertext,
                        encrypted_modified.ciphertext
                    ) << '\t'
                    << uaci(
                        encrypted_base.ciphertext,
                        encrypted_modified.ciphertext
                    ) << '\n';
            }
        }
    }

    std::cout
        << "Synthetic Fetteha probe complete\n"
        << "results/aggregated/"
        << "fetteha_synthetic_probe.tsv\n";

    return 0;
}
