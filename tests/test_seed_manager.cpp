#include "bioentropy/core/SeedManager.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr
            << "TEST FAILURE: "
            << message
            << '\n';

        std::exit(EXIT_FAILURE);
    }
}

} // namespace

int main() {
    const std::string master_seed =
        "0123456789abcdef"
        "0123456789abcdef"
        "0123456789abcdef"
        "0123456789abcdef";

    const auto seed_a =
        bioentropy::SeedManager::derive(
            master_seed,
            "smoke-test-001",
            0
        );

    const auto seed_b =
        bioentropy::SeedManager::derive(
            master_seed,
            "smoke-test-001",
            0
        );

    require(
        seed_a == seed_b,
        "same experiment must produce the same seed"
    );

    const std::string seed_a_hex =
        bioentropy::SeedManager::to_hex(seed_a);

    require(
        seed_a_hex.size() == 64,
        "derived seed must contain 256 bits"
    );

    require(
        seed_a_hex ==
        "a2b988dbbd0a0dde17e2124a203c405f"
        "5853d1db03547372a547682f38ee8d30",
        "derived seed does not match the reference vector"
    );

    const auto different_replicate =
        bioentropy::SeedManager::derive(
            master_seed,
            "smoke-test-001",
            1
        );

    require(
        seed_a != different_replicate,
        "different replicate IDs must produce different seeds"
    );

    const auto different_experiment =
        bioentropy::SeedManager::derive(
            master_seed,
            "another-experiment",
            0
        );

    require(
        seed_a != different_experiment,
        "different experiment IDs must produce different seeds"
    );

    std::cout
        << "SeedManager tests passed.\n";

    return EXIT_SUCCESS;
}
