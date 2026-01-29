#include <booster/robot/channel/channel_subscriber.hpp>
#include <booster_internal/idl/demo/DemoMsg.h>

#include <thread>
#include <chrono>
#include <iostream>

#define TOPIC "rt/DemoMsgTopic"

using namespace booster::robot;
using namespace booster::common;
using namespace booster::msg;

void Handler(const void *msg) {
    const DemoMsg *demo_msg = static_cast<const DemoMsg *>(msg);
    std::cout << "Received message: "
              << demo_msg->the_bool() << ", "
              << demo_msg->the_char() << std::endl;
}

int main() {
    ChannelFactory::Instance()->Init(0);
    ChannelSubscriber<DemoMsg> channel_subscriber(TOPIC, Handler);
    channel_subscriber.InitChannel();
    std::this_thread::sleep_for(std::chrono::seconds(1));
    channel_subscriber.CloseChannel();
    int wait_sec = 3;
    std::cout << "Close channel for " << wait_sec << "s" << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(wait_sec));

    channel_subscriber.InitChannel();
    wait_sec = 5;
    std::cout << "Reopen channel for " << wait_sec << "s" << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(wait_sec));
    channel_subscriber.CloseChannel();
    wait_sec = 3;
    std::cout << "Close channel for " << wait_sec << "s" << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(wait_sec));
    channel_subscriber.InitChannel();
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}