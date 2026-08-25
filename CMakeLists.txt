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

add_executable(
    bioentropy-runner
    src/main.cpp
)

target_include_directories(
    bioentropy-runner
    PRIVATE
        ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(
    bioentropy-runner
    PRIVATE
        OpenMP::OpenMP_CXX
)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(
        bioentropy-runner
        PRIVATE
            -Wall
            -Wextra
            -Wpedantic
    )
endif()
