#include <chrono>
#include <thread>
#include <iostream>

#include <booster/robot/x5_camera/x5_camera_api_const.hpp>
#include "x5_camera_rpc.hpp"

using namespace booster::robot;
using namespace booster::robot::x5_camera;
int main() {
    ChannelFactory::Instance()->Init(0);
    X5CameraRpcServer server = X5CameraRpcServer();
    server.Init(booster::robot::x5_camera::kTopicX5CameraControlMode);

    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
