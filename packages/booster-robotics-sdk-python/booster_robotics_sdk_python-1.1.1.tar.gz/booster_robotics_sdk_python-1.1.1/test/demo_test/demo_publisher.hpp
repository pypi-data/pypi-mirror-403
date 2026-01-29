#ifndef _BOOSTER_DEMO_PUBLISHER_H_
#define _BOOSTER_DEMO_PUBLISHER_H_

#include <fastdds/dds/domain/DomainParticipant.hpp>
#include <fastdds/dds/publisher/DataWriter.hpp>
#include <fastdds/dds/publisher/DataWriterListener.hpp>
#include <fastdds/dds/publisher/Publisher.hpp>
#include <fastdds/dds/topic/TypeSupport.hpp>

class ChannelPubListener : public eprosima::fastdds::dds::DataWriterListener {
public:
    ChannelPubListener() = default;
    ~ChannelPubListener() override = default;

    void on_publication_matched(
        eprosima::fastdds::dds::DataWriter *writer,
        const eprosima::fastdds::dds::PublicationMatchedStatus &info) override;

    int matched = 0;
};

class DemoPublisher {
public:
    DemoPublisher();
    virtual ~DemoPublisher();

    bool init();
    void run();

private:
    eprosima::fastdds::dds::DomainParticipant *participant_;
    eprosima::fastdds::dds::Publisher *publisher_;
    eprosima::fastdds::dds::Topic *topic_;
    eprosima::fastdds::dds::DataWriter *writer_;
    eprosima::fastdds::dds::TypeSupport type_;
    ChannelPubListener listener_;
};

#endif