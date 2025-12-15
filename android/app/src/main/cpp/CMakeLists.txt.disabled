cmake_minimum_required(VERSION 3.22.1)

project(firestorm_native)

add_library(firestorm_native SHARED
        native-lib.cpp)

find_library(log-lib log)

target_link_libraries(firestorm_native
        ${log-lib})
