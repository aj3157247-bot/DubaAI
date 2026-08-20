cmake_minimum_required(VERSION 3.18)

project(dubaai_whisper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# DubaAI native engine
#
# whisper.cpp source will be connected here
# in the next step.

message(STATUS "DubaAI Whisper native engine configuration loaded")
message(STATUS "Target ABI: ${ANDROID_ABI}")
