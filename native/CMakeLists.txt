cmake_minimum_required(VERSION 3.18)

project(dubaai_whisper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(WHISPER_ROOT
    ${CMAKE_CURRENT_SOURCE_DIR}/whisper.cpp
)

# Build official whisper.cpp as a subproject.
set(BUILD_SHARED_LIBS ON CACHE BOOL "" FORCE)

set(WHISPER_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_SERVER OFF CACHE BOOL "" FORCE)

set(WHISPER_CURL OFF CACHE BOOL "" FORCE)
set(WHISPER_SDL2 OFF CACHE BOOL "" FORCE)
set(WHISPER_COMMON_FFMPEG OFF CACHE BOOL "" FORCE)

set(GGML_NATIVE OFF CACHE BOOL "" FORCE)

add_subdirectory(
    ${WHISPER_ROOT}
    whisper-build
    EXCLUDE_FROM_ALL
)

# DubaAI wrapper
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

target_link_libraries(
    dubaai_whisper
    PRIVATE
    whisper
)

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

set_target_properties(
    dubaai_whisper
    PROPERTIES
    OUTPUT_NAME "dubaai_whisper"
)
