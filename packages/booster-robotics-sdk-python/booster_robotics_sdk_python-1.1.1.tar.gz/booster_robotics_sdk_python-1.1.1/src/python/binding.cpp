#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>

#include "booster/robot/b1/b1_loco_client.hpp"
#include "booster/robot/b1/b1_api_const.hpp"
#include "booster/robot/b1/b1_loco_api.hpp"
#include "booster/robot/ai/api.hpp"
#include "booster/robot/ai/client.hpp"
#include "booster/robot/ai/const.hpp"

#include "booster/robot/device/light/light_control_client.hpp"
#include "booster/robot/device/light/light_control_api.hpp"
#include "booster/robot/vision/vision_client.hpp"
#include "booster/robot/vision/vision_api.hpp"

#include "booster/idl/b1/ImuState.h"
#include "booster/idl/b1/LowState.h"
#include "booster/idl/b1/MotorState.h"
#include "booster/idl/b1/LowCmd.h"
#include "booster/idl/b1/MotorCmd.h"
#include "booster/idl/b1/Odometer.h"
#include "booster/robot/common/robot_shared.hpp"
#include "booster/robot/common/entities.hpp"
#include "booster/robot/channel/channel_factory.hpp"
#include "booster/idl/b1/HandReplyData.h"
#include "booster/idl/b1/HandReplyParam.h"
#include "booster/idl/b1/HandTouchData.h"
#include "booster/idl/b1/HandTouchParam.h"
#include "booster/idl/b1/BatteryState.h"
#include "booster/idl/ai/AsrChunk.h"
#include "booster/idl/ai/Subtitle.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;
namespace robot = booster::robot;

using booster::robot::b1::B1LocoClient;
using namespace booster::robot::b1;
using namespace booster::robot::light;
using namespace booster::robot::vision;

// These are RT IDL types used for binding LowState / HandTouch
using booster_interface::msg::LowState;
using booster_interface::msg::MotorState;
using booster_interface::msg::LowCmd;
using booster_interface::msg::MotorCmd;
using booster_interface::msg::Odometer;
using booster_interface::msg::ImuState;
using booster_interface::msg::CmdType;
using booster_interface::msg::HandReplyData;
using booster_interface::msg::HandReplyParam;
using booster_interface::msg::HandTouchData;
using booster_interface::msg::HandTouchParam;
using booster_interface::msg::BatteryState;
using booster_interface::msg::AsrChunk;
using booster_interface::msg::Subtitle;

// ====================== helper templates ======================

namespace b1py_detail {

// ================ Command wrapper: int32_t (Cls::*)(Args...) =================

// Cmd<Method>::call(self, args...)
template <auto Method>
struct Cmd;

template <typename Cls, typename... Args, int32_t (Cls::*Method)(Args...)>
struct Cmd<Method> {
    static void call(Cls &self, Args... args) {
        int32_t ret = (self.*Method)(std::forward<Args>(args)...);
        if (ret != 0) {
            throw std::runtime_error(
                std::string("API call failed, code = ") + std::to_string(ret));
        }
    }
};

// ================ Query wrapper (no extra argument): int32_t (Cls::*)(Resp&) ======

template <auto Method>
struct QueryNoArg;

template <typename Cls, typename Resp, int32_t (Cls::*Method)(Resp &)>
struct QueryNoArg<Method> {
    static Resp call(Cls &self) {
        Resp resp;
        int32_t ret = (self.*Method)(resp);
        if (ret != 0) {
            throw std::runtime_error(
                std::string("API call failed, code = ") + std::to_string(ret));
        }
        return resp;
    }
};

// ================ JSON string helpers =================

template <typename T>
void add_json_str_helpers(py::class_<T> &c) {
    c.def("to_json_str", [](const T &self) {
        return self.ToJson().dump();
    });
    c.def_static("from_json_str", [](const std::string &s) {
        nlohmann::json j = nlohmann::json::parse(s);
        T obj;
        obj.FromJson(j);
        return obj;
    });
}

} // namespace b1py_detail

// ====================== Macros (method-name only) ======================

// Command API (with or without parameters)
// B1_CMD("Move", Move) -> Cmd<&B1LocoClient::Move>::call
#define B1_CMD(py_name, Method) \
    .def(py_name,               \
         &::b1py_detail::Cmd<&B1LocoClient::Method>::call)

// Query API: no request parameters, only Resp& output
// Name is unified as B1_QUERY
#define B1_QUERY(py_name, RespType, Method) \
    .def(py_name,                           \
         &::b1py_detail::QueryNoArg<&B1LocoClient::Method>::call)

// AiClient command macro (throws on error)
// AI_CMD("StartAiChat", StartAiChat) ->
//      Cmd<&booster::robot::AiClient::StartAiChat>::call
#define AI_CMD(py_name, Method) \
    .def(py_name,               \
         &::b1py_detail::Cmd<&booster::robot::AiClient::Method>::call)

// LuiClient command macro (throws on error)
// LUI_CMD("SendTtsText", SendTtsText) ->
//      Cmd<&booster::robot::AiClient::SendTtsText>::call
#define LUI_CMD(py_name, Method) \
    .def(py_name,                \
         &::b1py_detail::Cmd<&booster::robot::LuiClient::Method>::call)

// LightControlClient command macro (throws on error)
// LIGHT_CMD("SetLEDLightColor", SetLEDLightColor) ->
//      Cmd<&booster::robot::light::LightControlClient::SetLEDLightColor>::call
#define LIGHT_CMD(py_name, Method) \
    .def(py_name,                  \
         &::b1py_detail::Cmd<&booster::robot::light::LightControlClient::Method>::call)

// VisionClient command macro
// VISION_CMD("StartVisionService", StartVisionService) ->
//      Cmd<&booster::robot::vision::VisionClient::StartVisionService>::call
#define VISION_CMD(py_name, Method) \
    .def(py_name,                   \
         &::b1py_detail::Cmd<&booster::robot::vision::VisionClient::Method>::call)

// VisionClient query macro (throws on error, returns Result)
// VISION_QUERY("GetDetectionObject", std::vector<DetectResults>, GetDetectionObject) ->
//      QueryNoArg<&booster::robot::vision::VisionClient::GetDetectionObject>::call
#define VISION_QUERY(py_name, RespType, Method) \
    .def(py_name,                               \
         &::b1py_detail::QueryNoArg<&booster::robot::vision::VisionClient::Method>::call)
// ====================== RT subscription / publication classes ======================

namespace booster::robot::b1 {

class __attribute__((visibility("hidden"))) B1LowStateSubscriber
    : public std::enable_shared_from_this<B1LowStateSubscriber> {
public:
    explicit B1LowStateSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<B1LowStateSubscriber>(shared_from_this());
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<LowState>(channel_name_,
                                              [weak_this](const void *msg) {
                                                  if (auto shared_this =
                                                          weak_this.lock()) {
                                                      py::gil_scoped_acquire
                                                          acquire;
                                                      const LowState
                                                          *low_state_msg =
                                                              static_cast<
                                                                  const LowState
                                                                      *>(msg);
                                                      shared_this->py_handler_(
                                                          low_state_msg);
                                                  }
                                              });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<LowState> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = kTopicLowState;
};

class __attribute__((visibility("hidden"))) B1LowHandTouchDataSubscriber
    : public std::enable_shared_from_this<B1LowHandTouchDataSubscriber> {
public:
    explicit B1LowHandTouchDataSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<B1LowHandTouchDataSubscriber>(shared_from_this());
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<HandTouchData>(
                    channel_name_, [weak_this](const void *msg) {
                        if (auto shared_this = weak_this.lock()) {
                            py::gil_scoped_acquire acquire;
                            const HandTouchData *hand_data =
                                static_cast<const HandTouchData *>(msg);
                            shared_this->py_handler_(hand_data);
                        }
                    });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<HandTouchData> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = "rt/booster_hand_touch_data";
};

class __attribute__((visibility("hidden"))) B1LowHandDataSubscriber
    : public std::enable_shared_from_this<B1LowHandDataSubscriber> {
public:
    explicit B1LowHandDataSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<B1LowHandDataSubscriber>(shared_from_this());
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<HandReplyData>(
                    channel_name_, [weak_this](const void *msg) {
                        if (auto shared_this = weak_this.lock()) {
                            py::gil_scoped_acquire acquire;
                            const HandReplyData *hand_data =
                                static_cast<const HandReplyData *>(msg);
                            shared_this->py_handler_(hand_data);
                        }
                    });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<HandReplyData> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = "rt/booster_hand_data";
};

class __attribute__((visibility("hidden"))) B1BatteryStateSubscriber
    : public std::enable_shared_from_this<B1BatteryStateSubscriber> {
public:
    explicit B1BatteryStateSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<B1BatteryStateSubscriber>(shared_from_this());
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<BatteryState>(
                    channel_name_, [weak_this](const void *msg) {
                        if (auto shared_this = weak_this.lock()) {
                            py::gil_scoped_acquire acquire;
                            const BatteryState *battery_data =
                                static_cast<const BatteryState *>(msg);
                            shared_this->py_handler_(battery_data);
                        }
                    });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<BatteryState> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = "rt/battery_state";
};

class __attribute__((visibility("hidden"))) B1LowCmdPublisher {
public:
    explicit B1LowCmdPublisher() :
        channel_name_(kTopicJointCtrl) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        channel_ptr_ = ChannelFactory::Instance()
                           ->CreateSendChannel<LowCmd>(channel_name_);
    }

