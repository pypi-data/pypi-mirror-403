cmake_minimum_required(VERSION 3.15...3.27)
cmake_policy(SET CMP0048 NEW)

if (ORIN)
    MESSAGE("Compile for ORIN ... ")

    execute_process(
        COMMAND uname -m
        OUTPUT_VARIABLE RAW_ARCH
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    string(TOLOWER "${RAW_ARCH}" DETECTED_ARCH)
    message(STATUS "[System] uname -m = ${DETECTED_ARCH}")

    if(DETECTED_ARCH MATCHES "x86_64|i[3456]86|amd64")
        SET(CMAKE_CXX_COMPILER "/usr/bin/aarch64-linux-gnu-g++-12")
        SET(CMAKE_C_COMPILER "/usr/bin/aarch64-linux-gnu-gcc-12")
    endif()

    set(CMAKE_SYSTEM_NAME Linux)
    set(CMAKE_SYSTEM_PROCESSOR aarch64)
    set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
    set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
    set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
    set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

    IF(NOT BOOSTER_THIRD_PARTY_INCLUDE_DIR)
        SET(BOOSTER_THIRD_PARTY_INCLUDE_DIR /opt/robosys/third_party_orin/include CACHE PATH "Booster third party include dir")
    ENDIF()

    IF(NOT BOOSTER_THIRD_PARTY_LIB_DIR)
        SET(BOOSTER_THIRD_PARTY_LIB_DIR /opt/robosys/third_party_orin/lib CACHE PATH "Booster third party lib dir")
    ENDIF()

    include_directories(${BOOSTER_THIRD_PARTY_INCLUDE_DIR})
    link_directories(${BOOSTER_THIRD_PARTY_LIB_DIR})
else()
    SET(CMAKE_CXX_STANDARD 17)
endif()

if(NOT DEFINED SKBUILD_PROJECT_NAME)
    set(SKBUILD_PROJECT_NAME booster_robotics_sdk)
endif()

if(NOT DEFINED SKBUILD_PROJECT_VERSION)
    set(SKBUILD_PROJECT_VERSION 0.1.0)
endif()

project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  LANGUAGES CXX)


SET(LIB_BOOSTER_ROBOTICS_SDK booster_robotics_sdk CACHE STRING "Booster Robotics SDK")
SET(TEST_BOOSTER_ROBOTICS_SDK booster_robotics_sdk_test CACHE STRING "Booster Robotics SDK Test")

option(BUILD_TEST "Build Test" off)

option(BUILD_PYTHON_BINDING "Build Python Binding" off)
message(STATUS "BUILD_PYTHON_BINDING: ${BUILD_PYTHON_BINDING}")

if(ORIN)
    set(PLATFORM_SUFFIX "_orin")
    message(STATUS "Architecture is: ORIN")

    if(NOT INSTALL_DIR)
        set(INSTALL_DIR /opt/robosys CACHE PATH "rs_sdk install dir")
    endif()

    set(LIB_INSTALL_PREFIX ${INSTALL_DIR}/${LIB_BOOSTER_ROBOTICS_SDK}${PLATFORM_SUFFIX})
else()
    set(LIB_INSTALL_PREFIX ${CMAKE_INSTALL_LIBDIR})
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_CXX_STANDARD 17)

include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include/booster/idl/b1)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include/booster/idl/builtin_interfaces)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include/booster/idl/sensor_msgs)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include/booster/idl/std_msgs)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/internal_include)


file(GLOB_RECURSE BOOSTER_ROBOTICS_SDK_SOURCES 
    "src/*.cpp"
    "src/*.cxx"
    "src/*.ipp")

list(FILTER BOOSTER_ROBOTICS_SDK_SOURCES EXCLUDE REGEX "src/python/.*\\.cpp")

file(GLOB_RECURSE BOOSTER_ROBOTICS_SDK_HEADERS 
    "include/*.h"
    "include/*.hpp")
file(GLOB_RECURSE DEMO_TEST_SOURCES 
    "test/demo_test/*.cpp"
    "test/demo_test/*.cxx"
    "test/demo_test/*.ipp")

add_library(${LIB_BOOSTER_ROBOTICS_SDK} ${BOOSTER_ROBOTICS_SDK_SOURCES})

link_libraries(${LIB_BOOSTER_ROBOTICS_SDK} fastrtps fastcdr libfoonathan_memory-0.7.3.a)

