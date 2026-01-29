#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>

#include "booster_internal/robot/b1/b1_loco_internal_client.hpp"
#include "booster_internal/robot/b1/b1_internal_api_const.hpp"
#include "booster_internal/robot/b1/b1_loco_internal_api.hpp"



#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;
namespace robot = booster_internal::robot;

PYBIND11_MODULE(booster_robotics_sdk_internal_python, m) {
    m.doc() = R"pbdoc(
        python binding of booster robotics sdk internal
        -----------------------
    )pbdoc";

    py::enum_<robot::b1::ControlMode>(m, "B1ControlMode")
        .value("kDefaultMode", robot::b1::ControlMode::kDefaultMode)
        .value("kAudienceMode", robot::b1::ControlMode::kAudienceMode)
        .value("kForbiddenMode", robot::b1::ControlMode::kForbiddenMode)
        .export_values();
    
    py::enum_<robot::b1::SquatDirection>(m, "B1SquatDirection")
        .value("kSquatDown", robot::b1::SquatDirection::kSquatDown)
        .value("kSquatUp", robot::b1::SquatDirection::kSquatUp)
        .export_values();

    py::class_<robot::b1::B1LocoInternalClient>(m, "B1LocoInternalClient")
        .def(py::init<>())
        .def("Init", py::overload_cast<>(&robot::b1::B1LocoInternalClient::Init))
        .def("Init", py::overload_cast<const std::string &>(&robot::b1::B1LocoInternalClient::Init))
        .def("MoveToTarget", &robot::b1::B1LocoInternalClient::MoveToTarget)
        .def("MoveToTargetWithKick", &robot::b1::B1LocoInternalClient::MoveToTargetWithKick)
        .def("MoveToTargetWithCentripetal", &robot::b1::B1LocoInternalClient::MoveToTargetWithCentripetal)
        .def("HighKick", &robot::b1::B1LocoInternalClient::HighKick)
        .def("HandAction", &robot::b1::B1LocoInternalClient::HandAction)
        .def("SetHandActionParams", &robot::b1::B1LocoInternalClient::SetHandActionParams)
        .def("StanceAction", &robot::b1::B1LocoInternalClient::StanceAction)
        .def("SquatAction", &robot::b1::B1LocoInternalClient::SquatAction)
        .def("ChangeControlMode", &robot::b1::B1LocoInternalClient::ChangeControlMode);
    


#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}