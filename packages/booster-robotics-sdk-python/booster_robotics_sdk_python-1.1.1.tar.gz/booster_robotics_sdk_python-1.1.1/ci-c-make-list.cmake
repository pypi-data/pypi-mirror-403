cmake_policy(SET CMP0048 NEW)

SET(CMAKE_CXX_STANDARD 17)

project(project-booster-robotics-sdk)

cmake_minimum_required(VERSION 3.15...3.27)

SET(LIB_BOOSTER_ROBOTICS_SDK booster_robotics_sdk CACHE STRING "Booster Robotics SDK")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_CXX_STANDARD 17)

include("${CMAKE_CURRENT_LIST_DIR}/.workflow/project-defined.cmake")


include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include/booster/idl/b1)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include/booster/idl/builtin_interfaces)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include/booster/idl/sensor_msgs)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/include/booster/idl/std_msgs)
include_directories(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/internal_include)

file(GLOB_RECURSE BOOSTER_ROBOTICS_SDK_SOURCES
        "src/*.cpp"
        "src/*.cxx"
        "src/*.ipp")

list(FILTER BOOSTER_ROBOTICS_SDK_SOURCES EXCLUDE REGEX "src/python/.*\\.cpp")


add_library(${LIB_BOOSTER_ROBOTICS_SDK} ${BOOSTER_ROBOTICS_SDK_SOURCES})
closure_link_target_lib(${LIB_BOOSTER_ROBOTICS_SDK})

macro(default_install_none)
endmacro()

macro(custom_install_env)
    install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/ DESTINATION ${CMAKE_INSTALL_PREFIX}/include)
    install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/internal_include/ DESTINATION ${CMAKE_INSTALL_PREFIX}/include)
endmacro()

closure_import_install_project(default_install_none custom_install_env)

