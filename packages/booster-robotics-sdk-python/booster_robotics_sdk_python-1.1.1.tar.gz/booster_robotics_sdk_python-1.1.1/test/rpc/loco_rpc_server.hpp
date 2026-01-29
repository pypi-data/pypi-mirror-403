#ifndef __BOOSTER_LOCO_RPC_SERVER_HPP__
#define __BOOSTER_LOCO_RPC_SERVER_HPP__

#include <booster/robot/rpc/rpc_server.hpp>

namespace booster {
namespace robot {

class LocoRpcServer : public RpcServer {
protected:
    virtual Response HandleRequest(const Request &req) override {
        // std::cout << "Received request: " << req.GetHeader().GetApiId() << std::endl;
        return Response(ResponseHeader(0), "Hello, world!");
    }
};

}
} // namespace booster::robot

#endif