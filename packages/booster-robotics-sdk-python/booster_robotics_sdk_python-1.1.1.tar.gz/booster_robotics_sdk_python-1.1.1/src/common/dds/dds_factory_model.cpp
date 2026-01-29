#include <booster/common/dds/dds_factory_model.hpp>
#include <fastdds/rtps/transport/UDPv4TransportDescriptor.h>

#include <vector>
#include <iostream>

namespace booster {
namespace common {

class DdsConfig {
public:
    void ParseConfig(const nlohmann::json &config) {
        if (config.find("interface_white_list") != config.end()) {
            interface_white_list_ = config["interface_white_list"].get<std::vector<std::string>>();
        }
        if (config.find("domain_id") != config.end()) {
            domain_id_ = config["domain_id"].get<int32_t>();
        }
        if (config.find("use_builtin_transports") != config.end()) {
            use_builtin_transports_ = config["use_builtin_transports"].get<bool>();
        }
    };

    std::vector<std::string> interface_white_list_;
    bool use_builtin_transports_ = true;
    int32_t domain_id_;
};

DdsFactoryModel::DdsFactoryModel() {
    participant_qos_ = PARTICIPANT_QOS_DEFAULT;
    topic_qos_ = TOPIC_QOS_DEFAULT;
    publisher_qos_ = PUBLISHER_QOS_DEFAULT;
    subscriber_qos_ = SUBSCRIBER_QOS_DEFAULT;
    writer_qos_ = DATAWRITER_QOS_DEFAULT;
    reader_qos_ = DATAREADER_QOS_DEFAULT;
}

DdsFactoryModel::~DdsFactoryModel() {
}

void DdsFactoryModel::Init(uint32_t domain_id, const std::string &network_interface) {
    if (network_interface.empty()) {
        std::cout << "Network interface not specified. Will use environment variable (FASTRTPS_DEFAULT_PROFILES_FILE)." << std::endl;
        const char *env_p = std::getenv("FASTRTPS_DEFAULT_PROFILES_FILE");
        std::string path;

        if (env_p != nullptr) {
            path = env_p;
        } else {
            std::cerr << "[Warning] Environment variable FASTRTPS_DEFAULT_PROFILES_FILE is not set." << std::endl;
        }

        InitWithConfigPath(domain_id, path);
    } else {
        std::cout << "Network interface specified.";
        nlohmann::json json_config;
        json_config["domain_id"] = domain_id;

        // Split network_interface string by ","
        std::vector<std::string> interfaces;
        std::istringstream iss(network_interface);
        std::string token;
        while (std::getline(iss, token, ',')) {
            token.erase(token.begin(), std::find_if(token.begin(), token.end(), [](int ch) {
                            return !std::isspace(ch);
                        }));
            token.erase(std::find_if(token.rbegin(), token.rend(), [](int ch) {
                            return !std::isspace(ch);
                        }).base(),
                        token.end());

            if (!token.empty()) {
                interfaces.push_back(token);
            }
        }

        json_config["interface_white_list"] = interfaces;
        Init(json_config);
    }
}

void DdsFactoryModel::Init(const nlohmann::json &json_config) {
    DdsConfig config = DdsConfig();
    config.ParseConfig(json_config);
    // std::cout << "Factory Model Init: domain_id: " << config.domain_id_ << ", interface_white_list: " << config.interface_white_list_.size() << std::endl;

    bool need_udp_transport = false;
    auto transport = std::make_shared<eprosima::fastdds::rtps::UDPv4TransportDescriptor>();
    if (!config.interface_white_list_.empty()) {
        transport->interfaceWhiteList = config.interface_white_list_;
        need_udp_transport = true;
    }
    if (!config.use_builtin_transports_) {
        participant_qos_.transport().use_builtin_transports = false;
        need_udp_transport = true;
    }
    if (need_udp_transport) {
        participant_qos_.transport().user_transports.push_back(transport);
    }

    auto participant_raw_ptr = DomainParticipantFactory::get_instance()->create_participant(config.domain_id_, participant_qos_);
    if (participant_raw_ptr == nullptr) {
        std::cerr << "Failed to create participant." << std::endl;
        return;
    }

    participant_ = std::shared_ptr<DomainParticipant>(participant_raw_ptr, [](DomainParticipant *participant) {});
    auto publisher_raw_ptr = participant_->create_publisher(publisher_qos_);
    if (publisher_raw_ptr == nullptr) {
        std::cerr << "Failed to create publisher." << std::endl;
        return;
    }

    publisher_ = std::shared_ptr<Publisher>(publisher_raw_ptr, [](Publisher *publisher) {});
    auto subscriber_raw_ptr = participant_->create_subscriber(subscriber_qos_);
    if (subscriber_raw_ptr == nullptr) {
        std::cerr << "Failed to create subscriber." << std::endl;
        return;
    }
    subscriber_ = std::shared_ptr<Subscriber>(subscriber_raw_ptr, [](Subscriber *subscriber) {});
}

void DdsFactoryModel::InitDefault(int32_t domain_id) {
    auto participant_raw_ptr = DomainParticipantFactory::get_instance()->create_participant(domain_id, DomainParticipantQos());
    if (participant_raw_ptr == nullptr) {
        std::cerr << "Failed to create participant." << std::endl;
        return;
    }

    participant_ = std::shared_ptr<DomainParticipant>(participant_raw_ptr, [](DomainParticipant *participant) {});
    auto publisher_raw_ptr = participant_->create_publisher(publisher_qos_);
    if (publisher_raw_ptr == nullptr) {
        std::cerr << "Failed to create publisher." << std::endl;
        return;
    }

    publisher_ = std::shared_ptr<Publisher>(publisher_raw_ptr, [](Publisher *publisher) {});
    auto subscriber_raw_ptr = participant_->create_subscriber(subscriber_qos_);
    if (subscriber_raw_ptr == nullptr) {
        std::cerr << "Failed to create subscriber." << std::endl;
        return;
    }
    subscriber_ = std::shared_ptr<Subscriber>(subscriber_raw_ptr, [](Subscriber *subscriber) {});
}

void DdsFactoryModel::InitWithConfigPath(int32_t domain_id, const std::string &config_file_path) {
    if (eprosima::fastrtps::types::ReturnCode_t::RETCODE_OK != DomainParticipantFactory::get_instance()->load_XML_profiles_file(config_file_path)) {
        std::cerr << "Failed to load XML profiles from " << config_file_path << std::endl;
        return;
    }
    auto participant_raw_ptr = DomainParticipantFactory::get_instance()->create_participant_with_profile(domain_id, "booster_dds");
    if (participant_raw_ptr == nullptr) {
        std::cerr << "Failed to create participant." << std::endl;
        return;
    }

    participant_ = std::shared_ptr<DomainParticipant>(participant_raw_ptr, [](DomainParticipant *participant) {});
    auto publisher_raw_ptr = participant_->create_publisher(publisher_qos_);
    if (publisher_raw_ptr == nullptr) {
        std::cerr << "Failed to create publisher." << std::endl;
        return;
    }

    publisher_ = std::shared_ptr<Publisher>(publisher_raw_ptr, [](Publisher *publisher) {});
    auto subscriber_raw_ptr = participant_->create_subscriber(subscriber_qos_);
    if (subscriber_raw_ptr == nullptr) {
        std::cerr << "Failed to create subscriber." << std::endl;
        return;
    }
    subscriber_ = std::shared_ptr<Subscriber>(subscriber_raw_ptr, [](Subscriber *subscriber) {});
}

}
} // namespace booster::common