#include "loco_rpc_server.hpp"

#include <chrono>
#include <thread>
#include <iostream>

#define TOPIC "rt/DemoRpcTopic"

using namespace booster::robot;

int main() {
    ChannelFactory::Instance()->Init(0);
    LocoRpcServer server = LocoRpcServer();
    server.Init(TOPIC);

    // 使用变量记录下次停止和启动的时间
    auto next_stop_time = std::chrono::steady_clock::now() + std::chrono::seconds(3);
    auto next_start_time = std::chrono::steady_clock::now(); // 初始化为现在，稍后会更新
    bool is_running = true;                                  // 用于跟踪服务器是否正在运行

    while (true) {
        auto now = std::chrono::steady_clock::now();

        // 检查是否到达停止时间
        if (is_running && now >= next_stop_time) {
            std::cout << "stop server" << std::endl;
            server.Stop();
            is_running = false;
            next_stop_time += std::chrono::seconds(3);       // 设置下一个停止时间
            next_start_time = now + std::chrono::seconds(4); // 设置启动时间
        }

        // 检查是否到达启动时间
        if (!is_running && now >= next_start_time) {
            std::cout << "start server" << std::endl;
            server.Init(TOPIC);
            is_running = true;
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}