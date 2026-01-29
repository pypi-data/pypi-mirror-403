#include <iostream>
#include <booster/third_party/nlohmann_json/json.hpp>
#include <booster/robot/x5_camera/x5_camera_api_const.hpp>
#include <booster/robot/x5_camera/x5_camera_api.hpp>
#include "x5_camera_rpc.hpp"

using namespace booster::robot;
using namespace booster::robot::x5_camera;


CameraControlStatus X5CameraRpcServer::GetCachedStatus() {
    std::lock_guard<std::mutex> lock(status_mutex_);
    return cached_status_;
}

void X5CameraRpcServer::StatusMonitorThread() {
    while (!stop_thread_) {
        CameraControlStatus current_status = checkCameraControlStatus();
        {
            std::lock_guard<std::mutex> lock(status_mutex_);
            cached_status_ = current_status;
            last_update_time_ = std::chrono::steady_clock::now();
        }
      /* 
        std::unique_lock<std::mutex> lock(cv_mutex_);
        cv_.wait_for(lock, std::chrono::seconds(3), [this] {
            return stop_thread_;
        });
        */
    }
}

bool X5CameraRpcServer::executeSystemctl(const std::string& command) {
    std::string fullCommand = "systemctl " + command;
    
    //std::cout << "执行命令: " << fullCommand << std::endl;
    
    int result = std::system(fullCommand.c_str());
    
    if (result != 0) {
        return false;
    }
    
    return true;
}

bool X5CameraRpcServer::stopService(const std::string& serviceName) {
    return executeSystemctl("stop " + serviceName);
}

bool X5CameraRpcServer::startService(const std::string& serviceName) {
    return executeSystemctl("start " + serviceName);
}

bool X5CameraRpcServer::disableService(const std::string& serviceName) {
    return executeSystemctl("disable " + serviceName);
}

bool X5CameraRpcServer::enableService(const std::string& serviceName) {
    return executeSystemctl("enable " + serviceName);
}

bool X5CameraRpcServer::disableAndStopService(const std::string& serviceName) {
    bool success = true;
    
    if (!stopService(serviceName)) {
        std::cerr << "stop " << serviceName << " failed." << std::endl;
        success = false;
    }
    
    if (!disableService(serviceName)) {
        std::cerr << "disable " << serviceName << " failed." << std::endl;
        success = false;
    }
    
    return success;
}

bool X5CameraRpcServer::enableAndStartService(const std::string& serviceName) {
    bool success = true;
    
    if (!enableService(serviceName)) {
        std::cerr << "enable " << serviceName << " failed." << std::endl;
        success = false;
    }
    
    if (!startService(serviceName)) {
        std::cerr << "start " << serviceName << " failed." << std::endl;
        success = false;
    }
    
    return success;
}

void X5CameraRpcServer::reloadSystemd() {
    executeSystemctl("daemon-reload");
}