    bool Write(LowCmd *msg) {
        if (channel_ptr_) {
            return channel_ptr_->Write(msg);
        }
        return false;
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            ChannelFactory::Instance()->CloseWriter(channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    std::string channel_name_;
    ChannelPtr<LowCmd> channel_ptr_;
};

class __attribute__((visibility("hidden"))) B1OdometerStateSubscriber
    : public std::enable_shared_from_this<B1OdometerStateSubscriber> {
public:
    explicit B1OdometerStateSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<B1OdometerStateSubscriber>(shared_from_this());
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<Odometer>(channel_name_,
                                              [weak_this](const void *msg) {
                                                  if (auto shared_this =
                                                          weak_this.lock()) {
                                                      py::gil_scoped_acquire
                                                          acquire;
                                                      const Odometer
                                                          *odom_msg =
                                                              static_cast<
                                                                  const Odometer
                                                                      *>(msg);
                                                      shared_this->py_handler_(
                                                          odom_msg);
                                                  }
                                              });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<Odometer> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = kTopicOdometerState;
};

} // namespace booster::robot::b1

namespace booster::robot::ai {
class __attribute__((visibility("hidden"))) AiSubtitleSubscriber
    : public std::enable_shared_from_this<AiSubtitleSubscriber> {
public:
    explicit AiSubtitleSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<AiSubtitleSubscriber>(shared_from_this());

        // 使用 Subtitle 类型创建接收通道
        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<Subtitle>(channel_name_,
                                              [weak_this](const void *msg) {
                                                  if (auto shared_this =
                                                          weak_this.lock()) {
                                                      py::gil_scoped_acquire
                                                          acquire;
                                                      const Subtitle
                                                          *subtitle_msg =
                                                              static_cast<
                                                                  const Subtitle
                                                                      *>(msg);
                                                      shared_this->py_handler_(
                                                          subtitle_msg);
                                                  }
                                              });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<Subtitle> channel_ptr_;
    py::function py_handler_;
    // 引用 booster::robot::kTopicAiSubtitle 常量
    const std::string channel_name_ = booster::robot::kTopicAiSubtitle;
};

class __attribute__((visibility("hidden"))) LuiAsrChunkSubscriber
    : public std::enable_shared_from_this<LuiAsrChunkSubscriber> {
public:
    explicit LuiAsrChunkSubscriber(const py::function &py_handler) :
        py_handler_(py_handler) {
    }

    void InitChannel() {
        py::gil_scoped_release release;
        auto weak_this =
            std::weak_ptr<LuiAsrChunkSubscriber>(shared_from_this());

        channel_ptr_ =
            booster::robot::ChannelFactory::Instance()
                ->CreateRecvChannel<AsrChunk>(channel_name_,
                                              [weak_this](const void *msg) {
                                                  if (auto shared_this =
                                                          weak_this.lock()) {
                                                      py::gil_scoped_acquire
                                                          acquire;
                                                      const AsrChunk
                                                          *chunk_msg =
                                                              static_cast<
                                                                  const AsrChunk
                                                                      *>(msg);
                                                      shared_this->py_handler_(
                                                          chunk_msg);
                                                  }
                                              });
    }

    void CloseChannel() {
        py::gil_scoped_release release;
        if (channel_ptr_) {
            booster::robot::ChannelFactory::Instance()->CloseReader(
                channel_name_);
            channel_ptr_.reset();
        }
    }

    const std::string &GetChannelName() const {
        return channel_name_;
    }

private:
    ChannelPtr<AsrChunk> channel_ptr_;
    py::function py_handler_;
    const std::string channel_name_ = "rt/lui_asr_chunk";
};

} // namespace booster::robot::ai

// ====================== Module definition ======================

PYBIND11_MODULE(_core, m) {
    m.doc() = R"pbdoc(
        python binding of booster robotics sdk
        -----------------------
    )pbdoc";

    // ===================== ChannelFactory =====================

    py::class_<robot::ChannelFactory>(m, "ChannelFactory")
        .def_static("Instance", &robot::ChannelFactory::Instance,
                    py::return_value_policy::reference,
                    R"pbdoc(
                    Get the singleton instance of the channel factory.

                    Note: The returned instance is managed internally and should not be deleted or modified.
                    )pbdoc")
        .def("Init",
             py::overload_cast<int32_t, const std::string &>(
                 &robot::ChannelFactory::Init),
             py::arg("domain_id"), py::arg("network_interface") = "",
             R"pbdoc(
                Initialize DDS.

                Parameters
                ----------
                domain_id : int
                    Domain id of DDS.
                network_interface : str, optional
                    Network interface of DDS. Empty string means default interface.
                )pbdoc");

    // ===================== Common robot enums (from robot_shared.hpp) =====================

    py::enum_<RobotMode>(m, "RobotMode")
        .value("kUnknown", RobotMode::kUnknown)
        .value("kDamping", RobotMode::kDamping)
        .value("kPrepare", RobotMode::kPrepare)
        .value("kWalking", RobotMode::kWalking)
        .value("kCustom", RobotMode::kCustom)
        .value("kSoccer", RobotMode::kSoccer)
        .export_values();

    py::enum_<BodyControl>(m, "BodyControl")
        .value("kUnknown", BodyControl::kUnknown)
        .value("kDamping", BodyControl::kDamping)
        .value("kPrepare", BodyControl::kPrepare)
        .value("kHumanlikeGait", BodyControl::kHumanlikeGait)
        .value("kProneBody", BodyControl::kProneBody)
        .value("kSoccerGait", BodyControl::kSoccerGait)
        .value("kCustom", BodyControl::kCustom)
        .value("kGetUp", BodyControl::kGetUp)
        .value("kWholeBodyDance", BodyControl::kWholeBodyDance)
        .value("kShoot", BodyControl::kShoot)
        .value("kInsideFoot", BodyControl::kInsideFoot)
        .value("kGoalie", BodyControl::kGoalie)
        .export_values();

    py::enum_<Action>(m, "Action")
        .value("kUnknown", Action::kUnknown)
        .value("kHandShake", Action::kHandShake)
        .value("kHandWave", Action::kHandWave)
        .value("kHandControl", Action::kHandControl)
        .value("kDanceNewYear", Action::kDanceNewYear)
        .value("kDanceNezha", Action::kDanceNezha)
        .value("kDanceTowardsFuture", Action::kDanceTowardsFuture)
        .value("kGestureDabbing", Action::kGestureDabbing)
        .value("kGestureUltraman", Action::kGestureUltraman)
        .value("kGestureRespect", Action::kGestureRespect)
        .value("kGestureCheer", Action::kGestureCheer)
        .value("kGestureLuckyCat", Action::kGestureLuckyCat)
        .value("kGestureBoxing", Action::kGestureBoxing)
        .value("kZeroTorqueDrag", Action::kZeroTorqueDrag)
        .value("kRecordTraj", Action::kRecordTraj)
        .value("kRunRecordedTraj", Action::kRunRecordedTraj)
        .export_values();

    py::enum_<Frame>(m, "Frame")
        .value("kUnknown", Frame::kUnknown)
        .value("kBody", Frame::kBody)
        .value("kHead", Frame::kHead)
        .value("kLeftHand", Frame::kLeftHand)
        .value("kRightHand", Frame::kRightHand)
        .value("kLeftFoot", Frame::kLeftFoot)
        .value("kRightFoot", Frame::kRightFoot)
        .export_values();

    py::enum_<ProneBodyControlPosture>(m, "ProneBodyControlPosture")
        .value("kUnknown", ProneBodyControlPosture::kUnknown)
        .value("kInactive", ProneBodyControlPosture::kInactive)
        .value("kPushUp", ProneBodyControlPosture::kPushUp)
        .value("kLieDown", ProneBodyControlPosture::kLieDown)
        .export_values();

    // ===================== B1 API enums =====================

    py::enum_<LocoApiId>(m, "LocoApiId")
        .value("kChangeMode", LocoApiId::kChangeMode)
        .value("kMove", LocoApiId::kMove)
        .value("kRotateHead", LocoApiId::kRotateHead)
        .value("kWaveHand", LocoApiId::kWaveHand)
        .value("kRotateHeadWithDirection", LocoApiId::kRotateHeadWithDirection)
        .value("kLieDown", LocoApiId::kLieDown)
        .value("kGetUp", LocoApiId::kGetUp)
        .value("kMoveHandEndEffector", LocoApiId::kMoveHandEndEffector)
        .value("kControlGripper", LocoApiId::kControlGripper)
        .value("kGetFrameTransform", LocoApiId::kGetFrameTransform)
        .value("kSwitchHandEndEffectorControlMode",
               LocoApiId::kSwitchHandEndEffectorControlMode)
        .value("kControlDexterousHand", LocoApiId::kControlDexterousHand)
        .value("kHandshake", LocoApiId::kHandshake)
        .value("kDance", LocoApiId::kDance)
        .value("kGetMode", LocoApiId::kGetMode)
        .value("kGetStatus", LocoApiId::kGetStatus)
        .value("kPushUp", LocoApiId::kPushUp)
        .value("kPlaySound", LocoApiId::kPlaySound)
        .value("kStopSound", LocoApiId::kStopSound)
        .value("kGetRobotInfo", LocoApiId::kGetRobotInfo)
        .value("kStopHandEndEffector", LocoApiId::kStopHandEndEffector)
        .value("kShoot", LocoApiId::kShoot)
        .value("kGetUpWithMode", LocoApiId::kGetUpWithMode)
        .value("kZeroTorqueDrag", LocoApiId::kZeroTorqueDrag)
        .value("kRecordTrajectory", LocoApiId::kRecordTrajectory)
        .value("kReplayTrajectory", LocoApiId::kReplayTrajectory)
        .value("kWholeBodyDance", LocoApiId::kWholeBodyDance)
        .value("kUpperBodyCustomControl", LocoApiId::kUpperBodyCustomControl)
        .value("kLoadCustomTrainedTraj", LocoApiId::kLoadCustomTrainedTraj)
        .value("kActivateCustomTrainedTraj", LocoApiId::kActivateCustomTrainedTraj)
        .value("kUnloadCustomTrainedTraj", LocoApiId::kUnloadCustomTrainedTraj)
        .value("kResetOdometry", LocoApiId::kResetOdometry)
        .export_values();

