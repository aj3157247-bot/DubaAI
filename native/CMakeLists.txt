cmake_minimum_required(VERSION 3.18)

project(dubaai_whisper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# =========================================================
# Official whisper.cpp
# =========================================================

set(WHISPER_ROOT
    ${CMAKE_CURRENT_SOURCE_DIR}/whisper.cpp
)

if(NOT EXISTS "${WHISPER_ROOT}/CMakeLists.txt")
    message(FATAL_ERROR
        "Official whisper.cpp source was not found at: ${WHISPER_ROOT}"
    )
endif()

# =========================================================
# Build whisper.cpp and GGML as STATIC libraries
# =========================================================

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

set(WHISPER_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_SERVER OFF CACHE BOOL "" FORCE)

set(WHISPER_CURL OFF CACHE BOOL "" FORCE)
set(WHISPER_SDL2 OFF CACHE BOOL "" FORCE)
set(WHISPER_COMMON_FFMPEG OFF CACHE BOOL "" FORCE)

set(GGML_NATIVE OFF CACHE BOOL "" FORCE)

# Disable unnecessary GGML backends
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_CUDA OFF CACHE BOOL "" FORCE)
set(GGML_METAL OFF CACHE BOOL "" FORCE)
set(GGML_VULKAN OFF CACHE BOOL "" FORCE)
set(GGML_SYCL OFF CACHE BOOL "" FORCE)

# =========================================================
# Add official whisper.cpp
# =========================================================

add_subdirectory(
    ${WHISPER_ROOT}
    whisper-build
    EXCLUDE_FROM_ALL
)

# =========================================================
# DubaAI native wrapper
# =========================================================

add_library(
    dubaai_whisper
    SHARED
    dubaai_whisper.cpp
)

target_include_directories(
    dubaai_whisper
    PRIVATE

    ${WHISPER_ROOT}/include
    ${WHISPER_ROOT}/ggml/include
)

# =========================================================
# Link whisper.cpp
#
# whisper.cpp and GGML are static, therefore their code
# becomes part of libdubaai_whisper.so.
# =========================================================

target_link_libraries(
    dubaai_whisper
    PRIVATE
    whisper
)

# =========================================================
# Android system libraries
# =========================================================

if(ANDROID)

    find_library(
        ANDROID_LOG
        log
    )

    target_link_libraries(
        dubaai_whisper
        PRIVATE
        ${ANDROID_LOG}
    )

endif()

# =========================================================
# Android ARM64 optimization
# =========================================================

if(ANDROID AND
   CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")

    target_compile_options(
        dubaai_whisper
        PRIVATE
        -O2
    )

endif()

# =========================================================
# Output
# =========================================================

set_target_properties(
    dubaai_whisper
    PROPERTIES
    OUTPUT_NAME "dubaai_whisper"
)
