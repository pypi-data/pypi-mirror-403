#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <functional>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#include "lumyn/cpp/export.hpp"
#include "lumyn/c/lumyn_modules.h"

namespace lumyn::device
{
  class ConnectorX;
}

namespace lumyn::modules
{

  struct ModuleDataEntry
  {
    std::vector<uint8_t> data;
    size_t len{0};
  };

  class LUMYN_SDK_CPP_API ModuleDataDispatcher
  {
  public:
    using ModuleDataListener = std::function<void(const std::vector<ModuleDataEntry> &)>;
    using ListenerToken = uint64_t;

    explicit ModuleDataDispatcher(lumyn::device::ConnectorX &device, cx_base_t *c_base)
        : device_(device), c_base_(c_base), use_c_api_(c_base != nullptr)
    {
    }

    ~ModuleDataDispatcher()
    {
      Stop();
      std::lock_guard<std::mutex> lock(mu_);
      listeners_.clear();
    }

    ListenerToken RegisterListener(std::string_view module_id, ModuleDataListener listener)
    {
      if (module_id.empty() || !listener)
        return 0;

      std::lock_guard<std::mutex> lock(mu_);
      const ListenerToken token = next_token_++;
      auto &entry = listeners_[std::string(module_id)];
      entry[token] = std::move(listener);
      if (use_c_api_ && entry.size() == 1)
      {
        lumyn_RegisterModule(c_base_, std::string(module_id).c_str(), &ModuleDataDispatcher::HandleModuleCallback, this);
      }
      Start();
      return token;
    }

    void UnregisterListener(std::string_view module_id, ListenerToken token)
    {
      if (module_id.empty() || token == 0)
        return;
      std::lock_guard<std::mutex> lock(mu_);
      auto it = listeners_.find(std::string(module_id));
      if (it == listeners_.end())
        return;
      it->second.erase(token);
      if (it->second.empty())
      {
        if (use_c_api_)
        {
          lumyn_UnregisterModule(c_base_, it->first.c_str());
        }
        listeners_.erase(it);
      }
    }

    void SetPollIntervalMs(int interval_ms)
    {
      poll_interval_ms_.store(interval_ms > 0 ? interval_ms : 1);
    }

    int GetPollIntervalMs() const
    {
      return poll_interval_ms_.load();
    }

    bool IsPolling() const
    {
      return polling_.load();
    }

    void Start()
    {
      bool expected = false;
      if (!polling_.compare_exchange_strong(expected, true))
        return;
      if (use_c_api_)
      {
        lumyn_SetModulePollingEnabled(c_base_, true);
      }
      poll_thread_ = std::thread([this]() { PollLoop(); });
    }

    void Stop()
    {
      polling_.store(false);
      if (poll_thread_.joinable())
      {
        poll_thread_.join();
      }
    }

    std::vector<ModuleDataEntry> FetchEntries(std::string_view module_id)
    {
      std::vector<ModuleDataEntry> entries;
      if (module_id.empty())
        return entries;

      if (use_c_api_)
      {
        std::lock_guard<std::mutex> lock(mu_);
        auto it = pending_.find(std::string(module_id));
        if (it == pending_.end() || it->second.empty())
          return entries;
        entries.swap(it->second);
        return entries;
      }

      std::vector<std::vector<uint8_t>> raw;
      if (!device_.GetModuleDataByName(module_id, raw))
        return entries;

      entries.reserve(raw.size());
      for (auto &payload : raw)
      {
        ModuleDataEntry entry;
        entry.len = payload.size();
        entry.data = std::move(payload);
        entries.push_back(std::move(entry));
      }
      return entries;
    }

  private:
    void PollLoop()
    {
      while (polling_.load())
      {
        if (use_c_api_)
        {
          lumyn_PollModules(c_base_);
        }
        else
        {
          std::vector<std::pair<std::string, std::vector<ModuleDataListener>>> snapshot;
          {
            std::lock_guard<std::mutex> lock(mu_);
            snapshot.reserve(listeners_.size());
            for (const auto &item : listeners_)
            {
              if (item.second.empty())
                continue;
              std::vector<ModuleDataListener> listeners;
              listeners.reserve(item.second.size());
              for (const auto &entry : item.second)
              {
                listeners.push_back(entry.second);
              }
              snapshot.emplace_back(item.first, std::move(listeners));
            }
          }

          for (const auto &item : snapshot)
          {
            const auto &module_id = item.first;
            const auto &listeners = item.second;
            if (listeners.empty())
              continue;
            auto entries = FetchEntries(module_id);
            if (entries.empty())
              continue;
            for (const auto &listener : listeners)
            {
              if (!listener)
                continue;
              listener(entries);
            }
          }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(poll_interval_ms_.load()));
      }
    }

    static void HandleModuleCallback(const char *module_id, const uint8_t *data, size_t len, void *user)
    {
      if (!user || !module_id || !data || len == 0)
        return;
      auto *self = static_cast<ModuleDataDispatcher *>(user);
      self->DispatchFromCallback(module_id, data, len);
    }

    void DispatchFromCallback(const char *module_id, const uint8_t *data, size_t len)
    {
      std::vector<ModuleDataListener> listeners_copy;
      std::vector<ModuleDataEntry> entries;
      {
        std::lock_guard<std::mutex> lock(mu_);
        auto it = listeners_.find(std::string(module_id));
        if (it != listeners_.end())
        {
          listeners_copy.reserve(it->second.size());
          for (const auto &entry : it->second)
          {
            listeners_copy.push_back(entry.second);
          }
        }

        ModuleDataEntry entry;
        entry.len = len;
        entry.data.assign(data, data + len);
        pending_[std::string(module_id)].push_back(std::move(entry));
      }

      if (listeners_copy.empty())
        return;
      entries = FetchEntries(module_id);
      if (entries.empty())
        return;
      for (const auto &listener : listeners_copy)
      {
        if (!listener)
          continue;
        listener(entries);
      }
    }

    lumyn::device::ConnectorX &device_;
    cx_base_t *c_base_{nullptr};
    bool use_c_api_{false};
    std::mutex mu_;
    std::unordered_map<std::string, std::unordered_map<ListenerToken, ModuleDataListener>> listeners_;
    std::unordered_map<std::string, std::vector<ModuleDataEntry>> pending_;
    std::atomic<bool> polling_{false};
    std::thread poll_thread_;
    std::atomic<int> poll_interval_ms_{10};
    ListenerToken next_token_{1};
  };

} // namespace lumyn::modules
