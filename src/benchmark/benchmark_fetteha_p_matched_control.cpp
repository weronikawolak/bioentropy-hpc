#include "bioentropy/crypto/FettehaDnaCipher2023.hpp"

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
            "Unexpected fixture size"
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

        const double p =
            static_cast<double>(count)
            / static_cast<double>(
                image.size()
            );

        result -= p * std::log2(p);
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

std::size_t find_plus_index(
    const Image& image,
    const std::size_t start
) {
    for (
        std::size_t offset = 0;
        offset < image.size();
        ++offset
    ) {
        const std::size_t index =
            (start + offset)
            % image.size();

        /*
         * +1 must really mean intensity
         * difference of exactly one.
         *
         * Therefore avoid 255 -> 0.
         */
        if (image[index] < 255U) {
            return index;
        }
    }

    throw std::runtime_error(
        "Cannot find +1 pixel"
    );
}

std::size_t find_minus_index(
    const Image& image,
    const std::size_t start,
    const std::size_t excluded
) {
    for (
        std::size_t offset = 0;
        offset < image.size();
        ++offset
    ) {
        const std::size_t index =
            (start + offset)
            % image.size();

        /*
         * -1 must have magnitude exactly 1,
         * and must affect a second pixel.
         */
        if (
            index != excluded
            && image[index] > 0U
        ) {
            return index;
        }
    }

    throw std::runtime_error(
        "Cannot find -1 pixel"
    );
}

Image perturb_change_p(
    const Image& input,
    const std::size_t plus_index
) {
    Image output = input;

    output[plus_index] =
        static_cast<std::uint8_t>(
            output[plus_index] + 1U
        );

    return output;
}

Image perturb_preserve_p_matched(
    const Image& input,
    const std::size_t plus_index,
    const std::size_t minus_index
) {
    Image output = input;

    /*
     * Matched-magnitude control:
     *
     * pixel A: +1
     * pixel B: -1
     *
     * Total pixel-sum change = 0.
     *
     * Therefore raw P is unchanged.
     */
    output[plus_index] =
        static_cast<std::uint8_t>(
            output[plus_index] + 1U
        );

    output[minus_index] =
        static_cast<std::uint8_t>(
            output[minus_index] - 1U
        );

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
        "fetteha_p_matched_control.tsv"
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
        << "plus_index\t"
        << "minus_index\t"
        << "raw_p_modified\t"
        << "effective_p_modified\t"
        << "effective_pass_delta\t"
        << "plaintext_changed_pixels\t"
        << "plaintext_total_abs_delta\t"
        << "cipher_entropy_base\t"
        << "npcr_percent\t"
        << "uaci_percent\n";

    output << std::setprecision(12);

    for (
        unsigned raw_p = 0;
        raw_p <= 15;
        ++raw_p
    ) {
        const std::string number =
            raw_p < 10
                ? "0" + std::to_string(raw_p)
                : std::to_string(raw_p);

        const auto path =
            std::filesystem::path(
                "results/generated/"
                "fetteha_p_fixtures"
            )
            / (
                "p_"
                + number
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

        const auto effective_base =
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
            const std::size_t primary_seed =
                (
                    trial * 1319U
                    + raw_p * 313U
                    + 17U
                )
                % image.size();

            const std::size_t plus_index =
                find_plus_index(
                    image,
                    primary_seed
                );

            /*
             * Deliberately use a different
             * deterministic walk for the
             * compensating -1 pixel.
             */
            const std::size_t secondary_seed =
                (
                    plus_index
                    + 7919U
                    + trial * 17U
                )
                % image.size();

            const std::size_t minus_index =
                find_minus_index(
                    image,
                    secondary_seed,
                    plus_index
                );

            for (
                const std::string mode :
                {
                    "change_p_plus1",
                    "preserve_p_plus1_minus1"
                }
            ) {
                const Image modified =
                    mode == "change_p_plus1"
                        ? perturb_change_p(
                            image,
                            plus_index
                        )
                        : perturb_preserve_p_matched(
                            image,
                            plus_index,
                            minus_index
                        );

                const auto modified_p =
                    FettehaDnaCipher2023::
                        iteration_count(
                            modified
                        );

                if (
                    mode
                        == "change_p_plus1"
                    && modified_p
                        != (
                            (raw_p + 1U)
                            % 16U
                        )
                ) {
                    throw std::runtime_error(
                        "Change-P perturbation "
                        "did not change P by +1"
                    );
                }

                if (
                    mode
                        == "preserve_p_plus1_minus1"
                    && modified_p != raw_p
                ) {
                    throw std::runtime_error(
                        "Matched control "
                        "did not preserve P"
                    );
                }

                const auto encrypted =
                    FettehaDnaCipher2023::
                        encrypt(
                            modified,
                            key
                        );

                const auto effective_modified =
                    FettehaDnaCipher2023::
                        effective_pass_count(
                            encrypted.p
                        );

                const int pass_delta =
                    static_cast<int>(
                        effective_modified
                    )
                    - static_cast<int>(
                        effective_base
                    );

                const unsigned
                    changed_plaintext_pixels =
                        mode
                            == "change_p_plus1"
                            ? 1U
                            : 2U;

                const unsigned
                    total_abs_delta =
                        mode
                            == "change_p_plus1"
                            ? 1U
                            : 2U;

                output
                    << raw_p << '\t'
                    << static_cast<unsigned>(
                        effective_base
                    ) << '\t'
                    << mode << '\t'
                    << trial << '\t'
                    << plus_index << '\t';

                if (
                    mode
                    == "change_p_plus1"
                ) {
                    output << -1;
                } else {
                    output << minus_index;
                }

                output
                    << '\t'
                    << static_cast<unsigned>(
                        encrypted.p
                    ) << '\t'
                    << static_cast<unsigned>(
                        effective_modified
                    ) << '\t'
                    << pass_delta << '\t'
                    << changed_plaintext_pixels
                    << '\t'
                    << total_abs_delta
                    << '\t'
                    << base_entropy << '\t'
                    << npcr(
                        base.ciphertext,
                        encrypted.ciphertext
                    ) << '\t'
                    << uaci(
                        base.ciphertext,
                        encrypted.ciphertext
                    ) << '\n';
            }
        }

        std::cout
            << "P="
            << raw_p
            << " complete\n";
    }

    std::cout
        << "Matched-magnitude campaign complete\n"
        << "results/aggregated/"
        << "fetteha_p_matched_control.tsv\n";

    return 0;
}
