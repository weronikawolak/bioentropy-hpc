#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using Image =
    std::vector<std::uint8_t>;

constexpr std::size_t trials = 50;
constexpr std::size_t expected_pixels =
    256U * 256U;

Image read_image(
    const std::filesystem::path& path
) {
    std::ifstream input(
        path,
        std::ios::binary
    );

    if (!input) {
        throw std::runtime_error(
            "Cannot open fixture: "
            + path.string()
        );
    }

    Image image{
        std::istreambuf_iterator<char>(
            input
        ),
        std::istreambuf_iterator<char>()
    };

    if (
        image.size()
        != expected_pixels
    ) {
        throw std::runtime_error(
            "Unexpected fixture size: "
            + path.string()
        );
    }

    return image;
}

double entropy(
    const Image& image
) {
    std::array<std::uint64_t, 256>
        counts{};

    for (const auto value : image) {
        ++counts[value];
    }

    double result = 0.0;

    for (const auto count : counts) {
        if (count == 0U) {
            continue;
        }

        const double probability =
            static_cast<double>(count)
            / static_cast<double>(
                image.size()
            );

        result -=
            probability
            * std::log2(probability);
    }

    return result;
}

double npcr(
    const Image& first,
    const Image& second
) {
    if (
        first.size()
        != second.size()
    ) {
        throw std::invalid_argument(
            "NPCR size mismatch"
        );
    }

    std::size_t changed = 0;

    for (
        std::size_t i = 0;
        i < first.size();
        ++i
    ) {
        if (first[i] != second[i]) {
            ++changed;
        }
    }

    return (
        100.0
        * static_cast<double>(changed)
        / static_cast<double>(
            first.size()
        )
    );
}

double uaci(
    const Image& first,
    const Image& second
) {
    if (
        first.size()
        != second.size()
    ) {
        throw std::invalid_argument(
            "UACI size mismatch"
        );
    }

    double total = 0.0;

    for (
        std::size_t i = 0;
        i < first.size();
        ++i
    ) {
        total += std::abs(
            static_cast<int>(first[i])
            - static_cast<int>(
                second[i]
            )
        );
    }

    return (
        100.0
        * total
        / (
            255.0
            * static_cast<double>(
                first.size()
            )
        )
    );
}

Image perturb_change_p(
    const Image& input,
    const std::size_t index
) {
    Image output = input;

    /*
     * +1 modulo 256.
     *
     * Even 255 -> 0 changes the sum
     * by -255, which is still +1 mod 16.
     *
     * Therefore:
     *
     * raw P -> (raw P + 1) mod 16.
     */
    output[index] =
        static_cast<std::uint8_t>(
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
     * +/-16 changes one pixel while
     * preserving sum(image) mod 16.
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
    using bioentropy::
        FettehaDnaCipher2023;

    const FettehaDnaCipher2023::Key
        key{
            0xfc, 0x93, 0x22, 0x49,
            0x33, 0x3c, 0x5f, 0xd1,
            0x3b, 0xab, 0xc5, 0x1b,
            0xe9, 0x9e, 0x2e, 0x39,
            0x28, 0x68, 0x27, 0xb5,
            0x33, 0x00, 0xcc, 0xa7,
            0x38, 0x22, 0x7f, 0x90,
            0x9b, 0xe8, 0x5b, 0xda
        };

    std::filesystem::create_directories(
        "results/aggregated"
    );

    std::ofstream output(
        "results/aggregated/"
        "fetteha_p_confounding.tsv"
    );

    if (!output) {
        std::cerr
            << "Cannot open output TSV\n";

        return 1;
    }

    output
        << "raw_p_base\t"
        << "effective_p_base\t"
        << "mode\t"
        << "trial\t"
        << "changed_index\t"
        << "raw_p_modified\t"
        << "effective_p_modified\t"
        << "effective_pass_delta\t"
        << "cipher_entropy_base\t"
        << "npcr_percent\t"
        << "uaci_percent\n";

    output << std::setprecision(12);

    for (
        unsigned raw_p = 0;
        raw_p <= 15;
        ++raw_p
    ) {
        const auto path =
            std::filesystem::path(
                "results/generated/"
                "fetteha_p_fixtures"
            )
            / (
                "p_"
                + (
                    raw_p < 10
                        ? std::string("0")
                        : std::string()
                )
                + std::to_string(raw_p)
                + ".bin"
            );

        const auto image =
            read_image(path);

        const auto observed_p =
            FettehaDnaCipher2023::
                iteration_count(image);

        if (observed_p != raw_p) {
            throw std::runtime_error(
                "Fixture P mismatch"
            );
        }

        const auto base =
            FettehaDnaCipher2023::
                encrypt(
                    image,
                    key
                );

        const auto base_effective =
            FettehaDnaCipher2023::
                effective_pass_count(
                    base.p
                );

        const double base_entropy =
            entropy(base.ciphertext);

        for (
            std::size_t trial = 0;
            trial < trials;
            ++trial
        ) {
            const std::size_t index =
                (
                    trial * 1319U
                    + raw_p * 313U
                    + 17U
                )
                % image.size();

            for (
                const std::string mode :
                {
                    "change_p",
                    "preserve_p"
                }
            ) {
                const Image modified =
                    mode == "change_p"
                        ? perturb_change_p(
                            image,
                            index
                        )
                        : perturb_preserve_p(
                            image,
                            index
                        );

                const auto modified_result =
                    FettehaDnaCipher2023::
                        encrypt(
                            modified,
                            key
                        );

                const auto modified_effective =
                    FettehaDnaCipher2023::
                        effective_pass_count(
                            modified_result.p
                        );

                const int pass_delta =
                    static_cast<int>(
                        modified_effective
                    )
                    - static_cast<int>(
                        base_effective
                    );

                output
                    << raw_p << '\t'
                    << static_cast<unsigned>(
                        base_effective
                    ) << '\t'
                    << mode << '\t'
                    << trial << '\t'
                    << index << '\t'
                    << static_cast<unsigned>(
                        modified_result.p
                    ) << '\t'
                    << static_cast<unsigned>(
                        modified_effective
                    ) << '\t'
                    << pass_delta << '\t'
                    << base_entropy << '\t'
                    << npcr(
                        base.ciphertext,
                        modified_result.ciphertext
                    ) << '\t'
                    << uaci(
                        base.ciphertext,
                        modified_result.ciphertext
                    ) << '\n';
            }
        }

        std::cout
            << "P="
            << raw_p
            << " complete\n";
    }

    std::cout
        << "Fetteha P-confounding campaign complete\n"
        << "results/aggregated/"
        << "fetteha_p_confounding.tsv\n";

    return 0;
}
