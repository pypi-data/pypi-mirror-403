#include <booster_internal/robot/b1/b1_loco_internal_client.hpp>
#include <booster/robot/rpc/request.hpp>
#include <booster/robot/rpc/response.hpp>

#include <iostream>

namespace booster_internal {
namespace robot {
namespace b1 {

void B1LocoInternalClient::Init() {
    Init("");
}

void B1LocoInternalClient::Init(const std::string &robot_name) {
    std::string name_suffix = "";
    if(!robot_name.empty()) {
        name_suffix = "/" + robot_name;
    }
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init("rt/LocoApiTopic" + name_suffix);
}

int32_t B1LocoInternalClient::SendApiRequest(LocoInternalApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req);
    
    return resp.GetHeader().GetStatus();
}
}
}
} // namespace booster_internal::robot::b1
