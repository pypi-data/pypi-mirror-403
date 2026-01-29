#include <booster/robot/ai/client.hpp>
#include <booster/robot/rpc/request.hpp>
#include <booster/robot/rpc/response.hpp>

#include <iostream>

namespace booster {
namespace robot {

void AiClient::Init() {
    Init("");
}

void AiClient::Init(const std::string &robot_name) {
    std::string name_suffix = "";
    if (!robot_name.empty()) {
        name_suffix = "/" + robot_name;
    }
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init("rt/AiApiTopic" + name_suffix);
}

int32_t AiClient::SendApiRequest(AiApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req, 10000);

    return resp.GetHeader().GetStatus();
}

int32_t AiClient::SendApiRequestWithResponse(AiApiId api_id, const std::string &param, Response &resp) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    resp = rpc_client_->SendApiRequest(req, 10000);

    return resp.GetHeader().GetStatus();
}

void LuiClient::Init() {
    Init("");
}

void LuiClient::Init(const std::string &robot_name) {
    std::string name_suffix = "";
    if (!robot_name.empty()) {
        name_suffix = "/" + robot_name;
    }
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init("rt/LuiApiTopic" + name_suffix);
}

int32_t LuiClient::SendApiRequest(LuiApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req, 10000);

    return resp.GetHeader().GetStatus();
}

int32_t LuiClient::SendApiRequestWithResponse(LuiApiId api_id, const std::string &param, Response &resp) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    resp = rpc_client_->SendApiRequest(req, 10000);

    return resp.GetHeader().GetStatus();
}
}
} // namespace booster::robot::b1
