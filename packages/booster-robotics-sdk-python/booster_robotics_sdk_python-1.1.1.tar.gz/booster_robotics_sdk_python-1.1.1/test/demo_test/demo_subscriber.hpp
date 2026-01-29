#ifndef _BOOSTER_DEMO_SUBSCRIBER_H_
#define _BOOSTER_DEMO_SUBSCRIBER_H_

#include <fastdds/dds/domain/DomainParticipant.hpp>
#include <fastdds/dds/subscriber/DataReader.hpp>
#include <fastdds/dds/subscriber/DataReaderListener.hpp>
#include <fastdds/dds/subscriber/Subscriber.hpp>

class ChannelSubListener : public eprosima::fastdds::dds::DataReaderListener {
public:
    ChannelSubListener() = default;
    ~ChannelSubListener() override = default;

    void on_data_available(
        eprosima::fastdds::dds::DataReader *reader) override;

    void on_subscription_matched(
        eprosima::fastdds::dds::DataReader *reader,
        const eprosima::fastdds::dds::SubscriptionMatchedStatus &info) override;

    int matched = 0;
    uint32_t samples = 0;

};

class DemoSubscriber {
public:
    DemoSubscriber();

    virtual ~DemoSubscriber();

    //! Initialize the subscriber
    bool init();

    //! RUN the subscriber
    void run();

private:
    eprosima::fastdds::dds::DomainParticipant *participant_;
    eprosima::fastdds::dds::Subscriber *subscriber_;
    eprosima::fastdds::dds::Topic *topic_;
    eprosima::fastdds::dds::DataReader *reader_;
    eprosima::fastdds::dds::TypeSupport type_;
    ChannelSubListener listener_;
};

#endif