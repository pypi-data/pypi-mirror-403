project(camera_rpc)
include(/opt/robosys/common/cmake/common.cmake)
set(CAMERA_RPC camera-rpc CACHE STRING "camera rpc")
cmake_minimum_required(VERSION 3.0)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -Ofast -fpermissive ")

include_directories(${BOOSTER_ROBOTICS_SDK_INCLUDE_DIR})
include_directories("/usr/local/include")
message("BOOSTER_ROBOTICS_SDK_INCLUDE_DIR: ${BOOSTER_ROBOTICS_SDK_INCLUDE_DIR}")
link_directories(${BOOSTER_ROBOTICS_SDK_LIBS_DIR})

SET(BOOSTER_ROBOTICS_DEPENDENCIES booster_robotics_sdk.a fastrtps fastcdr)
set (SOURCES
    src/x5_camera_rpc.cpp
    src/rpc_server.cpp
)

add_executable(${CAMERA_RPC} ${SOURCES} ${BOOSTER_INTERFACE_SOURCES})

target_link_libraries(${CAMERA_RPC} 
    ${BOOSTER_ROBOTICS_DEPENDENCIES}
)

SET(BOOSTER_ROBOTICS_DEPENDENCIES booster_robotics_sdk.a fastrtps fastcdr)
set (SOURCES_CLIENT
    src/rpc_client.cpp
)

add_executable(camera-client ${SOURCES_CLIENT} ${BOOSTER_INTERFACE_SOURCES})

target_link_libraries(camera-client
    ${BOOSTER_ROBOTICS_DEPENDENCIES}
)





