cmake_minimum_required(VERSION 3.20)

project(
    BioEntropyHPC
    VERSION 0.1.0
    DESCRIPTION "HPC-assisted evaluation framework for bio-inspired randomness sources and lightweight cryptography"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(OpenMP REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(yaml-cpp REQUIRED)

add_library(
    bioentropy_core
    src/core/ExperimentConfig.cpp
    src/core/SeedManager.cpp
    src/sources/RandomnessSourceFactory.cpp
    src/sources/chaos/LogisticMapSource.cpp
    src/sources/cellular/CellularAutomatonSource.cpp
    src/metrics/BitstreamStatistics.cpp
    src/io/ResultWriter.cpp
)

target_include_directories(
    bioentropy_core
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(
    bioentropy_core
    PUBLIC
        OpenSSL::Crypto
        yaml-cpp
)

add_executable(
    bioentropy-runner
    src/main.cpp
)

target_link_libraries(
    bioentropy-runner
    PRIVATE
        bioentropy_core
        OpenMP::OpenMP_CXX
)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(
        bioentropy_core
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
            -fno-fast-math
            -ffp-contract=off
    )

    target_compile_options(
        bioentropy-runner
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
    )
endif()

enable_testing()

add_executable(
    seed-manager-test
    tests/test_seed_manager.cpp
)

target_link_libraries(
    seed-manager-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME seed-manager-test
    COMMAND seed-manager-test
)

add_executable(
    logistic-map-source-test
    tests/test_logistic_map_source.cpp
)

target_link_libraries(
    logistic-map-source-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME logistic-map-source-test
    COMMAND logistic-map-source-test
)

add_executable(
    bitstream-statistics-test
    tests/test_bitstream_statistics.cpp
)

target_link_libraries(
    bitstream-statistics-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME bitstream-statistics-test
    COMMAND bitstream-statistics-test
)

add_executable(
    cellular-automaton-source-test
    tests/test_cellular_automaton_source.cpp
)

target_link_libraries(
    cellular-automaton-source-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME cellular-automaton-source-test
    COMMAND cellular-automaton-source-test
)
