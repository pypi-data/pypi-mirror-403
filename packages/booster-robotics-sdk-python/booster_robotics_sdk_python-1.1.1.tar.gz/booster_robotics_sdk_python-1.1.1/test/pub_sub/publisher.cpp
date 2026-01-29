#include <booster/robot/channel/channel_publisher.hpp>
#include <booster_internal/idl/demo/DemoMsg.h>

#include <thread>
#include <chrono>
#include <iostream>
#include <vector>

#define TOPIC "rt/DemoMsgTopic"
#define SLEEP_MILLI_TIME 20

using namespace booster::robot;
using namespace booster::msg;

int main(int argc, char const *argv[]) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }
    ChannelFactory::Instance()->Init(0, argv[1]);
    ChannelPublisher<DemoMsg> channel_publisher(TOPIC);

    std::vector<std::pair<int, int>> intervals = {
        {3, 2}, // 发送3秒，停止2秒
        {2, 1}, // 发送2秒，停止1秒
        {1, 1},
        // 如果需要，在此添加更多的时间间隔
    };

    while (true) {
        for (auto interval : intervals) {
            auto sending_duration = std::chrono::seconds(interval.first);
            auto pausing_duration = std::chrono::seconds(interval.second);

            auto start_time = std::chrono::steady_clock::now();
            auto now = start_time;

            channel_publisher.InitChannel();

            // 发送阶段
            while (std::chrono::duration_cast<std::chrono::seconds>(now - start_time) < sending_duration) {
                DemoMsg demo_msg;
                demo_msg.the_bool(true);
                demo_msg.the_char('a');
                channel_publisher.Write(&demo_msg);
                std::cout << "Publishing Demo Msg" << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(SLEEP_MILLI_TIME));
                now = std::chrono::steady_clock::now();
            }

            // 调用发送停止回调
            channel_publisher.CloseChannel();

            std::cout << "Pausing for " << interval.second << " seconds..." << std::endl;
            std::this_thread::sleep_for(pausing_duration);
        }
    }

    return 0;
}