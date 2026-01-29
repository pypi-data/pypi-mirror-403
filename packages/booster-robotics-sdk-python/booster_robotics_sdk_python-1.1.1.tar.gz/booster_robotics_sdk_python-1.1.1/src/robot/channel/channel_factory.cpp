#include <booster/robot/channel/channel_factory.hpp>
#include <booster/third_party/nlohmann_json/json.hpp>
#include <booster/common/dds/dds_entity.hpp>

namespace booster {
namespace robot {

void ChannelFactory::Init(int32_t domain_id, const std::string &network_interface) {
    nlohmann::json config;
    config["domain_id"] = domain_id;
    // Split network_interface string by ","
    std::vector<std::string> interfaces;
    std::istringstream iss(network_interface);
    std::string token;
    while (std::getline(iss, token, ',')) {
        // Remove leading and trailing whitespaces
        token.erase(token.begin(), std::find_if(token.begin(), token.end(), [](int ch) {
                        return !std::isspace(ch);
                    }));
        interfaces.push_back(token);
    }
    if (!network_interface.empty()) {
        config["interface_white_list"] = interfaces;
        config["use_builtin_transports"] = false;
        Init(config);
    } else {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!initialized_) {
            dds_factory_model_ = std::make_shared<common::DdsFactoryModel>();
            dds_factory_model_->Init(domain_id);
            initialized_ = true;
        }
    }
}

void ChannelFactory::Init(const nlohmann::json &config) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!initialized_) {
        dds_factory_model_ = std::make_shared<common::DdsFactoryModel>();
        dds_factory_model_->Init(config);
        initialized_ = true;
    }
}

void ChannelFactory::InitDefault(int32_t domain_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!initialized_) {
        dds_factory_model_ = std::make_shared<common::DdsFactoryModel>();
        dds_factory_model_->InitDefault(domain_id);
        initialized_ = true;
    }
}

void ChannelFactory::InitWithConfigPath(int32_t domain_id, const std::string &config_file_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!initialized_) {
        dds_factory_model_ = std::make_shared<common::DdsFactoryModel>();
        dds_factory_model_->InitWithConfigPath(domain_id, config_file_path);
        initialized_ = true;
    }
}

void ChannelFactory::CloseReader(const std::string &channel_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (initialized_) {
        dds_factory_model_->CloseReader(channel_name);
    }
}

void ChannelFactory::CloseWriter(const std::string &channel_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (initialized_) {
        dds_factory_model_->CloseWriter(channel_name);
    }
}

void ChannelFactory::CloseTopic(TopicPtr topic) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (initialized_) {
        dds_factory_model_->CloseTopic(topic);
    }
}

}
} // namespace booster::robot