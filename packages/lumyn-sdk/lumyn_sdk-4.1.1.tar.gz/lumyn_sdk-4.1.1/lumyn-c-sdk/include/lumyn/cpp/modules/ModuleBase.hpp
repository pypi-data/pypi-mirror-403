#pragma once

#include <cstdint>
#include <functional>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include "lumyn/cpp/export.hpp"
#include "lumyn/cpp/modules/ModuleDataDispatcher.hpp"
#include "lumyn/cpp/connectorXVariant/ConnectorX.hpp"

namespace lumyn::modules
{
  // Note: ModuleBase is a header-only template and should NOT have LUMYN_SDK_CPP_API.
  // The derived concrete classes (AnalogInputModule, etc.) are also header-only.
  template <typename T>
  class ModuleBase
  {
  public:
    using Callback = std::function<void(const T &)>;
    using CallbackToken = uint64_t;

    ModuleBase(lumyn::device::ConnectorX &device, std::string module_id)
        : device_(device), module_id_(std::move(module_id))
    {
    }

    virtual ~ModuleBase()
    {
      Stop();
    }

    void Start()
    {
      if (running_)
        return;
      running_ = true;
      auto &dispatcher = device_.GetModuleDispatcher();
      dispatcher_token_ = dispatcher.RegisterListener(module_id_, [this](const std::vector<ModuleDataEntry> &entries)
                                                      { HandleEntries(entries); });
    }

    void Stop()
    {
      if (!running_)
        return;
      running_ = false;
      if (dispatcher_token_ != 0)
      {
        device_.GetModuleDispatcher().UnregisterListener(module_id_, dispatcher_token_);
        dispatcher_token_ = 0;
      }
    }

    std::vector<T> Get()
    {
      std::vector<T> out;
      auto entries = device_.GetModuleDispatcher().FetchEntries(module_id_);
      out.reserve(entries.size());
      for (const auto &entry : entries)
      {
        out.push_back(Parse(entry));
      }
      return out;
    }

    CallbackToken OnUpdate(Callback cb)
    {
      std::lock_guard<std::mutex> lock(callback_mu_);
      const CallbackToken token = next_callback_token_++;
      callbacks_[token] = std::move(cb);
      return token;
    }

    void RemoveCallback(CallbackToken token)
    {
      std::lock_guard<std::mutex> lock(callback_mu_);
      callbacks_.erase(token);
    }

    const std::string &GetModuleId() const
    {
      return module_id_;
    }

  protected:
    virtual T Parse(const ModuleDataEntry &entry) = 0;

  private:
    void HandleEntries(const std::vector<ModuleDataEntry> &entries)
    {
      if (entries.empty())
        return;

      std::vector<Callback> callbacks_copy;
      {
        std::lock_guard<std::mutex> lock(callback_mu_);
        callbacks_copy.reserve(callbacks_.size());
        for (const auto &item : callbacks_)
        {
          callbacks_copy.push_back(item.second);
        }
      }

      for (const auto &entry : entries)
      {
        T payload{};
        try
        {
          payload = Parse(entry);
        }
        catch (...)
        {
          continue;
        }

        for (const auto &cb : callbacks_copy)
        {
          if (!cb)
            continue;
          try
          {
            cb(payload);
          }
          catch (...)
          {
          }
        }
      }
    }

    lumyn::device::ConnectorX &device_;
    std::string module_id_;
    std::mutex callback_mu_;
    std::unordered_map<CallbackToken, Callback> callbacks_;
    CallbackToken next_callback_token_{1};
    bool running_{false};
    ModuleDataDispatcher::ListenerToken dispatcher_token_{0};
  };

} // namespace lumyn::modules