bool X5CameraRpcServer::setCameraMode(const CameraSetMode & mode) {
    const std::string normalService = "start_camera.service";
    const std::string stereoService = "start_stereo.service";
    const std::string highResService = "start_high_resolution_camera.service";
    
    bool success = true;
    
    if (mode == CameraSetMode::kCameraModeNormal) {
        std::cout << "set mode: normal" << std::endl;
        std::cout << "1. stop high relolution service" << std::endl;
        if (!stopService(highResService)) {
            std::cout << "stop " << highResService << " failed." << std::endl;
            success = false;
        }
        
        std::cout << "2. start normal service" << std::endl;
        if (!(startService(normalService) && startService(stereoService))) {
            std::cerr << "start " << normalService << " failed." << std::endl;
            return false;
        }
        
    } else if (mode == CameraSetMode::kCameraModeHighResolution) {
        std::cout << "set mode: high_resolution" << std::endl;
        std::cout << "1. stop normal service" << std::endl;
        if (!(stopService(normalService) && stopService(stereoService))) {
            std::cerr << "stop " << normalService << " failed." << std::endl;
            success = false;
        }
        
        std::cout << "2. start high resolution" << std::endl;
        if (!startService(highResService)) {
            std::cerr << "start " << highResService << " failed." << std::endl;
            return false;
        }
    } else if (mode == CameraSetMode::kCameraModeNormalEnable) {
        std::cout << "set mode: normal enable" << std::endl;
        std::cout << "1. stop & disable high relolution service" << std::endl;
        if (!disableAndStopService(highResService)) {
            std::cerr << "stoop & disable " << highResService << " failed." << std::endl;
            success = false;
        }
        
        std::cout << "2. enable & start normal service" << std::endl;
        if (!(enableAndStartService(normalService) && enableAndStartService(stereoService))) {
            std::cerr << "enable & start " << normalService << " failed" << std::endl;
            return false;
        }
        
        std::cout << "3. reload systemd config" << std::endl;
        reloadSystemd();
        
    } else if (mode == CameraSetMode::kCameraModeHighResolutionEnable) {
        std::cout << "set mode: high_resolution enable" << std::endl;
        std::cout << "1. stop & disable normal service" << std::endl;
        if (!(disableAndStopService(normalService) && disableAndStopService(stereoService))) {
            std::cerr << "stop & disable " << normalService << " failed" << std::endl;
            success = false;
        }
        
        std::cout << "2. enable & start high resolution service" << std::endl;
        if (!enableAndStartService(highResService)) {
            std::cout << "enable & start " << highResService << " failed" << std::endl;
            return false;
        }
        
        std::cout << "3. reload systemd config" << std::endl;
        reloadSystemd();
        
    } else {
        std::cout << "invalide mode '" << (int)mode << "'" << std::endl;
        return false;
    }
    
    if (success) {
        std::cout << "set mode success: " << (int)mode << std::endl;
    } else {
        std::cout << "set mode complete: " << (int)mode << " (some warnning)" << std::endl;
    }
    
    return success;
}

CameraControlStatus X5CameraRpcServer::checkCameraControlStatus() {
    bool camera1Active = isServiceActive("start_camera.service");
    bool camera2Active = isServiceActive("start_high_resolution_camera.service");
    
    if (camera1Active && camera2Active) {
        return CameraControlStatus::kCameraStatusError;
    } else if (camera1Active) {
        return CameraControlStatus::kCameraStatusNormal;
    } else if (camera2Active) {
        return CameraControlStatus::kCameraStatusHighResolution;
    } else {
        return CameraControlStatus::kCameraStatusNull;
    }
}

bool X5CameraRpcServer::isServiceActive(const std::string& serviceName) {
    std::string command = "systemctl is-active --quiet " + serviceName;
    int result = std::system(command.c_str());
    return (result == 0);
}

Response X5CameraRpcServer::HandleRequest(const Request &req) {
    X5CameraApiId api_id = static_cast<X5CameraApiId>(req.GetHeader().GetApiId());
    std::string param = "";
    int result = kRpcStatusCodeSuccess;
    switch(api_id) {
        case X5CameraApiId::kGetStatus: {
            CameraControlStatus status = cached_status_.load();
            GetStatusResponse status_res(status);
            std::string param = status_res.ToJson().dump();
            std::cout << "Get camera status from cache: " << (int)status << std::endl;
            return Response(ResponseHeader(kRpcStatusCodeSuccess), param);
            break;
        }
        case X5CameraApiId::kChangeMode: {
            auto json_param = nlohmann::json::parse(req.GetBody());
            CameraSetMode mode = static_cast<CameraSetMode>(json_param["mode"]);
            if (is_mode_change_running_.load()) {
                std::cout << "Mode change rejected, another task is running, mode: " 
                          << (int)mode << std::endl;
                result = kRpcStatusCodeBadRequest;
            } else {
                is_mode_change_running_.store(true);
                std::cout << "Starting mode change task, mode: " << (int)mode << std::endl;
                
                std::thread([this, mode]() {
                    try {
                        setCameraMode(mode);
                        std::cout << "Mode change completed, mode: " << (int)mode << std::endl;
                        
                        CameraControlStatus new_status = checkCameraControlStatus();
                        cached_status_.store(new_status);
                    } catch (const std::exception& e) {
                        std::cerr << "Mode change failed: " << e.what() << std::endl;
                    }
                    
                    is_mode_change_running_.store(false);
                }).detach();
                result = kRpcStatusCodeSuccess;
            }
            break;
        }
    }
    //return Response(ResponseHeader((int)api_id), param);
    return Response(ResponseHeader(result), param);
}

