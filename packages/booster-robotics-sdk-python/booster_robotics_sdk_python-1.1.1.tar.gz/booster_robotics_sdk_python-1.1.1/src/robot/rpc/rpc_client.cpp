#include <booster/robot/rpc/rpc_client.hpp>
#include <booster/robot/rpc/response_header.hpp>
#include <booster/robot/rpc/request_header.hpp>
#include <booster/robot/rpc/error.hpp>

#include <iostream>
#include <chrono>
#include <random>
#include <string>
#include <sstream>
#include <iomanip>

using namespace booster_msgs::msg;

namespace booster {
namespace robot {

const std::string kRequestChannelSuffix = "Req";
const std::string kResponseChannelSuffix = "Resp";

const int64_t kRpcErrorTimeout = 100;
const int64_t kRpcErrorServer = 500;
const int64_t kRpcErrorServerRequestRefused = 503;

void RpcClient::Init(const std::string &channel_name) {
    std::string req_channel_name = channel_name + kRequestChannelSuffix;
    channel_publisher_ = std::make_shared<ChannelPublisher<RpcReqMsg>>(req_channel_name);
    channel_publisher_->InitChannel();

    std::string resp_channel_name = channel_name + kResponseChannelSuffix;
    channel_subscriber_ = std::make_shared<ChannelSubscriber<RpcRespMsg>>(
        resp_channel_name,
        std::bind(&RpcClient::DdsSubMsgHandler, this, std::placeholders::_1));
    channel_subscriber_->InitChannel();
}

Response RpcClient::SendApiRequest(const Request &req, int64_t timeout_ms) {
    std::string uuid = GenUuid();
    RpcReqMsg msg;
    msg.uuid(uuid);
    std::string header_str = req.GetHeader().ToJson().dump();
    msg.header(header_str);
    msg.body(req.GetBody());
    {
        std::lock_guard<std::mutex> lock(mutex_);

        resp_map_[uuid] = std::make_pair(Response(), std::make_unique<std::condition_variable>());
    }

    channel_publisher_->Write(&msg);

    std::unique_lock<std::mutex> lock(mutex_);
    auto &entry = resp_map_[uuid];

    bool ret = entry.second->wait_for(lock, std::chrono::milliseconds(timeout_ms), [&entry] { return (entry.first.GetHeader().GetStatus() != kRpcStatusCodeInvalid); });
    if (!ret) {
        resp_map_.erase(uuid);
        ResponseHeader header = ResponseHeader();
        header.SetStatus(kRpcStatusCodeTimeout);
        Response resp = Response(header, "");
        return resp;
    }
    Response resp = entry.first;
    resp_map_.erase(uuid);
    return resp;
}

std::string RpcClient::GenUuid() {
    std::random_device rd;
    std::mt19937 rng(rd());
    std::uniform_int_distribution<int> uni(0, 15);
    std::uniform_int_distribution<int> uni8(8, 11);

    std::stringstream ss;
    ss << std::hex;
    for (int i = 0; i < 8; i++) ss << uni(rng);
    ss << "-";
    for (int i = 0; i < 4; i++) ss << uni(rng);
    ss << "-4"; // 第13位是4，表明这是一个版本4的UUID
    for (int i = 0; i < 3; i++) ss << uni(rng);
    ss << "-";
    ss << uni8(rng); // 第17位是8、9、A或B
    for (int i = 0; i < 3; i++) ss << uni(rng);
    ss << "-";
    for (int i = 0; i < 12; i++) ss << uni(rng);

    return ss.str();
}

void RpcClient::DdsSubMsgHandler(const void *msg) {
    std::unique_lock<std::mutex> lock(mutex_);
    auto resp_msg = static_cast<const RpcRespMsg *>(msg);

    auto it = resp_map_.find(resp_msg->uuid());
    if (it != resp_map_.end()) {
        nlohmann::json json = nlohmann::json::parse(resp_msg->header());
        ResponseHeader resp_header = ResponseHeader();
        resp_header.FromJson(json);

        Response resp = Response(resp_header, resp_msg->body());

        it->second.first = resp;
        it->second.second->notify_one();
    }
}

void RpcClient::Stop() {
    channel_publisher_->CloseChannel();
    channel_publisher_.reset();
    channel_subscriber_->CloseChannel();
    channel_subscriber_.reset();
}

}
} // namespace booster::robot
