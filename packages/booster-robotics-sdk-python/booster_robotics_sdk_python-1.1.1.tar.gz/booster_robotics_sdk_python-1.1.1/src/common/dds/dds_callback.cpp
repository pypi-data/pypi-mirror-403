#include <booster/common/dds/dds_callback.hpp>

namespace booster {
namespace common {

bool DdsReaderCallback::HasMessageHandler() const {
    return handler_ != nullptr;
}

void DdsReaderCallback::OnDataAvailable(const void *data) {
    if (handler_) {
        handler_(data);
    }
}

}
} // namespace booster::common