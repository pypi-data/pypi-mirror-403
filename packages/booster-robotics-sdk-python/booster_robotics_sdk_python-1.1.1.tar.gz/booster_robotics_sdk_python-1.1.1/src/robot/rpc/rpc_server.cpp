#include <booster/robot/rpc/rpc_server.hpp>

#include <booster/robot/rpc/request_header.hpp>
#include <booster/robot/rpc/response_header.hpp>

#include <iostream>
#include <chrono>

using namespace booster_msgs::msg;

namespace booster {
namespace robot {

const std::string kRequestChannelSuffix = "Req";
const std::string kResponseChannelSuffix = "Resp";

void RpcServer::Init(const std::string &channel_name) {
    auto resp_channel_name = channel_name + kResponseChannelSuffix;
    channel_publisher_ = std::make_shared<ChannelPublisher<RpcRespMsg>>(resp_channel_name);
    channel_publisher_->InitChannel();

    auto req_channel_name = channel_name + kRequestChannelSuffix;
    channel_subscriber_ = std::make_shared<ChannelSubscriber<RpcReqMsg>>(
        req_channel_name,
        std::bind(&RpcServer::DdsReqMsgHandler, this, std::placeholders::_1), true);
    channel_subscriber_->InitChannel();
}

int32_t RpcServer::SendResponse(const std::string &uuid, const Response &resp) {
    RpcRespMsg msg;
    msg.uuid(uuid);
    msg.header(resp.GetHeader().ToJson().dump());
    msg.body(resp.GetBody());
    bool ret = channel_publisher_->Write(&msg);
    if (!ret) {
        return -1;
    }
    return 0;
}

void RpcServer::DdsReqMsgHandler(const void *msg) {
    auto req_msg = static_cast<const RpcReqMsg *>(msg);
    nlohmann::json header_json = nlohmann::json::parse(req_msg->header());
    RequestHeader req_header = RequestHeader();
    req_header.FromJson(header_json);
    Request req = Request(req_header, req_msg->body());
    Response resp = HandleRequest(req);
    SendResponse(req_msg->uuid(), resp);
}

void RpcServer::Stop() {
    channel_publisher_->CloseChannel();
    channel_publisher_.reset();
    channel_subscriber_->CloseChannel();
    channel_subscriber_.reset();
}

}
} // namespace booster::robot