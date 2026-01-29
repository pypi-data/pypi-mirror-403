#include <booster/robot/channel/channel_publisher.hpp>
#include "temp/Header.h"
#include <booster_internal/idl/demo/DemoMsg.h>

#include <thread>
#include <chrono>
#include <iostream>
#include <vector>

#define TOPIC "rt/TestMsgTopic"
#define SLEEP_MILLI_TIME 20

using namespace booster::robot;
using namespace booster::msg;
using namespace std_msgs::msg;

int main(int argc, char const *argv[]) {
    ChannelFactory::Instance()->Init(0, "127.0.0.1");
    ChannelPublisher<Header> channel_publisher(TOPIC);
    channel_publisher.InitChannel();

    while (true) {
        Header demo_msg;
        demo_msg.frame_id("framegg");
        // demo_msg.cmd_type(PARALLEL);
        // demo_msg.the_bool(true);
        channel_publisher.Write(&demo_msg);
        std::cout << "Publishing Test Msg" << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}