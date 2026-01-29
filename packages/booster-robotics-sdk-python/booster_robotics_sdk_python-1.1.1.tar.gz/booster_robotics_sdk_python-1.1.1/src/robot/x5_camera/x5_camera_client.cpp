#include <booster/robot/x5_camera/x5_camera_client.hpp>
#include <booster/robot/x5_camera/x5_camera_api_const.hpp>
#include <booster/robot/rpc/request.hpp>
#include <booster/robot/rpc/response.hpp>

#include <iostream>

namespace booster {
namespace robot {
namespace x5_camera {

void X5CameraClient::Init() {
    rpc_client_ = std::make_shared<booster::robot::RpcClient>();
    rpc_client_->Init(kTopicX5CameraControlMode);
}

int32_t X5CameraClient::SendApiRequest(X5CameraApiId api_id, const std::string &param) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    Response resp = rpc_client_->SendApiRequest(req);
    
    return resp.GetHeader().GetStatus();
}

int32_t X5CameraClient::SendApiRequestWithResponse(X5CameraApiId api_id, const std::string &param, Response &resp) {
    RequestHeader header = RequestHeader(static_cast<int64_t>(api_id));
    Request req = Request(header, param);

    resp = rpc_client_->SendApiRequest(req);
    
    return resp.GetHeader().GetStatus();
}

}
}
} // namespace booster::robot::x5_camera
