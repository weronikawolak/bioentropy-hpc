cmake_minimum_required(VERSION 3.20)

project(
    BioEntropyHPC
    VERSION 0.1.0
    DESCRIPTION "HPC-assisted evaluation framework for bio-inspired randomness sources and lightweight cryptography"
    LANGUAGES C CXX
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(OpenMP REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(MPFR REQUIRED IMPORTED_TARGET mpfr)

add_library(
    bioentropy_core
    src/core/ExperimentConfig.cpp
    src/core/SeedManager.cpp
    src/sources/RandomnessSourceFactory.cpp
    src/sources/chaos/LogisticMapSource.cpp
    src/sources/chaos/Chen4DDcsSource.cpp
    src/sources/cellular/CellularAutomatonSource.cpp
    src/sources/reference/ChaCha20ReferenceSource.cpp
    src/sources/dna/DNASequenceSource.cpp
    src/metrics/BitstreamStatistics.cpp
    src/io/ResultWriter.cpp
    src/conditioning/AsconXof128Conditioner.cpp
    src/conditioning/ascon_xof128_variable.c
    src/crypto/AsconAead128.cpp
    src/crypto/ChaCha20Poly1305.cpp
    src/crypto/Aes128Gcm.cpp
    src/crypto/FettehaDnaCipher2023.cpp
    third_party/ascon-c/crypto_aead/asconaead128/ref/aead.c
    third_party/ascon-c/crypto_aead/asconaead128/ref/printstate.c
)

target_include_directories(
    bioentropy_core
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
    PRIVATE
        ${PROJECT_SOURCE_DIR}/src/conditioning
        ${PROJECT_SOURCE_DIR}/third_party/ascon-c/crypto_hash/asconxof128/ref
        ${PROJECT_SOURCE_DIR}/third_party/ascon-c/crypto_aead/asconaead128/ref
        ${PROJECT_SOURCE_DIR}/third_party/ascon-c/tests
)

target_link_libraries(
    bioentropy_core
    PUBLIC
        OpenSSL::Crypto
        yaml-cpp
        PkgConfig::MPFR
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


add_executable(
    chacha20-reference-source-test
    tests/test_chacha20_reference_source.cpp
)

target_link_libraries(
    chacha20-reference-source-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME chacha20-reference-source-test
    COMMAND chacha20-reference-source-test
)


add_executable(
    dna-sequence-source-test
    tests/test_dna_sequence_source.cpp
)

target_link_libraries(
    dna-sequence-source-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME dna-sequence-source-test
    COMMAND dna-sequence-source-test
)

add_executable(
    serial-bitstream-metrics-test
    tests/test_serial_bitstream_metrics.cpp
)

target_link_libraries(
    serial-bitstream-metrics-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME serial-bitstream-metrics-test
    COMMAND serial-bitstream-metrics-test
)


add_executable(
    ascon-xof128-conditioner-test
    tests/test_ascon_xof128_conditioner.cpp
    third_party/ascon-c/crypto_hash/asconxof128/ref/hash.c
    third_party/ascon-c/crypto_hash/asconxof128/ref/printstate.c
)

target_include_directories(
    ascon-xof128-conditioner-test
    PRIVATE
        ${PROJECT_SOURCE_DIR}/third_party/ascon-c/crypto_hash/asconxof128/ref
        ${PROJECT_SOURCE_DIR}/third_party/ascon-c/tests
)

target_link_libraries(
    ascon-xof128-conditioner-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME ascon-xof128-conditioner-test
    COMMAND ascon-xof128-conditioner-test
)


add_executable(
    experiment-config-conditioning-test
    tests/test_experiment_config_conditioning.cpp
)

target_link_libraries(
    experiment-config-conditioning-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME experiment-config-conditioning-test
    COMMAND experiment-config-conditioning-test
)


add_executable(
    ascon-aead128-test
    tests/test_ascon_aead128.cpp
)

target_link_libraries(
    ascon-aead128-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME ascon-aead128-test
    COMMAND ascon-aead128-test
)




add_executable(
    chacha20-poly1305-test
    tests/test_chacha20_poly1305.cpp
)

target_link_libraries(
    chacha20-poly1305-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME chacha20-poly1305-test
    COMMAND chacha20-poly1305-test
)

add_executable(
    ascon-aead128-benchmark
    src/benchmark/benchmark_ascon_aead128.cpp
)

target_link_libraries(
    ascon-aead128-benchmark
    PRIVATE
        bioentropy_core
)


add_executable(
    ascon-aead128-avalanche
    src/benchmark/benchmark_ascon_aead128_avalanche.cpp
)

target_link_libraries(
    ascon-aead128-avalanche
    PRIVATE
        bioentropy_core
)


add_executable(
    fetteha-dna-cipher-2023-test
    tests/test_fetteha_dna_cipher_2023.cpp
)

target_link_libraries(
    fetteha-dna-cipher-2023-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME fetteha-dna-cipher-2023-test
    COMMAND fetteha-dna-cipher-2023-test
)

add_executable(
    fetteha-synthetic-probe
    src/benchmark/benchmark_fetteha_synthetic.cpp
)

target_link_libraries(
    fetteha-synthetic-probe
    PRIVATE
        bioentropy_core
)

add_executable(
    fetteha-p-confounding
    src/benchmark/benchmark_fetteha_p_confounding.cpp
)

target_link_libraries(
    fetteha-p-confounding
    PRIVATE
        bioentropy_core
)


add_executable(
    fetteha-p-matched-control
    src/benchmark/benchmark_fetteha_p_matched_control.cpp
)

target_link_libraries(
    fetteha-p-matched-control
    PRIVATE
        bioentropy_core
)


add_executable(
    fetteha-p-performance
    src/benchmark/benchmark_fetteha_p_performance.cpp
)

target_link_libraries(
    fetteha-p-performance
    PRIVATE
        bioentropy_core
)


add_executable(
    ascon-vs-fetteha-benchmark
    src/benchmark/benchmark_ascon_vs_fetteha.cpp
)

target_link_libraries(
    ascon-vs-fetteha-benchmark
    PRIVATE
        bioentropy_core
)

add_executable(
    brent-cycle-detection-test
    tests/test_brent_cycle_detection.cpp
)

target_link_libraries(
    brent-cycle-detection-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME brent-cycle-detection-test
    COMMAND brent-cycle-detection-test
)

add_executable(
    logistic-periodicity-probe
    src/benchmark/benchmark_logistic_periodicity.cpp
)

target_link_libraries(
    logistic-periodicity-probe
    PRIVATE
        bioentropy_core
        PkgConfig::MPFR
        yaml-cpp
)

add_executable(
    chen-4d-dcs-source-test
    tests/test_chen_4d_dcs_source.cpp
)

target_link_libraries(
    chen-4d-dcs-source-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME chen-4d-dcs-source-test
    COMMAND chen-4d-dcs-source-test
)


add_executable(
    chen-4d-dcs-periodicity-probe
    src/benchmark/benchmark_chen_4d_dcs_periodicity.cpp
)

target_link_libraries(
    chen-4d-dcs-periodicity-probe
    PRIVATE
        bioentropy_core
)

add_executable(
    source-key-material-probe
    src/benchmark/probe_source_key_material.cpp
)

target_link_libraries(
    source-key-material-probe
    PRIVATE
        bioentropy_core
        OpenSSL::Crypto
)

add_executable(
    ascon-xof128-condition-material
    src/benchmark/condition_ascon_xof128_material.cpp
)

target_link_libraries(
    ascon-xof128-condition-material
    PRIVATE
        bioentropy_core
)


add_executable(
    aes128-gcm-test
    tests/test_aes128_gcm.cpp
)

target_link_libraries(
    aes128-gcm-test
    PRIVATE
        bioentropy_core
)

add_test(
    NAME aes128-gcm-test
    COMMAND aes128-gcm-test
)


add_executable(
    source-key-material-probe-aead3
    src/benchmark/probe_source_key_material_aead3.cpp
)

target_link_libraries(
    source-key-material-probe-aead3
    PRIVATE
        bioentropy_core
        OpenSSL::Crypto
)


add_executable(
    three-aead-benchmark
    src/benchmark/benchmark_three_aeads.cpp
)

target_link_libraries(
    three-aead-benchmark
    PRIVATE
        bioentropy_core
        OpenSSL::Crypto
)