    py::enum_<GripperControlMode>(m, "GripperControlMode")
        .value("kPosition", GripperControlMode::kPosition)
        .value("kForce", GripperControlMode::kForce)
        .export_values();

    py::enum_<DanceId>(m, "DanceId")
        .value("kNewYear", DanceId::kNewYear)
        .value("kNezha", DanceId::kNezha)
        .value("kTowardsFuture", DanceId::kTowardsFuture)
        .value("kDabbingGesture", DanceId::kDabbingGesture)
        .value("kUltramanGesture", DanceId::kUltramanGesture)
        .value("kRespectGesture", DanceId::kRespectGesture)
        .value("kCheeringGesture", DanceId::kCheeringGesture)
        .value("kLuckyCatGesture", DanceId::kLuckyCatGesture)
        .value("kStop", DanceId::kStop)
        .export_values();

    py::enum_<WholeBodyDanceId>(m, "WholeBodyDanceId")
        .value("kArbicDance", WholeBodyDanceId::kArbicDance)
        .value("kMichaelDance1", WholeBodyDanceId::kMichaelDance1)
        .value("kMichaelDance2", WholeBodyDanceId::kMichaelDance2)
        .value("kMichaelDance3", WholeBodyDanceId::kMichaelDance3)
        .value("kMoonWalk", WholeBodyDanceId::kMoonWalk)
        .value("kBoxingStyleKick", WholeBodyDanceId::kBoxingStyleKick)
        .value("kRoundhouseKick", WholeBodyDanceId::kRoundhouseKick)
        .export_values();

    // ===================== Hand and joint enums / constants =====================

    py::enum_<JointIndex>(m, "JointIndex")
        .value("kHeadYaw", JointIndex::kHeadYaw)
        .value("kHeadPitch", JointIndex::kHeadPitch)
        .value("kLeftShoulderPitch", JointIndex::kLeftShoulderPitch)
        .value("kLeftShoulderRoll", JointIndex::kLeftShoulderRoll)
        .value("kLeftElbowPitch", JointIndex::kLeftElbowPitch)
        .value("kLeftElbowYaw", JointIndex::kLeftElbowYaw)
        .value("kRightShoulderPitch", JointIndex::kRightShoulderPitch)
        .value("kRightShoulderRoll", JointIndex::kRightShoulderRoll)
        .value("kRightElbowPitch", JointIndex::kRightElbowPitch)
        .value("kRightElbowYaw", JointIndex::kRightElbowYaw)
        .value("kWaist", JointIndex::kWaist)
        .value("kLeftHipPitch", JointIndex::kLeftHipPitch)
        .value("kLeftHipRoll", JointIndex::kLeftHipRoll)
        .value("kLeftHipYaw", JointIndex::kLeftHipYaw)
        .value("kLeftKneePitch", JointIndex::kLeftKneePitch)
        .value("kCrankUpLeft", JointIndex::kCrankUpLeft)
        .value("kCrankDownLeft", JointIndex::kCrankDownLeft)
        .value("kRightHipPitch", JointIndex::kRightHipPitch)
        .value("kRightHipRoll", JointIndex::kRightHipRoll)
        .value("kRightHipYaw", JointIndex::kRightHipYaw)
        .value("kRightKneePitch", JointIndex::kRightKneePitch)
        .value("kCrankUpRight", JointIndex::kCrankUpRight)
        .value("kCrankDownRight", JointIndex::kCrankDownRight)
        .export_values();

    py::enum_<JointIndexWith7DofArm>(m, "JointIndexWith7DofArm")
        .value("kHeadYaw", JointIndexWith7DofArm::kHeadYaw)
        .value("kHeadPitch", JointIndexWith7DofArm::kHeadPitch)
        .value("kLeftShoulderPitch", JointIndexWith7DofArm::kLeftShoulderPitch)
        .value("kLeftShoulderRoll", JointIndexWith7DofArm::kLeftShoulderRoll)
        .value("kLeftElbowPitch", JointIndexWith7DofArm::kLeftElbowPitch)
        .value("kLeftElbowYaw", JointIndexWith7DofArm::kLeftElbowYaw)
        .value("kLeftWristPitch", JointIndexWith7DofArm::kLeftWristPitch)
        .value("kLeftWristYaw", JointIndexWith7DofArm::kLeftWristYaw)
        .value("kLeftHandRoll", JointIndexWith7DofArm::kLeftHandRoll)
        .value("kRightShoulderPitch",
               JointIndexWith7DofArm::kRightShoulderPitch)
        .value("kRightShoulderRoll",
               JointIndexWith7DofArm::kRightShoulderRoll)
        .value("kRightElbowPitch", JointIndexWith7DofArm::kRightElbowPitch)
        .value("kRightElbowYaw", JointIndexWith7DofArm::kRightElbowYaw)
        .value("kRightWristPitch", JointIndexWith7DofArm::kRightWristPitch)
        .value("kRightWristYaw", JointIndexWith7DofArm::kRightWristYaw)
        .value("kRightHandRoll", JointIndexWith7DofArm::kRightHandRoll)
        .value("kWaist", JointIndexWith7DofArm::kWaist)
        .value("kLeftHipPitch", JointIndexWith7DofArm::kLeftHipPitch)
        .value("kLeftHipRoll", JointIndexWith7DofArm::kLeftHipRoll)
        .value("kLeftHipYaw", JointIndexWith7DofArm::kLeftHipYaw)
        .value("kLeftKneePitch", JointIndexWith7DofArm::kLeftKneePitch)
        .value("kCrankUpLeft", JointIndexWith7DofArm::kCrankUpLeft)
        .value("kCrankDownLeft", JointIndexWith7DofArm::kCrankDownLeft)
        .value("kRightHipPitch", JointIndexWith7DofArm::kRightHipPitch)
        .value("kRightHipRoll", JointIndexWith7DofArm::kRightHipRoll)
        .value("kRightHipYaw", JointIndexWith7DofArm::kRightHipYaw)
        .value("kRightKneePitch", JointIndexWith7DofArm::kRightKneePitch)
        .value("kCrankUpRight", JointIndexWith7DofArm::kCrankUpRight)
        .value("kCrankDownRight", JointIndexWith7DofArm::kCrankDownRight)
        .export_values();

    m.attr("kJointCnt") = py::int_(kJointCnt);
    m.attr("kJointCnt7DofArm") = py::int_(kJointCnt7DofArm);

    py::enum_<HandIndex>(m, "HandIndex")
        .value("kLeftHand", HandIndex::kLeftHand)
        .value("kRightHand", HandIndex::kRightHand)
        .export_values();

    py::enum_<BoosterHandType>(m, "BoosterHandType")
        .value("kInspireHand", BoosterHandType::kInspireHand)
        .value("kInspireTouchHand", BoosterHandType::kInspireTouchHand)
        .value("kRevoHand", BoosterHandType::kRevoHand)
        .value("kUnknown", BoosterHandType::kUnknown)
        .export_values();

    py::enum_<HandAction>(m, "HandAction")
        .value("kHandOpen", HandAction::kHandOpen)
        .value("kHandClose", HandAction::kHandClose)
        .export_values();

    py::enum_<RemoteControllerEvent>(m, "RemoteControllerEvent")
        .value("NONE", RemoteControllerEvent::NONE)
        .value("AXIS", RemoteControllerEvent::AXIS)
        .value("HAT", RemoteControllerEvent::HAT)
        .value("BUTTON_DOWN", RemoteControllerEvent::BUTTON_DOWN)
        .value("BUTTON_UP", RemoteControllerEvent::BUTTON_UP)
        .value("REMOVE", RemoteControllerEvent::REMOVE)
        .export_values();

    py::enum_<JointOrder>(m, "JointOrder")
        .value("kMuJoCo", JointOrder::kMuJoCo)
        .value("kIsaacLab", JointOrder::kIsaacLab)
        .export_values();
    // ===================== AI enums / constants =====================

    py::enum_<booster::robot::AiApiId>(m, "AiApiId")
        .value("kStartAiChat", booster::robot::AiApiId::kStartAiChat)
        .value("kStopAiChat", booster::robot::AiApiId::kStopAiChat)
        .value("kSpeak", booster::robot::AiApiId::kSpeak)
        .value("kStartFaceTracking", booster::robot::AiApiId::kStartFaceTracking)
        .value("kStopFaceTracking", booster::robot::AiApiId::kStopFaceTracking)
        .export_values();

    // ===================== LUI enums / constants =====================
    py::enum_<booster::robot::LuiApiId>(m, "LuiApiId")
        .value("kStartAsr", booster::robot::LuiApiId::kStartAsr)
        .value("kStopAsr", booster::robot::LuiApiId::kStopAsr)
        .value("kStartTts", booster::robot::LuiApiId::kStartTts)
        .value("kStopTts", booster::robot::LuiApiId::kStopTts)
        .value("kSendTtsText", booster::robot::LuiApiId::kSendTtsText)
        .export_values();

    // ===================== Light enums =====================

    py::enum_<LightApiId>(m, "LightApiId")
        .value("kSetLEDLightColor", LightApiId::kSetLEDLightColor)
        .value("kStopLEDLightControl", LightApiId::kStopLEDLightControl)
        .export_values();

