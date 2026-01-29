#include "demo_subscriber.hpp"

#include <string>

#include <fastdds/dds/domain/DomainParticipantFactory.hpp>
#include <fastdds/dds/subscriber/DataReader.hpp>
#include <fastdds/dds/subscriber/SampleInfo.hpp>
#include <fastdds/dds/subscriber/Subscriber.hpp>
#include <fastdds/dds/subscriber/qos/DataReaderQos.hpp>

#include "booster_internal/idl/demo/DemoMsg.h"
#include "booster_internal/common/ros_dds_bridge/bridge.hpp"

using namespace eprosima::fastdds::dds;
using namespace booster::robot;
using namespace booster::msg;

void ChannelSubListener::on_subscription_matched(
    DataReader *reader,
    const SubscriptionMatchedStatus &info) {
    if (info.current_count_change == 1) {
        matched = info.total_count;
    } else if (info.current_count_change == -1) {
        matched = info.total_count;
    }
}

void ChannelSubListener::on_data_available(
    DataReader *reader) {
    DemoMsg msg;
    SampleInfo info;
    if (reader->take_next_sample(&msg, &info) == ReturnCode_t::RETCODE_OK) {
        if (info.valid_data) {
            samples++;
            std::cout << "Received message: " << msg.the_bool() << ", " << msg.the_char() << std::endl;
        }
    }
}

DemoSubscriber::DemoSubscriber() :
    participant_(nullptr),
    subscriber_(nullptr), topic_(nullptr), reader_(nullptr), type_(new DemoMsg()) {
}

DemoSubscriber::~DemoSubscriber() {
    if (reader_ != nullptr) {
        subscriber_->delete_datareader(reader_);
    }
    if (topic_ != nullptr) {
        participant_->delete_topic(topic_);
    }
    if (subscriber_ != nullptr) {
        participant_->delete_subscriber(subscriber_);
    }
    DomainParticipantFactory::get_instance()->delete_participant(participant_);
}

bool DemoSubscriber::init() {
    // Create the participant
    DomainParticipantQos pqos;
    pqos.name(RosDdsBridge::GetBoosterDomainParticipantname("demo_subscriber"));
    participant_ = DomainParticipantFactory::get_instance()->create_participant(0, pqos);
    if (participant_ == nullptr) {
        return false;
    }

    // Register the type
    type_.register_type(participant_);

    // Create the subscriber
    subscriber_ = participant_->create_subscriber(SUBSCRIBER_QOS_DEFAULT, nullptr);
    if (subscriber_ == nullptr) {
        return false;
    }

    // Create the topic
    topic_ = participant_->create_topic(
        RosDdsBridge::GetBoosterDomainTopicName("DemoMsgTopic"),
        type_.get_type_name(),
        TOPIC_QOS_DEFAULT);
    if (topic_ == nullptr) {
        return false;
    }

    // Create the DataReader
    DataReaderQos rqos;
    rqos.reliability().kind = RELIABLE_RELIABILITY_QOS;
    reader_ = subscriber_->create_datareader(topic_, rqos, &listener_);
    if (reader_ == nullptr) {
        return false;
    }

    return true;
}

void DemoSubscriber::run() {
    std::cout << "Waiting for Data, press Enter to stop the DataReader. " << std::endl;
    std::cin.ignore();
    std::cout << "Shutting down the Subscriber." << std::endl;
}
