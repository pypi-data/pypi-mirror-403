#include "booster_internal/common/ros_dds_bridge/bridge.hpp"

namespace booster {
namespace robot {

const std::string BOOSTER_DOMAIN_PARTICIPANT_PREFIX = "booster_participant_";
const std::string BOOSTER_DOMAIN_TOPIC_PREFIX = "rt/";
const std::string BOOSTER_DOMAIN_MSG_TYPE_PREFIX = "booster_interface::msg::dds_::";

std::string RosDdsBridge::GetBoosterDomainParticipantname(const std::string &participant_name) {
    return BOOSTER_DOMAIN_PARTICIPANT_PREFIX + participant_name;
}

std::string RosDdsBridge::GetBoosterDomainTopicName(const std::string &topic_name) {
    return BOOSTER_DOMAIN_TOPIC_PREFIX + topic_name;
}

std::string RosDdsBridge::GetBoosterDomainMsgTypeName(const std::string &msg_type_name) {
    return BOOSTER_DOMAIN_MSG_TYPE_PREFIX + msg_type_name + "_";
}
}
}