    // Topic constants
    m.attr("kTopicAiSubtitle") = booster::robot::kTopicAiSubtitle;
    m.attr("kBoosterRobotUserId") = booster::robot::kBoosterRobotUserId;

    m.attr("kTopicJointCtrl") = kTopicJointCtrl;
    m.attr("kTopicLowState") = kTopicLowState;
    m.attr("kTopicFallDown") = kTopicFallDown;
    m.attr("kTopicOdometerState") = kTopicOdometerState;
    m.attr("kTopicBoosterHandData") = kTopicBoosterHandData;
    m.attr("kTopicHandTouchData") = kTopicHandTouchData;
    m.attr("kTopicTF") = kTopicTF;
    m.attr("kTopicRobotStates") = kTopicRobotStates;
    m.attr("kTopicProneBodyControlStatus") =
        kTopicProneBodyControlStatus;
    m.attr("kTopicRobotReplayTrajID") = kTopicRobotReplayTrajID;

    // ===================== Vision Enums =====================

    py::enum_<VisionApiId>(m, "VisionApiId")
        .value("kStartVisionService", VisionApiId::kStartVisionService)
        .value("kStopVisionService", VisionApiId::kStopVisionService)
        .value("kGetDetectionObject", VisionApiId::kGetDetectionObject)
        .export_values();

    // ===================== Spatial geometry types =====================

