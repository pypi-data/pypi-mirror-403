#include <booster/robot/device/light/light_control_client.hpp>
#include <booster/robot/rpc/request.hpp>
#include <booster/robot/rpc/response.hpp>

#include <iostream>

namespace booster {
namespace robot {
namespace light {

void LightControlClient::Init() {
    Init("");
}

void LightControlClient::Init(const std::string &robot_name) {
    std::string name_suffix = "";
    if (!robot_name.empty()) {
        name_suffix = "/" + robot_name;
    }
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init("rt/LightControlApiTopic" + name_suffix);
}

int32_t LightControlClient::SendApiRequest(LightApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req);

    return resp.GetHeader().GetStatus();
}

int32_t LightControlClient::SendApiRequestWithResponse(LightApiId api_id, const std::string &param, Response &resp) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    resp = rpc_client_->SendApiRequest(req);

    return resp.GetHeader().GetStatus();
}

}
}
} // namespace booster::robot::light