if (BUILD_TEST)
    add_executable(${TEST_BOOSTER_ROBOTICS_SDK} ${DEMO_TEST_SOURCES})
    # target_link_libraries(${TEST_BOOSTER_ROBOTICS_SDK} ${LIB_BOOSTER_ROBOTICS_SDK} fastrtps fastcdr)

    add_executable(b1_loco_example_client sdk_release/example/high_level/b1_loco_example_client.cpp)
    add_executable(b1_low_level_publisher sdk_release/example/low_level/low_level_publisher.cpp)
    add_executable(b1_low_level_subscriber sdk_release/example/low_level/low_level_subscriber.cpp)
    add_executable(b1_odometer_example sdk_release/example/low_level/odometer_example.cpp)
    add_executable(b1_arm_sdk_example_client sdk_release/example/high_level/b1_arm_sdk_example.cpp)
    add_executable(b1_low_sdk_example sdk_release/example/low_level/b1_low_sdk_example.cpp)
    add_executable(b1_state_subscriber sdk_release/example/high_level/b1_state_subscriber.cpp)

    add_executable(test_rpc_client test/rpc/rpc_client.cpp)
    add_executable(test_rpc_server test/rpc/rpc_server.cpp)
    add_executable(test_publisher test/pub_sub/publisher.cpp)
    add_executable(test_subscriber test/pub_sub/subscriber.cpp)
    add_executable(test_sim_bridge_subscriber test/sim_bridge/sim_bridge_subscriber.cpp)
endif()

include(GNUInstallDirs)
#install(TARGETS ${LIB_BOOSTER_ROBOTICS_SDK} ARCHIVE DESTINATION ${LIB_INSTALL_PREFIX CMAKE_INSTALL_LIBDIR})
install(TARGETS ${LIB_BOOSTER_ROBOTICS_SDK} ARCHIVE DESTINATION ${LIB_INSTALL_PREFIX})
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(DIRECTORY internal_include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})



if(BUILD_PYTHON_BINDING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
    message(STATUS "Python3 executable: ${Python3_EXECUTABLE}")

    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
        OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE result
        ERROR_VARIABLE error
    )

    include_directories(${Python3_INCLUDE_DIRS})
    find_package(pybind11 CONFIG REQUIRED)

    python3_add_library(_core MODULE src/python/binding.cpp WITH_SOABI)
    target_compile_definitions(_core PRIVATE VERSION_INFO=${PROJECT_VERSION})

    python3_add_library(booster_robotics_sdk_internal_python MODULE src/python/internal_binding.cpp WITH_SOABI)
    target_compile_definitions(booster_robotics_sdk_internal_python PRIVATE VERSION_INFO=${PROJECT_VERSION})

    if(GENERATE_PYBIND11_STUBS)
        find_program(PYBIND11_STUBGEN_EXECUTABLE pybind11-stubgen)
        if(NOT PYBIND11_STUBGEN_EXECUTABLE)
            message(FATAL_ERROR "pybind11-stubgen not found")
        endif()

        add_custom_command(
            TARGET _core
            POST_BUILD
            COMMAND PYTHONPATH=${CMAKE_SOURCE_DIR}/build:/${PYTHONPATH} pybind11-stubgen -o ${CMAKE_SOURCE_DIR}/build _core
        )

        add_custom_command(
            TARGET booster_robotics_sdk_internal_python
            POST_BUILD
            COMMAND PYTHONPATH=${CMAKE_SOURCE_DIR}/build:/${PYTHONPATH} pybind11-stubgen -o ${CMAKE_SOURCE_DIR}/build booster_robotics_sdk_internal_python
        )
    endif()

    if(DEFINED SKBUILD_PLATLIB_DIR)
        message(STATUS "Install Python modules into SKBUILD_PLATLIB_DIR = ${SKBUILD_PLATLIB_DIR}")
        set(PYTHON_SITE_PACKAGES "${SKBUILD_PLATLIB_DIR}")
    else()
        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
            OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        message(STATUS "Local build: install Python modules into ${PYTHON_SITE_PACKAGES}")
    endif()

    install(TARGETS _core
            LIBRARY DESTINATION "${PYTHON_SITE_PACKAGES}/booster_robotics_sdk_python")
            
    install(TARGETS booster_robotics_sdk_internal_python
            LIBRARY DESTINATION "${PYTHON_SITE_PACKAGES}")

    if(GENERATE_PYBIND11_STUBS)
        install(FILES ${CMAKE_SOURCE_DIR}/build/_core.pyi 
                DESTINATION "${PYTHON_SITE_PACKAGES}/booster_robotics_sdk_python")
                
        install(FILES ${CMAKE_SOURCE_DIR}/build/booster_robotics_sdk_internal_python.pyi 
                DESTINATION "${PYTHON_SITE_PACKAGES}")
    endif()

endif()