    {
        auto c = py::class_<Position>(m, "Position")
                     .def(py::init<>())
                     .def(py::init<float, float, float>(),
                          py::arg("x"), py::arg("y"), py::arg("z"))
                     .def_readwrite("x", &Position::x_)
                     .def_readwrite("y", &Position::y_)
                     .def_readwrite("z", &Position::z_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<Orientation>(m, "Orientation")
                     .def(py::init<>())
                     .def(py::init<float, float, float>(),
                          py::arg("roll"), py::arg("pitch"), py::arg("yaw"))
                     .def_readwrite("roll", &Orientation::roll_)
                     .def_readwrite("pitch", &Orientation::pitch_)
                     .def_readwrite("yaw", &Orientation::yaw_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<Posture>(m, "Posture")
                     .def(py::init<>())
                     .def(py::init<const Position &, const Orientation &>(),
                          py::arg("position"), py::arg("orientation"))
                     .def_readwrite("position", &Posture::position_)
                     .def_readwrite("orientation", &Posture::orientation_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<Quaternion>(m, "Quaternion")
                     .def(py::init<>())
                     .def(py::init<float, float, float, float>(),
                          py::arg("x"), py::arg("y"), py::arg("z"),
                          py::arg("w"))
                     .def_readwrite("x", &Quaternion::x_)
                     .def_readwrite("y", &Quaternion::y_)
                     .def_readwrite("z", &Quaternion::z_)
                     .def_readwrite("w", &Quaternion::w_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<Transform>(m, "Transform")
                     .def(py::init<>())
                     .def(py::init<const Position &, const Quaternion &>(),
                          py::arg("position"), py::arg("orientation"))
                     .def_readwrite("position", &Transform::position_)
                     .def_readwrite("orientation", &Transform::orientation_);
        b1py_detail::add_json_str_helpers(c);
    }

    // ===================== B1 parameter / response types =====================

    {
        auto c = py::class_<RotateHeadParameter>(m, "RotateHeadParameter")
                     .def(py::init<>())
                     .def(py::init<float, float>(), py::arg("pitch"),
                          py::arg("yaw"))
                     .def_readwrite("pitch", &RotateHeadParameter::pitch_)
                     .def_readwrite("yaw", &RotateHeadParameter::yaw_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<ChangeModeParameter>(m, "ChangeModeParameter")
                     .def(py::init<>())
                     .def(py::init<RobotMode>(), py::arg("mode"))
                     .def_readwrite("mode", &ChangeModeParameter::mode_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GetModeResponse>(m, "GetModeResponse")
                     .def(py::init<>())
                     .def_readwrite("mode", &GetModeResponse::mode_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c =
            py::class_<GetStatusResponse>(m, "GetStatusResponse")
                .def(py::init<>())
                .def_readwrite("current_mode",
                               &GetStatusResponse::current_mode_)
                .def_readwrite("current_body_control",
                               &GetStatusResponse::current_body_control_)
                .def_readwrite("current_actions",
                               &GetStatusResponse::current_actions_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GetRobotInfoResponse>(m, "GetRobotInfoResponse")
                     .def(py::init<>())
                     .def_readwrite("name", &GetRobotInfoResponse::name_)
                     .def_readwrite("nickname",
                                    &GetRobotInfoResponse::nickname_)
                     .def_readwrite("version",
                                    &GetRobotInfoResponse::version_)
                     .def_readwrite("model", &GetRobotInfoResponse::model_)
                     .def_readwrite("serial_number", &GetRobotInfoResponse::serial_number_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<MoveParameter>(m, "MoveParameter")
                     .def(py::init<>())
                     .def(py::init<float, float, float>(), py::arg("vx"),
                          py::arg("vy"), py::arg("vyaw"))
                     .def_readwrite("vx", &MoveParameter::vx_)
                     .def_readwrite("vy", &MoveParameter::vy_)
                     .def_readwrite("vyaw", &MoveParameter::vyaw_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<RotateHeadWithDirectionParameter>(
                     m, "RotateHeadWithDirectionParameter")
                     .def(py::init<>())
                     .def(py::init<int, int>(), py::arg("pitch_direction"),
                          py::arg("yaw_direction"))
                     .def_readwrite("pitch_direction",
                                    &RotateHeadWithDirectionParameter::
                                        pitch_direction_)
                     .def_readwrite("yaw_direction",
                                    &RotateHeadWithDirectionParameter::
                                        yaw_direction_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GetUpWithModeParameter>(m, "GetUpWithModeParameter")
                     .def(py::init<>())
                     .def(py::init<RobotMode>(), py::arg("mode"))
                     .def_readwrite("mode", &GetUpWithModeParameter::mode_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<WaveHandParameter>(m, "WaveHandParameter")
                     .def(py::init<>())
                     .def(py::init<HandIndex, HandAction>(),
                          py::arg("hand_index"), py::arg("hand_action"))
                     .def_readwrite("hand_index",
                                    &WaveHandParameter::hand_index_)
                     .def_readwrite("hand_action",
                                    &WaveHandParameter::hand_action_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<HandshakeParameter>(m, "HandshakeParameter")
                     .def(py::init<>())
                     .def(py::init<HandAction>(), py::arg("hand_action"))
                     .def_readwrite("hand_action",
                                    &HandshakeParameter::hand_action_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<MoveHandEndEffectorParameter>(
                     m, "MoveHandEndEffectorParameter")
                     .def(py::init<>())
                     .def(py::init<const Posture &, int, HandIndex>(),
                          py::arg("target_posture"), py::arg("time_millis"),
                          py::arg("hand_index"))
                     .def(py::init<const Posture &, const Posture &, int,
                                   HandIndex>(),
                          py::arg("target_posture"), py::arg("aux_posture"),
                          py::arg("time_millis"), py::arg("hand_index"))
                     .def(py::init<const Posture &, int, HandIndex, bool>(),
                          py::arg("target_posture"), py::arg("time_millis"),
                          py::arg("hand_index"), py::arg("new_version"))
                     .def_readwrite("target_posture",
                                    &MoveHandEndEffectorParameter::
                                        target_posture_)
                     .def_readwrite("aux_posture",
                                    &MoveHandEndEffectorParameter::
                                        aux_posture_)
                     .def_readwrite("time_millis",
                                    &MoveHandEndEffectorParameter::
                                        time_millis_)
                     .def_readwrite("hand_index",
                                    &MoveHandEndEffectorParameter::hand_index_)
                     .def_readwrite("has_aux",
                                    &MoveHandEndEffectorParameter::has_aux_)
                     .def_readwrite("new_version",
                                    &MoveHandEndEffectorParameter::new_version_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GripperMotionParameter>(m,
                                                    "GripperMotionParameter")
                     .def(py::init<>())
                     .def(py::init<int32_t, int32_t, int32_t>(),
                          py::arg("position"), py::arg("force"),
                          py::arg("speed"))
                     .def_readwrite("position",
                                    &GripperMotionParameter::position_)
                     .def_readwrite("force", &GripperMotionParameter::force_)
                     .def_readwrite("speed", &GripperMotionParameter::speed_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<ControlGripperParameter>(m,
                                                     "ControlGripperParameter")
                     .def(py::init<>())
                     .def(py::init<const GripperMotionParameter &,
                                   GripperControlMode, HandIndex>(),
                          py::arg("motion_param"), py::arg("mode"),
                          py::arg("hand_index"))
                     .def_readwrite("motion_param",
                                    &ControlGripperParameter::motion_param_)
                     .def_readwrite("mode", &ControlGripperParameter::mode_)
                     .def_readwrite("hand_index",
                                    &ControlGripperParameter::hand_index_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GetFrameTransformParameter>(
                     m, "GetFrameTransformParameter")
                     .def(py::init<>())
                     .def(py::init<const Frame &, const Frame &>(),
                          py::arg("src"), py::arg("dst"))
                     .def_readwrite("src", &GetFrameTransformParameter::src_)
                     .def_readwrite("dst", &GetFrameTransformParameter::dst_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<SwitchHandEndEffectorControlModeParameter>(
                     m, "SwitchHandEndEffectorControlModeParameter")
                     .def(py::init<>())
                     .def(py::init<bool>(), py::arg("switch_on"))
                     .def_readwrite("switch_on",
                                    &SwitchHandEndEffectorControlModeParameter::
                                        switch_on_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<DexterousFingerParameter>(
                     m, "DexterousFingerParameter")
                     .def(py::init<>())
                     .def(py::init<int32_t, int32_t, int32_t, int32_t>(),
                          py::arg("seq"), py::arg("angle"), py::arg("force"),
                          py::arg("speed"))
                     .def_readwrite("seq", &DexterousFingerParameter::seq_)
                     .def_readwrite("angle", &DexterousFingerParameter::angle_)
                     .def_readwrite("force", &DexterousFingerParameter::force_)
                     .def_readwrite("speed", &DexterousFingerParameter::speed_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c =
            py::class_<ControlDexterousHandParameter>(
                m, "ControlDexterousHandParameter")
                .def(py::init<>())

                // Constructor without hand_type; Python side uses kInspireHand by default
                .def(py::init<const std::vector<DexterousFingerParameter> &,
                              HandIndex>(),
                     py::arg("finger_params"),
                     py::arg("hand_index"))

                // Constructor with explicit hand_type
                .def(py::init<const std::vector<DexterousFingerParameter> &,
                              HandIndex, BoosterHandType>(),
                     py::arg("finger_params"),
                     py::arg("hand_index"),
                     py::arg("hand_type"))
                .def_readwrite("finger_params",
                               &ControlDexterousHandParameter::finger_params_)
                .def_readwrite("hand_index",
                               &ControlDexterousHandParameter::hand_index_)
                .def_readwrite("hand_type",
                               &ControlDexterousHandParameter::hand_type_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<DanceParameter>(m, "DanceParameter")
                     .def(py::init<>())
                     .def(py::init<DanceId>(), py::arg("dance_id"))
                     .def_readwrite("dance_id", &DanceParameter::dance_id_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<PlaySoundParameter>(m, "PlaySoundParameter")
                     .def(py::init<>())
                     .def(py::init<const std::string &>(),
                          py::arg("sound_file_path"));
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<ReplayTrajectoryParameter>(
                     m, "ReplayTrajectoryParameter")
                     .def(py::init<>())
                     .def(py::init<const std::string &>(),
                          py::arg("traj_file_path"));
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<ZeroTorqueDragParameter>(
                     m, "ZeroTorqueDragParameter")
                     .def(py::init<>())
                     .def(py::init<bool>(), py::arg("enable"));
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<RecordTrajectoryParameter>(
                     m, "RecordTrajectoryParameter")
                     .def(py::init<>())
                     .def(py::init<bool>(), py::arg("enable"));
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<WholeBodyDanceParameter>(
                     m, "WholeBodyDanceParameter")
                     .def(py::init<>())
                     .def(py::init<WholeBodyDanceId>(), py::arg("dance_id"))
                     .def_readwrite("dance_id",
                                    &WholeBodyDanceParameter::dance_id_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<UpperBodyCustomControlParameter>(
                     m, "UpperBodyCustomControlParameter")
                     .def(py::init<>())
                     .def(py::init<bool>(), py::arg("start"))
                     .def_readwrite("start",
                                    &UpperBodyCustomControlParameter::start_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<CustomModelParams>(m, "CustomModelParams")
                     .def(py::init<>())
                     .def(py::init<const std::vector<double> &,
                                   const std::vector<double> &,
                                   const std::vector<double> &>(),
                          py::arg("action_scale"), py::arg("kp"), py::arg("kd"))
                     .def_readwrite("action_scale", &CustomModelParams::action_scale_)
                     .def_readwrite("kp", &CustomModelParams::kp_)
                     .def_readwrite("kd", &CustomModelParams::kd_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<CustomModel>(m, "CustomModel")
                     .def(py::init<>())
                     .def(py::init<const std::string &,
                                   const std::vector<CustomModelParams> &,
                                   JointOrder>(),
                          py::arg("file_path"), py::arg("params"),
                          py::arg("joint_order"))
                     .def_readwrite("file_path", &CustomModel::file_path_)
                     .def_readwrite("params", &CustomModel::params_)
                     .def_readwrite("joint_order", &CustomModel::joint_order_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<CustomTrainedTraj>(m, "CustomTrainedTraj")
                     .def(py::init<>())
                     .def(py::init<const std::string &, const CustomModel &>(),
                          py::arg("traj_file_path"), py::arg("model"))
                     .def_readwrite("traj_file_path",
                                    &CustomTrainedTraj::traj_file_path_)
                     .def_readwrite("model", &CustomTrainedTraj::model_);
        b1py_detail::add_json_str_helpers(c);
    }

    // ===================== AI configuration / parameter types =====================

    {
        auto c = py::class_<booster::robot::TtsConfig>(m, "TtsConfig")
                     .def(py::init<>())
                     .def(py::init<const std::string &,
                                   const std::vector<int8_t> &>(),
                          py::arg("voice_type"),
                          py::arg("ignore_bracket_text"))
                     .def_readwrite("voice_type",
                                    &booster::robot::TtsConfig::voice_type_)
                     .def_readwrite("ignore_bracket_text",
                                    &booster::robot::TtsConfig::ignore_bracket_text_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::LlmConfig>(m, "LlmConfig")
                     .def(py::init<>())
                     .def(py::init<const std::string &,
                                   const std::string &,
                                   const std::string &>(),
                          py::arg("system_prompt"),
                          py::arg("welcome_msg"),
                          py::arg("prompt_name") = "")
                     .def_readwrite("system_prompt",
                                    &booster::robot::LlmConfig::system_prompt_)
                     .def_readwrite("welcome_msg",
                                    &booster::robot::LlmConfig::welcome_msg_)
                     .def_readwrite("prompt_name",
                                    &booster::robot::LlmConfig::prompt_name_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::AsrConfig>(m, "AsrConfig")
                     .def(py::init<>())
                     .def(py::init<int32_t,
                                   const std::vector<std::string> &>(),
                          py::arg("interrupt_speech_duration"),
                          py::arg("interrupt_keywords"))
                     .def_readwrite("interrupt_speech_duration",
                                    &booster::robot::AsrConfig::interrupt_speech_duration_)
                     .def_readwrite("interrupt_keywords",
                                    &booster::robot::AsrConfig::interrupt_keywords_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::StartAiChatParameter>(
                     m, "StartAiChatParameter")
                     .def(py::init<>())

                     // Combined constructor
                     .def(py::init([](bool interrupt_mode,
                                      const booster::robot::TtsConfig &tts,
                                      const booster::robot::LlmConfig &llm,
                                      const booster::robot::AsrConfig &asr,
                                      bool enable_face_tracking) {
                              booster::robot::StartAiChatParameter p;
                              p.interrupt_mode_ = interrupt_mode;
                              p.tts_config_ = tts;
                              p.llm_config_ = llm;
                              p.asr_config_ = asr;
                              p.enable_face_tracking_ = enable_face_tracking;
                              return p;
                          }),
                          py::arg("interrupt_mode"),
                          py::arg("tts_config"),
                          py::arg("llm_config"),
                          py::arg("asr_config"),
                          py::arg("enable_face_tracking"))

                     .def_readwrite("interrupt_mode",
                                    &booster::robot::StartAiChatParameter::interrupt_mode_)
                     .def_readwrite("tts_config",
                                    &booster::robot::StartAiChatParameter::tts_config_)
                     .def_readwrite("llm_config",
                                    &booster::robot::StartAiChatParameter::llm_config_)
                     .def_readwrite("asr_config",
                                    &booster::robot::StartAiChatParameter::asr_config_)
                     .def_readwrite("enable_face_tracking",
                                    &booster::robot::StartAiChatParameter::enable_face_tracking_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::SpeakParameter>(m, "SpeakParameter")
                     .def(py::init<>())
                     .def(py::init<const std::string &>(), py::arg("msg"))
                     .def_readwrite("msg", &booster::robot::SpeakParameter::msg_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::Response>(m, "AiResponse")
                     .def(py::init<>());
        // No ToJson/FromJson; helper is not added
    }

    // ===================== LUI configuration / parameter types =====================
    {
        /*
                auto c = py::class_<booster::robot::TtsConfig>(m, "TtsConfig")
                     .def(py::init<>())
                     .def(py::init<const std::string &,
                                   const std::vector<int8_t> &>(),
                          py::arg("voice_type"),
                          py::arg("ignore_bracket_text"))
                     .def_readwrite("voice_type",
                                    &booster::robot::TtsConfig::voice_type_)
                     .def_readwrite("ignore_bracket_text",
                                    &booster::robot::TtsConfig::ignore_bracket_text_);
        b1py_detail::add_json_str_helpers(c);
        */
        auto c = py::class_<booster::robot::LuiTtsConfig>(m, "LuiTtsConfig")
                     .def(py::init<>())
                     .def(py::init<const std::string &>(),
                          py::arg("voice_type"))
                     .def_readwrite("voice_type",
                                    &booster::robot::LuiTtsConfig::voice_type_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<booster::robot::LuiTtsParameter>(m, "LuiTtsParameter")
                     .def(py::init<>())
                     .def(py::init<const std::string &>(),
                          py::arg("text"))
                     .def_readwrite("text",
                                    &booster::robot::LuiTtsParameter::text_);
        b1py_detail::add_json_str_helpers(c);
    }

    // ===================== Light parameters =====================

    {
        auto c = py::class_<SetLEDLightColorParameter>(m, "SetLEDLightColorParameter")
                     .def(py::init<>())
                     // Constructor for R, G, B
                     .def(py::init<uint8_t, uint8_t, uint8_t>(),
                          py::arg("r"), py::arg("g"), py::arg("b"))
                     // Constructor for Hex String (e.g., "#FF0000")
                     .def(py::init<const std::string &>(),
                          py::arg("color_hex_string"))
                     .def_readwrite("r", &SetLEDLightColorParameter::r_)
                     .def_readwrite("g", &SetLEDLightColorParameter::g_)
                     .def_readwrite("b", &SetLEDLightColorParameter::b_);
        b1py_detail::add_json_str_helpers(c);
    }
    // ===================== Vision Parameters & Results =====================

    {
        auto c = py::class_<StartVisionServiceParameter>(m, "StartVisionServiceParameter")
                     .def(py::init<>())
                     .def(py::init<bool, bool, bool>(),
                          py::arg("enable_position"), py::arg("enable_color"), py::arg("enable_face_detection"))
                     .def_readwrite("enable_position", &StartVisionServiceParameter::enable_position_)
                     .def_readwrite("enable_color", &StartVisionServiceParameter::enable_color_)
                     .def_readwrite("enable_face_detection", &StartVisionServiceParameter::enable_face_detection_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<GetDetectionObjectParameter>(m, "GetDetectionObjectParameter")
                     .def(py::init<>())
                     .def(py::init<float>(), py::arg("focus_ratio"))
                     .def_readwrite("focus_ratio", &GetDetectionObjectParameter::focus_ratio_);
        b1py_detail::add_json_str_helpers(c);
    }

    {
        auto c = py::class_<DetectResults>(m, "DetectResults")
                     .def(py::init<>())
                     .def_readwrite("xmin", &DetectResults::xmin_)
                     .def_readwrite("ymin", &DetectResults::ymin_)
                     .def_readwrite("xmax", &DetectResults::xmax_)
                     .def_readwrite("ymax", &DetectResults::ymax_)
                     .def_readwrite("position", &DetectResults::position_)
                     .def_readwrite("tag", &DetectResults::tag_)
                     .def_readwrite("conf", &DetectResults::conf_)
                     .def_readwrite("rgb_mean", &DetectResults::rgb_mean_);
        b1py_detail::add_json_str_helpers(c);
    }

    // ===================== B1LocoClient =====================

    py::class_<B1LocoClient>(m, "B1LocoClient")
        .def(py::init<>())

        // Expose with PascalCase method names
        .def("Init", static_cast<void (B1LocoClient::*)()>(
                         &B1LocoClient::Init))
        .def("InitWithName",
             static_cast<void (B1LocoClient::*)(const std::string &)>(
                 &B1LocoClient::Init),
             py::arg("robot_name"))

        // Low-level sending interface (JSON string parameter)
        .def("SendApiRequest", &B1LocoClient::SendApiRequest,
             py::arg("api_id"), py::arg("param"))

        // ===== Command APIs =====
        // clang-format off
        B1_CMD("ChangeMode", ChangeMode)
        B1_CMD("Move", Move)
        B1_CMD("RotateHead", RotateHead)
        B1_CMD("WaveHand", WaveHand)
        B1_CMD("RotateHeadWithDirection", RotateHeadWithDirection)
        B1_CMD("LieDown", LieDown)
        B1_CMD("GetUp", GetUp)
        B1_CMD("GetUpWithMode", GetUpWithMode)
        B1_CMD("Shoot", Shoot)
        B1_CMD("MoveHandEndEffectorWithAux", MoveHandEndEffectorWithAux)
        B1_CMD("MoveHandEndEffector", MoveHandEndEffector)
        B1_CMD("MoveHandEndEffectorV2", MoveHandEndEffectorV2)
        B1_CMD("StopHandEndEffector", StopHandEndEffector)
        B1_CMD("ControlGripper", ControlGripper)
        B1_CMD("SwitchHandEndEffectorControlMode",
               SwitchHandEndEffectorControlMode)
        B1_CMD("Handshake", Handshake)
        B1_CMD("ControlDexterousHand", ControlDexterousHand)
        B1_CMD("Dance", Dance)
        B1_CMD("PlaySound", PlaySound)
        B1_CMD("StopSound", StopSound)
        B1_CMD("ZeroTorqueDrag", ZeroTorqueDrag)
        B1_CMD("RecordTrajectory", RecordTrajectory)
        B1_CMD("ReplayTrajectory", ReplayTrajectory)
        B1_CMD("WholeBodyDance", WholeBodyDance)
        B1_CMD("UpperBodyCustomControl", UpperBodyCustomControl)
        B1_CMD("ResetOdometry", ResetOdometry)
        B1_CMD("ActivateCustomTrainedTraj", ActivateCustomTrainedTraj)
        B1_CMD("UnloadCustomTrainedTraj", UnloadCustomTrainedTraj)

        // ===== Query APIs (using B1_QUERY macro) =====
        B1_QUERY("GetMode", GetModeResponse, GetMode)
        B1_QUERY("GetStatus", GetStatusResponse, GetStatus)
        B1_QUERY("GetRobotInfo", GetRobotInfoResponse, GetRobotInfo)

        .def("GetFrameTransform",
             [](B1LocoClient &self, Frame src, Frame dst) {
                 Transform tf;
                 int32_t ret = self.GetFrameTransform(src, dst, tf);
                 if (ret != 0) {
                     throw std::runtime_error(
                         "API call failed, code = " + std::to_string(ret));
                 }
                 return tf;
             },
             py::arg("src"), py::arg("dst"))

        .def("LoadCustomTrainedTraj",
             [](B1LocoClient &self, const CustomTrainedTraj &traj) {
                 std::string tid;
                 int32_t ret = self.LoadCustomTrainedTraj(traj, tid);
                 if (ret != 0) {
                     throw std::runtime_error("API call failed, code = " +
                                              std::to_string(ret));
                 }
                 return tid;
             },
             py::arg("traj"),
             R"pbdoc(
                Load a custom trained trajectory.

                Parameters
                ----------
                traj : CustomTrainedTraj
                    The trajectory configuration.

                Returns
                -------
                str
                    The trajectory ID (tid) if successful.
             )pbdoc");
    // clang-format on

    // ===================== AiClient =====================

    py::class_<booster::robot::AiClient>(m, "AiClient")
        .def(py::init<>())

        .def("Init",
             static_cast<void (booster::robot::AiClient::*)()>(
                 &booster::robot::AiClient::Init),
             R"pbdoc(
                Initialize AiClient with default robot name.
             )pbdoc")

        .def("InitWithName",
             static_cast<void (booster::robot::AiClient::*)(const std::string &)>(
                 &booster::robot::AiClient::Init),
             py::arg("robot_name"),
             R"pbdoc(
                Initialize AiClient with specified robot name.
             )pbdoc")

        // Raw SendApiRequest: throws on error
        .def(
            "SendApiRequest",
            [](booster::robot::AiClient &self,
               booster::robot::AiApiId api_id,
               const std::string &param) {
                int32_t ret = self.SendApiRequest(api_id, param);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send raw AI API request (no response body).
             )pbdoc")

        // SendApiRequest with Response: returns AiResponse
        .def(
            "SendApiRequestWithResponse",
            [](booster::robot::AiClient &self,
               booster::robot::AiApiId api_id,
               const std::string &param) {
                booster::robot::Response resp;
                int32_t ret =
                    self.SendApiRequestWithResponse(api_id, param, resp);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
                return resp;
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send AI API request and get a Response object (AiResponse).
             )pbdoc")

        // ===== High-level wrappers (throw on error) =====
        // clang-format off
        AI_CMD("StartAiChat",        StartAiChat)
        AI_CMD("StopAiChat",         StopAiChat)
        AI_CMD("Speak",              Speak)
        AI_CMD("StartFaceTracking",  StartFaceTracking)
        AI_CMD("StopFaceTracking",   StopFaceTracking);
    // clang-format on

    // ===================== LuiClient =====================

    py::class_<booster::robot::LuiClient>(m, "LuiClient")
        .def(py::init<>())

        .def("Init",
             static_cast<void (booster::robot::LuiClient::*)()>(
                 &booster::robot::LuiClient::Init),
             R"pbdoc(
                Initialize LuiClient with default robot name.
             )pbdoc")

        .def("InitWithName",
             static_cast<void (booster::robot::LuiClient::*)(const std::string &)>(
                 &booster::robot::LuiClient::Init),
             py::arg("robot_name"),
             R"pbdoc(
                Initialize LuiClient with specified robot name.
             )pbdoc")

        // Raw SendApiRequest: throws on error
        .def(
            "SendApiRequest",
            [](booster::robot::LuiClient &self,
               booster::robot::LuiApiId api_id,
               const std::string &param) {
                int32_t ret = self.SendApiRequest(api_id, param);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send raw AI API request (no response body).
             )pbdoc")

        // SendApiRequest with Response: returns LuiResponse
        .def(
            "SendApiRequestWithResponse",
            [](booster::robot::LuiClient &self,
               booster::robot::LuiApiId api_id,
               const std::string &param) {
                booster::robot::Response resp;
                int32_t ret =
                    self.SendApiRequestWithResponse(api_id, param, resp);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
                return resp;
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send AI API request and get a Response object (LuiResponse).
             )pbdoc")

        // ===== High-level wrappers (throw on error) =====
        // clang-format off
        LUI_CMD("StartAsr",        StartAsr)
        LUI_CMD("StopAsr",         StopAsr)
        LUI_CMD("StartTts",        StartTts)
        LUI_CMD("StopTts",         StopTts)
        LUI_CMD("SendTtsText",     SendTtsText);
    // clang-format on

    // ===================== LightControlClient =====================

    py::class_<LightControlClient>(m, "LightControlClient")
        .def(py::init<>())

        .def("Init",
             static_cast<void (LightControlClient::*)()>(
                 &LightControlClient::Init),
             R"pbdoc(
                Initialize LightControlClient with default robot name.
             )pbdoc")

        .def("InitWithName",
             static_cast<void (LightControlClient::*)(const std::string &)>(
                 &LightControlClient::Init),
             py::arg("robot_name"),
             R"pbdoc(
                Initialize LightControlClient with specified robot name.
             )pbdoc")

        // Raw SendApiRequest: throws on error
        .def(
            "SendApiRequest",
            [](LightControlClient &self,
               LightApiId api_id,
               const std::string &param) {
                int32_t ret = self.SendApiRequest(api_id, param);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send raw Light API request (no response body).
             )pbdoc")

        // SendApiRequest with Response: returns Response object
        .def(
            "SendApiRequestWithResponse",
            [](LightControlClient &self,
               LightApiId api_id,
               const std::string &param) {
                booster::robot::Response resp;
                int32_t ret =
                    self.SendApiRequestWithResponse(api_id, param, resp);
                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
                return resp;
            },
            py::arg("api_id"), py::arg("param"),
            R"pbdoc(
                Send Light API request and get a Response object.
             )pbdoc")

        // ===== High-level wrappers (throw on error) =====
        // clang-format off
        LIGHT_CMD("SetLEDLightColor", SetLEDLightColor)
        LIGHT_CMD("StopLEDLightControl", StopLEDLightControl);
    // clang-format on
    // ===================== VisionClient =====================

    py::class_<VisionClient>(m, "VisionClient")
        .def(py::init<>())

        .def("Init",
             static_cast<void (VisionClient::*)()>(
                 &VisionClient::Init),
             R"pbdoc(
                Initialize VisionClient with default robot name.
             )pbdoc")

        .def("InitWithName",
             static_cast<void (VisionClient::*)(const std::string &)>(
                 &VisionClient::Init),
             py::arg("robot_name"),
             R"pbdoc(
                Initialize VisionClient with specified robot name.
             )pbdoc")

        // Raw SendApiRequest
        .def(
            "SendApiRequest",
            [](VisionClient &self, VisionApiId api_id, const std::string &param) {
                int32_t ret = self.SendApiRequest(api_id, param);
                if (ret != 0) {
                    throw std::runtime_error("API call failed, code = " + std::to_string(ret));
                }
            },
            py::arg("api_id"), py::arg("param"))

        // ===== Command APIs (Returns None) =====
        // clang-format off
        VISION_CMD("StartVisionService", StartVisionService)
        VISION_CMD("StopVisionService", StopVisionService)
        // clang-format on
        // 3. Get Detection Objects
        .def(
            "GetDetectionObject",
            [](VisionClient &self, float focus_ratio) {
                std::vector<DetectResults> objects;

                // [修改] 调用 C++ 接口 (注意参数顺序: 先 objects, 后 ratio)
                // 如果 Python 端没传 focus_ratio，这里就会用 binding 的默认值传进来
                int32_t ret = self.GetDetectionObject(objects, focus_ratio);

                if (ret != 0) {
                    throw std::runtime_error(
                        "API call failed, code = " + std::to_string(ret));
                }
                return objects;
            },
            // [修改] 在 Binding 层也写上默认值，方便 Python 自动补全提示
            py::arg("focus_ratio") = 0.33f,
            R"pbdoc(
                Get detected objects from the vision service.
                
                Parameters
                ----------
                focus_ratio : float, optional
                    The ratio of the center focus area (0.0 - 1.0). Default is 0.33.

                Returns
                -------
                list[DetectResults]
                    A list of detected objects.
             )pbdoc");

    // ===================== RT-layer IDL / subscription / publication bindings =====================

    py::class_<ImuState>(m, "ImuState")
        .def(py::init<>())
        .def(py::init<const ImuState &>())
        .def_property("rpy",
                      (const std::array<float, 3> &(ImuState::*)()
                           const)
                          & ImuState::rpy,
                      (void(ImuState::*)(const std::array<float, 3> &)) & ImuState::rpy)
        .def_property("gyro",
                      (const std::array<float, 3> &(ImuState::*)()
                           const)
                          & ImuState::gyro,
                      (void(ImuState::*)(const std::array<float, 3> &)) & ImuState::gyro)
        .def_property("acc",
                      (const std::array<float, 3> &(ImuState::*)()
                           const)
                          & ImuState::acc,
                      (void(ImuState::*)(const std::array<float, 3> &)) & ImuState::acc)
        .def("__eq__", &ImuState::operator==)
        .def("__ne__", &ImuState::operator!=);

    py::class_<MotorState>(m, "MotorState")
        .def(py::init<>())
        .def(py::init<const MotorState &>())
        .def_property("mode",
                      (uint8_t(MotorState::*)() const) & MotorState::mode,
                      (uint8_t & (MotorState::*)()) & MotorState::mode)
        .def_property("q", (float(MotorState::*)() const) & MotorState::q,
                      (float &(MotorState::*)()) & MotorState::q)
        .def_property("dq", (float(MotorState::*)() const) & MotorState::dq,
                      (float &(MotorState::*)()) & MotorState::dq)
        .def_property("ddq",
                      (float(MotorState::*)() const) & MotorState::ddq,
                      (float &(MotorState::*)()) & MotorState::ddq)
        .def_property("tau_est",
                      (float(MotorState::*)() const) & MotorState::tau_est,
                      (float &(MotorState::*)()) & MotorState::tau_est)
        .def_property("temperature",
                      (uint8_t(MotorState::*)() const) & MotorState::temperature,
                      (uint8_t & (MotorState::*)()) & MotorState::temperature)
        .def_property("lost",
                      (uint32_t(MotorState::*)() const) & MotorState::lost,
                      (uint32_t & (MotorState::*)()) & MotorState::lost)
        .def_property("reserve",
                      (const std::array<uint32_t, 2> &(MotorState::*)()
                           const)
                          & MotorState::reserve,
                      (std::array<uint32_t, 2> & (MotorState::*)()) & MotorState::reserve)
        .def("__eq__", &MotorState::operator==)
        .def("__ne__", &MotorState::operator!=);

    py::class_<LowState>(m, "LowState")
        .def(py::init<>())
        .def(py::init<const LowState &>())
        .def_property("imu_state",
                      (const ImuState &(LowState::*)() const) & LowState::imu_state,
                      (void(LowState::*)(const ImuState &)) & LowState::imu_state)
        .def_property("motor_state_parallel",
                      (const std::vector<MotorState> &(LowState::*)()
                           const)
                          & LowState::motor_state_parallel,
                      (void(LowState::*)(
                          const std::vector<MotorState> &))
                          & LowState::motor_state_parallel)
        .def_property("motor_state_serial",
                      (const std::vector<MotorState> &(LowState::*)()
                           const)
                          & LowState::motor_state_serial,
                      (void(LowState::*)(
                          const std::vector<MotorState> &))
                          & LowState::motor_state_serial)
        .def("__eq__", &LowState::operator==)
        .def("__ne__", &LowState::operator!=);

    py::class_<MotorCmd>(m, "MotorCmd")
        .def(py::init<>())
        .def(py::init<const MotorCmd &>())
        .def_property("mode",
                      (uint8_t(MotorCmd::*)() const) & MotorCmd::mode,
                      (void(MotorCmd::*)(uint8_t)) & MotorCmd::mode)
        .def_property("q", (float(MotorCmd::*)() const) & MotorCmd::q,
                      (void(MotorCmd::*)(float)) & MotorCmd::q)
        .def_property("dq", (float(MotorCmd::*)() const) & MotorCmd::dq,
                      (void(MotorCmd::*)(float)) & MotorCmd::dq)
        .def_property("tau", (float(MotorCmd::*)() const) & MotorCmd::tau,
                      (void(MotorCmd::*)(float)) & MotorCmd::tau)
        .def_property("kp", (float(MotorCmd::*)() const) & MotorCmd::kp,
                      (void(MotorCmd::*)(float)) & MotorCmd::kp)
        .def_property("kd", (float(MotorCmd::*)() const) & MotorCmd::kd,
                      (void(MotorCmd::*)(float)) & MotorCmd::kd)
        .def_property("weight",
                      (float(MotorCmd::*)() const) & MotorCmd::weight,
                      (void(MotorCmd::*)(float)) & MotorCmd::weight)
        .def("__eq__", &MotorCmd::operator==)
        .def("__ne__", &MotorCmd::operator!=);

    py::enum_<CmdType>(m, "LowCmdType")
        .value("PARALLEL", CmdType::PARALLEL)
        .value("SERIAL", CmdType::SERIAL)
        .export_values();

    py::class_<LowCmd>(m, "LowCmd")
        .def(py::init<>())
        .def(py::init<const LowCmd &>())
        .def_property("cmd_type",
                      (CmdType(LowCmd::*)() const) & LowCmd::cmd_type,
                      (void(LowCmd::*)(CmdType)) & LowCmd::cmd_type)
        .def_property("motor_cmd",
                      (const std::vector<MotorCmd> &(LowCmd::*)()
                           const)
                          & LowCmd::motor_cmd,
                      (void(LowCmd::*)(const std::vector<MotorCmd> &)) & LowCmd::motor_cmd)
        .def("__eq__", &LowCmd::operator==)
        .def("__ne__", &LowCmd::operator!=);

    py::class_<robot::b1::B1LowStateSubscriber,
               std::shared_ptr<robot::b1::B1LowStateSubscriber>>(
        m, "B1LowStateSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::b1::B1LowStateSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::b1::B1LowStateSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1LowStateSubscriber::GetChannelName);

    py::class_<robot::b1::B1LowHandTouchDataSubscriber,
               std::shared_ptr<robot::b1::B1LowHandTouchDataSubscriber>>(
        m, "B1LowHandTouchDataSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::b1::B1LowHandTouchDataSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::b1::B1LowHandTouchDataSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1LowHandTouchDataSubscriber::GetChannelName);

    py::class_<robot::b1::B1LowHandDataSubscriber,
               std::shared_ptr<robot::b1::B1LowHandDataSubscriber>>(
        m, "B1LowHandDataSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::b1::B1LowHandDataSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::b1::B1LowHandDataSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1LowHandDataSubscriber::GetChannelName);

    py::class_<robot::b1::B1BatteryStateSubscriber,
               std::shared_ptr<robot::b1::B1BatteryStateSubscriber>>(
        m, "B1BatteryStateSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::b1::B1BatteryStateSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::b1::B1BatteryStateSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1BatteryStateSubscriber::GetChannelName);

    py::class_<robot::b1::B1LowCmdPublisher>(m, "B1LowCmdPublisher")
        .def(py::init<>())
        .def("InitChannel",
             &robot::b1::B1LowCmdPublisher::InitChannel)
        .def("Write", &robot::b1::B1LowCmdPublisher::Write,
             py::arg("msg"))
        .def("CloseChannel",
             &robot::b1::B1LowCmdPublisher::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1LowCmdPublisher::GetChannelName);

    py::class_<Odometer>(m, "Odometer")
        .def(py::init<>())
        .def_property("x", (float(Odometer::*)() const) & Odometer::x,
                      (void(Odometer::*)(float)) & Odometer::x)
        .def_property("y", (float(Odometer::*)() const) & Odometer::y,
                      (void(Odometer::*)(float)) & Odometer::y)
        .def_property("theta",
                      (float(Odometer::*)() const) & Odometer::theta,
                      (void(Odometer::*)(float)) & Odometer::theta);

    py::class_<robot::b1::B1OdometerStateSubscriber,
               std::shared_ptr<robot::b1::B1OdometerStateSubscriber>>(
        m, "B1OdometerStateSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::b1::B1OdometerStateSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::b1::B1OdometerStateSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::b1::B1OdometerStateSubscriber::GetChannelName);

    py::class_<HandReplyParam>(m, "HandReplyParam")
        .def(py::init<>())
        .def(py::init<const HandReplyParam &>())
        .def_property("angle",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::angle,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::angle)
        .def_property("force",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::force,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::force)
        .def_property("current",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::current,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::current)
        .def_property("error",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::error,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::error)
        .def_property("status",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::status,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::status)
        .def_property("temp",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::temp,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::temp)
        .def_property("seq",
                      (int32_t(HandReplyParam::*)() const) & HandReplyParam::seq,
                      (int32_t & (HandReplyParam::*)()) & HandReplyParam::seq)
        .def("__eq__", &HandReplyParam::operator==)
        .def("__ne__", &HandReplyParam::operator!=);

    py::class_<HandReplyData>(m, "HandReplyData")
        .def(py::init<>())
        .def(py::init<const HandReplyData &>())
        .def_property("hand_index",
                      (int32_t(HandReplyData::*)() const) & HandReplyData::hand_index,
                      (int32_t & (HandReplyData::*)()) & HandReplyData::hand_index)
        .def_property("hand_type",
                      (int32_t(HandReplyData::*)() const) & HandReplyData::hand_type,
                      (int32_t & (HandReplyData::*)()) & HandReplyData::hand_type)
        .def_property(
            "hand_data",
            (const std::vector<HandReplyParam> &(HandReplyData::*)()
                 const)
                & HandReplyData::hand_data,
            (void(HandReplyData::*)(
                const std::vector<HandReplyParam> &))
                & HandReplyData::hand_data)
        .def("__eq__", &HandReplyData::operator==)
        .def("__ne__", &HandReplyData::operator!=);

    py::class_<HandTouchParam>(m, "HandTouchParam")
        .def(py::init<>())
        .def(py::init<const HandTouchParam &>())
        .def_property(
            "finger_one",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_one,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_one)
        .def_property(
            "finger_two",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_two,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_two)
        .def_property(
            "finger_three",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_three,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_three)
        .def_property(
            "finger_four",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_four,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_four)
        .def_property(
            "finger_five",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_five,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_five)
        .def_property(
            "finger_palm",
            (const std::vector<uint8_t> &(HandTouchParam::*)()
                 const)
                & HandTouchParam::finger_palm,
            (void(HandTouchParam::*)(
                const std::vector<uint8_t> &))
                & HandTouchParam::finger_palm)
        .def("__eq__", &HandTouchParam::operator==)
        .def("__ne__", &HandTouchParam::operator!=);

    py::class_<BatteryState>(m, "BatteryState")
        .def(py::init<>())
        .def(py::init<const BatteryState &>())

        .def_property("voltage",
                      (float(BatteryState::*)() const) & BatteryState::voltage,
                      (float &(BatteryState::*)()) & BatteryState::voltage)

        .def_property("current",
                      (float(BatteryState::*)() const) & BatteryState::current,
                      (float &(BatteryState::*)()) & BatteryState::current)

        .def_property("soc",
                      (float(BatteryState::*)() const) & BatteryState::soc,
                      (float &(BatteryState::*)()) & BatteryState::soc)

        .def_property("average_voltage",
                      (float(BatteryState::*)() const) & BatteryState::average_voltage,
                      (float &(BatteryState::*)()) & BatteryState::average_voltage)

        .def("__eq__", &BatteryState::operator==)
        .def("__ne__", &BatteryState::operator!=);

    py::class_<HandTouchData>(m, "HandTouchData")
        .def(py::init<>())
        .def(py::init<const HandTouchData &>())
        .def_property("hand_index",
                      (int32_t(HandTouchData::*)() const) & HandTouchData::hand_index,
                      (int32_t & (HandTouchData::*)()) & HandTouchData::hand_index)
        .def_property("hand_type",
                      (int32_t(HandTouchData::*)() const) & HandTouchData::hand_type,
                      (int32_t & (HandTouchData::*)()) & HandTouchData::hand_type)
        .def_property(
            "touch_data",
            (const HandTouchParam &(HandTouchData::*)() const) & HandTouchData::touch_data,
            (void(HandTouchData::*)(const HandTouchParam &)) & HandTouchData::touch_data)
        .def("__eq__", &HandTouchData::operator==)
        .def("__ne__", &HandTouchData::operator!=);

    py::class_<AsrChunk>(m, "AsrChunk")
        .def(py::init<>())
        .def(py::init<const AsrChunk &>())
        .def_property("text",
                      (const std::string &(AsrChunk::*)() const) & AsrChunk::text,
                      (void(AsrChunk::*)(const std::string &)) & AsrChunk::text)
        .def("__eq__", &AsrChunk::operator==)
        .def("__ne__", &AsrChunk::operator!=);

    py::class_<robot::ai::LuiAsrChunkSubscriber,
               std::shared_ptr<robot::ai::LuiAsrChunkSubscriber>>(
        m, "LuiAsrChunkSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::ai::LuiAsrChunkSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::ai::LuiAsrChunkSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::ai::LuiAsrChunkSubscriber::GetChannelName);

    py::class_<Subtitle>(m, "Subtitle")
        .def(py::init<>())
        .def(py::init<const Subtitle &>())
        // magic_number
        .def_property("magic_number",
                      (const std::string &(Subtitle::*)() const) & Subtitle::magic_number,
                      (void(Subtitle::*)(const std::string &)) & Subtitle::magic_number)
        // text
        .def_property("text",
                      (const std::string &(Subtitle::*)() const) & Subtitle::text,
                      (void(Subtitle::*)(const std::string &)) & Subtitle::text)
        // language
        .def_property("language",
                      (const std::string &(Subtitle::*)() const) & Subtitle::language,
                      (void(Subtitle::*)(const std::string &)) & Subtitle::language)
        // user_id
        .def_property("user_id",
                      (const std::string &(Subtitle::*)() const) & Subtitle::user_id,
                      (void(Subtitle::*)(const std::string &)) & Subtitle::user_id)
        // seq
        .def_property("seq",
                      (int32_t(Subtitle::*)() const) & Subtitle::seq,
                      (void(Subtitle::*)(int32_t)) & Subtitle::seq)
        // definite
        .def_property("definite",
                      (bool(Subtitle::*)() const) & Subtitle::definite,
                      (void(Subtitle::*)(bool)) & Subtitle::definite)
        // paragraph
        .def_property("paragraph",
                      (bool(Subtitle::*)() const) & Subtitle::paragraph,
                      (void(Subtitle::*)(bool)) & Subtitle::paragraph)
        // round_id
        .def_property("round_id",
                      (int32_t(Subtitle::*)() const) & Subtitle::round_id,
                      (void(Subtitle::*)(int32_t)) & Subtitle::round_id)

        // 比较运算符
        .def("__eq__", &Subtitle::operator==)
        .def("__ne__", &Subtitle::operator!=);

    py::class_<robot::ai::AiSubtitleSubscriber,
               std::shared_ptr<robot::ai::AiSubtitleSubscriber>>(
        m, "AiSubtitleSubscriber")
        .def(py::init<const py::function &>(), py::arg("handler"))
        .def("InitChannel",
             &robot::ai::AiSubtitleSubscriber::InitChannel)
        .def("CloseChannel",
             &robot::ai::AiSubtitleSubscriber::CloseChannel)
        .def("GetChannelName",
             &robot::ai::AiSubtitleSubscriber::GetChannelName);

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}