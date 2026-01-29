#include <booster/robot/rpc/rpc_client.hpp>

#include <chrono>
#include <thread>
#include <iostream>

#define TOPIC "rt/DemoRpcTopic"
#define SLEEP_MILLI_TIME 20

using namespace booster::robot;

int main() {
    ChannelFactory::Instance()->Init(0);
    RpcClient client;
    
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

            client.Init(TOPIC);

            // 发送阶段
            while (std::chrono::duration_cast<std::chrono::seconds>(now - start_time) < sending_duration) {
                RequestHeader header = RequestHeader(1111);
                Request req = Request(header, "Hello, world!");

                Response resp = client.SendApiRequest(req);
                std::cout << "Response: body = " << resp.GetBody() << ", status = " << resp.GetHeader().GetStatus() << std::endl;

                std::this_thread::sleep_for(std::chrono::milliseconds(SLEEP_MILLI_TIME));
                now = std::chrono::steady_clock::now();
            }

            // 调用发送停止回调
            client.Stop();

            std::cout << "Pausing for " << interval.second << " seconds..." << std::endl;
            std::this_thread::sleep_for(pausing_duration);
        }
    }
    return 0;
}