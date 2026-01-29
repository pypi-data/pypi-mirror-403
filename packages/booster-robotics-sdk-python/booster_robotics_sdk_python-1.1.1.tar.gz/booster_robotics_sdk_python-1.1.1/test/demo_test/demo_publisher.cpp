#include "demo_publisher.hpp"

#include <thread>
#include <chrono>

#include <fastdds/dds/domain/DomainParticipantFactory.hpp>
#include <fastdds/dds/publisher/Publisher.hpp>
#include <fastdds/dds/publisher/qos/PublisherQos.hpp>
#include <fastdds/dds/publisher/DataWriter.hpp>
#include <fastdds/dds/publisher/qos/DataWriterQos.hpp>

#include "booster_internal/idl/demo/DemoMsg.h"
#include "booster_internal/common/ros_dds_bridge/bridge.hpp"

using namespace eprosima::fastdds::dds;
using namespace booster::robot;
using namespace booster::msg;

void ChannelPubListener::on_publication_matched(
    eprosima::fastdds::dds::DataWriter *writer,
    const eprosima::fastdds::dds::PublicationMatchedStatus &info) {
    if (info.current_count_change == 1) {
        std::cout << "DataWriter matched." << std::endl;
        matched = info.total_count;
    } else if (info.current_count_change == -1) {
        std::cout << "DataWriter unmatched." << std::endl;
        matched = info.total_count;
    }
}

DemoPublisher::DemoPublisher() :
    participant_(nullptr),
    publisher_(nullptr),
    topic_(nullptr),
    writer_(nullptr),
    type_(new DemoMsg()) {
}

DemoPublisher::~DemoPublisher() {
    if (writer_ != nullptr) {
        publisher_->delete_datawriter(writer_);
    }
    if (topic_ != nullptr) {
        participant_->delete_topic(topic_);
    }
    if (publisher_ != nullptr) {
        participant_->delete_publisher(publisher_);
    }
    DomainParticipantFactory::get_instance()->delete_participant(participant_);
}

bool DemoPublisher::init() {
    /* Initialize data_ here */

    // CREATE THE PARTICIPANT
    DomainParticipantQos pqos;
    pqos.name(RosDdsBridge::GetBoosterDomainParticipantname("demo_publisher"));
    participant_ = DomainParticipantFactory::get_instance()->create_participant(0, pqos);
    if (participant_ == nullptr) {
        return false;
    }

    // REGISTER THE TYPE
    type_.register_type(participant_);

    // CREATE THE PUBLISHER
    publisher_ = participant_->create_publisher(PUBLISHER_QOS_DEFAULT, nullptr);
    if (publisher_ == nullptr) {
        return false;
    }

    // CREATE THE TOPIC
    topic_ = participant_->create_topic(
        RosDdsBridge::GetBoosterDomainTopicName("DemoMsgTopic"),
        type_.get_type_name(),
        TOPIC_QOS_DEFAULT);
    if (topic_ == nullptr) {
        return false;
    }

    // CREATE THE WRITER
    writer_ = publisher_->create_datawriter(topic_, DATAWRITER_QOS_DEFAULT, &listener_);
    if (writer_ == nullptr) {
        return false;
    }

    std::cout << "DemoMsg DataWriter created." << std::endl;
    return true;
}

void DemoPublisher::run() {
    std::cout << "DemoMsg DataWriter waiting for DataReaders." << std::endl;
    while (listener_.matched == 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(250)); // Sleep 250 ms
    }

    // Publication code

    DemoMsg msg;
    msg.the_bool(true);
    msg.the_char('a');

    /* Initialize your structure here */

    int msgsent = 0;
    char ch = 'y';
    do {
        if (ch == 'y') {
            writer_->write(&msg);
            ++msgsent;
            std::cout << "Sending sample, count=" << msgsent << ", send another sample?(y-yes,n-stop): ";
        } else if (ch == 'n') {
            std::cout << "Stopping execution " << std::endl;
            break;
        } else {
            std::cout << "Command " << ch << " not recognized, please enter \"y/n\":";
        }
    } while (std::cin >> ch);
}