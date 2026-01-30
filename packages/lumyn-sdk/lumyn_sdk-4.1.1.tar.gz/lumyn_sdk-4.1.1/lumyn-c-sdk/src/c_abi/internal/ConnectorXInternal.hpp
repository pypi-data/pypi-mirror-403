#pragma once

#include "ConnectorXInternalBase.hpp"

#include <lumyn/cpp/connectorXVariant/ConnectorX.hpp>
#include <lumyn/c/lumyn_sdk.h>
#include <lumyn/c/serial_io.h>
#include <lumyn/util/hashing/IDCreator.h>

#include <atomic>
#include <algorithm>
#include <mutex>
#include <string>
#include <vector>

namespace lumyn_c_sdk::internal {

struct ModuleCallbackEntry {
    std::string module_id;
    lumyn_module_data_callback_t callback;
    void* user;
};

class ModuleState {
public:
    std::vector<ModuleCallbackEntry> callbacks;
    std::mutex mu;
};

class ConnectorXInternal : public ConnectorXInternalBase<::lumyn::device::ConnectorX> {
public:
    explicit ConnectorXInternal(cx_base_t* base_ptr)
        : ConnectorXInternalBase(base_ptr)
    {
    }

    void SetModulePollingEnabled(bool enabled) {
        module_polling_enabled_.store(enabled);
    }

    void PollModules() {
        if (!IsConnected() || !module_polling_enabled_.load()) return;

        std::vector<ModuleCallbackEntry> callbacks_copy;
        {
            std::lock_guard<std::mutex> lock(module_state_.mu);
            callbacks_copy = module_state_.callbacks;
        }

        for (const auto& entry : callbacks_copy) {
            if (!entry.callback) continue;
            const uint16_t module_key = ::lumyn::internal::IDCreator::createId(entry.module_id);
            std::vector<std::vector<uint8_t>> entries;
            if (!this->device()->GetModuleDataByHash(module_key, entries)) {
                continue;
            }
            for (const auto& payload : entries) {
                if (payload.empty()) continue;
                entry.callback(entry.module_id.c_str(), payload.data(), payload.size(), entry.user);
            }
        }
    }

    bool RegisterModuleCallback(const char* module_id, lumyn_module_data_callback_t cb, void* user) {
        std::lock_guard<std::mutex> lock(module_state_.mu);
        for (auto& entry : module_state_.callbacks) {
            if (entry.module_id == module_id) {
                entry.callback = cb;
                entry.user = user;
                return true;
            }
        }
        module_state_.callbacks.push_back({module_id, cb, user});
        return true;
    }

    bool UnregisterModuleCallback(const char* module_id) {
        std::lock_guard<std::mutex> lock(module_state_.mu);
        auto it = std::remove_if(module_state_.callbacks.begin(), module_state_.callbacks.end(),
                                 [&](const ModuleCallbackEntry& entry) {
                                     return entry.module_id == module_id;
                                 });
        if (it == module_state_.callbacks.end()) return false;
        module_state_.callbacks.erase(it, module_state_.callbacks.end());
        return true;
    }

    ModuleState& GetModuleState() { return module_state_; }

private:
    ModuleState module_state_;
    std::atomic<bool> module_polling_enabled_{true};
};

} // namespace lumyn_c_sdk::internal
