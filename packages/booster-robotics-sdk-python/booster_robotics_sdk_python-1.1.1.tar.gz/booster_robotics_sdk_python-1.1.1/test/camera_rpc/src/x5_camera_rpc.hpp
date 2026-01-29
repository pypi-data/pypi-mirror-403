#ifndef __BOOSTER_X5_CAMERA_RPC_SERVER_HPP__
#define __BOOSTER_X5_CAMERA_RPC_SERVER_HPP__

#include <booster/robot/x5_camera/x5_camera_api_const.hpp>
#include <booster/robot/x5_camera/x5_camera_api.hpp>
#include <booster/robot/rpc/rpc_server.hpp>

namespace booster {
namespace robot {
namespace x5_camera{

class X5CameraRpcServer : public RpcServer {
public:
    X5CameraRpcServer()
        : status_thread_(&X5CameraRpcServer::StatusMonitorThread, this)
        , stop_thread_(false) {
    }

    ~X5CameraRpcServer() {
        stop_thread_ = true;
        //status_cv_.notify_one();
        
        if (status_thread_.joinable()) {
            status_thread_.join();
        }

    }

private:
    void StatusMonitorThread();
    CameraControlStatus GetCachedStatus();

    bool executeSystemctl(const std::string& command);
    bool stopService(const std::string& serviceName);
    bool startService(const std::string& serviceName);
    bool disableService(const std::string& serviceName);
    bool enableService(const std::string& serviceName);
    bool disableAndStopService(const std::string& serviceName);
    bool enableAndStartService(const std::string& serviceName);
    void reloadSystemd();
    bool X5CameraRpcServer::setCameraMode(const booster::robot::x5_camera::CameraSetMode & mode);

    CameraControlStatus checkCameraControlStatus();
    bool isServiceActive(const std::string& serviceName);

    std::atomic<x5_camera::CameraControlStatus> current_status_;
    std::atomic<CameraControlStatus> cached_status_ = CameraControlStatus::kCameraStatusNull;
    std::chrono::steady_clock::time_point last_update_time_;
    std::mutex status_mutex_;
    
    std::thread status_thread_;
    std::atomic<bool> stop_thread_;
    
    //std::mutex cv_mutex_;
    //std::condition_variable cv_;

    std::atomic<bool> is_mode_change_running_{false};
    std::atomic<CameraSetMode> mode_to_set_;
protected:
    virtual Response HandleRequest(const Request &req) override;
};

}
}
} // namespace booster::robot

#endif
