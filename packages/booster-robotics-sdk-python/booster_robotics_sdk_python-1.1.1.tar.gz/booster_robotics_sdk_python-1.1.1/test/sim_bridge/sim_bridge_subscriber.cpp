#include <booster/robot/channel/channel_subscriber.hpp>
#include <booster_internal/idl/sensor_msgs/JointState.h>
#include <booster_internal/idl/sensor_msgs/Imu.h>

#include <thread>
#include <chrono>
#include <iostream>

#define TOPIC "rt/kidsize_joint_state"

using namespace booster::robot;
using namespace booster::common;

void Handler(const void *msg) {
    const sensor_msgs::msg::JointState *joint_state_msg = static_cast<const sensor_msgs::msg::JointState *>(msg);
     
    std::cout << "Received message: " << std::endl;
    for (size_t i = 0; i < joint_state_msg->name().size(); i++)
    {
        std::cout << "  " << joint_state_msg->name()[i] << ": " << joint_state_msg->position()[i] << std::endl;
    }
}

int main() {
    ChannelFactory::Instance()->Init(0);
    ChannelSubscriber<sensor_msgs::msg::JointState> channel_subscriber(TOPIC, Handler);
    channel_subscriber.InitChannel();
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}