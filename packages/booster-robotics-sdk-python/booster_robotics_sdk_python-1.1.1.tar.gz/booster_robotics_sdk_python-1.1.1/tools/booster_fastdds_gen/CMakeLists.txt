cmake_minimum_required(VERSION 3.0)

# Set default buld_type as `Release`
IF(NOT CMAKE_BUILD_TYPE)
    SET(CMAKE_BUILD_TYPE Release)
ENDIF()

IF(CMAKE_BUILD_TYPE MATCHES Debug)
    MESSAGE("Debug build.")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -Wall -Wextra -Wpedantic")
elseIF(CMAKE_BUILD_TYPE MATCHES Release)
    MESSAGE("Release build.")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall")
ENDIF()

project(booster_fastdds_gen)
add_executable(booster_fastdds_gen codegen.cpp)

install(TARGETS booster_fastdds_gen DESTINATION /usr/local/bin)

option(BUILD_TEST "Build Test" off)

if (BUILD_TEST)
    file(GLOB_RECURSE TEST_PUB_SOURCES
        "test/temp/*.cpp"
        "test/test_publisher.cpp")
    link_libraries(booster_robotics_sdk fastrtps fastcdr libfoonathan_memory-0.7.3.a)
    add_executable(test_pub ${TEST_PUB_SOURCES})

    file(GLOB_RECURSE TEST_SUB_SOURCES
        "test/temp/*.cpp"
        "test/test_subscriber.cpp")
    link_libraries(booster_robotics_sdk fastrtps fastcdr libfoonathan_memory-0.7.3.a)
    add_executable(test_sub ${TEST_SUB_SOURCES})
endif()
