cmake_minimum_required(VERSION 3.18)

project(dubaai_whisper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(WHISPER_ROOT
    ${CMAKE_CURRENT_SOURCE_DIR}/whisper.cpp
)

add_library(
    dubaai_whisper
    SHARED
    dubaai_whisper.cpp
)

target_include_directories(
    dubaai_whisper
    PRIVATE
    ${WHISPER_ROOT}/include
)

target_link_directories(
    dubaai_whisper
    PRIVATE
    ${CMAKE_CURRENT_BINARY_DIR}
)

target_link_libraries(
    dubaai_whisper
    whisper
)

if(ANDROID)

    target_link_libraries(
        dubaai_whisper
        log
    )

endif()
