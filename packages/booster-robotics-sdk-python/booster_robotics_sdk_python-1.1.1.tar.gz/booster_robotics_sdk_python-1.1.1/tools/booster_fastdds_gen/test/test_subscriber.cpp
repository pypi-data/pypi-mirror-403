#include <booster/robot/channel/channel_subscriber.hpp>
#include "temp/Header.h"
#include <booster_internal/idl/demo/DemoMsg.h>

#include <thread>
#include <chrono>
#include <iostream>

#define TOPIC "rt/TestMsgTopic"

using namespace booster::robot;
using namespace booster::common;
using namespace booster::msg;
using namespace std_msgs::msg;

void Handler(const void *msg) {
    const Header *demo_msg = static_cast<const Header *>(msg);
    // int res = demo_msg->cmd_type() == SERIAL ? 1 : 0;
    std::cout << "Received message: "
              << demo_msg->frame_id() << ", "
              << std::endl;
}

int main() {
    ChannelFactory::Instance()->Init(0, "127.0.0.1");
    ChannelSubscriber<Header> channel_subscriber(TOPIC, Handler);
    channel_subscriber.InitChannel();
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}