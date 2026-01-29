#include <booster/robot/b1/b1_loco_client.hpp>
#include <booster/robot/rpc/request.hpp>
#include <booster/robot/rpc/response.hpp>

#include <iostream>

namespace booster {
namespace robot {
namespace b1 {

void B1LocoClient::Init() {
    Init("");
}

void B1LocoClient::Init(const std::string &robot_name) {
    std::string name_suffix = "";
    if(!robot_name.empty()) {
        name_suffix = "/" + robot_name;
    }
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init("rt/LocoApiTopic" + name_suffix);
}

int32_t B1LocoClient::SendApiRequest(LocoApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req);
    
    return resp.GetHeader().GetStatus();
}

int32_t B1LocoClient::SendApiRequestWithResponse(LocoApiId api_id, const std::string &param, Response &resp) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    resp = rpc_client_->SendApiRequest(req);
    
    return resp.GetHeader().GetStatus();
}

}
}
} // namespace booster::robot::b1
