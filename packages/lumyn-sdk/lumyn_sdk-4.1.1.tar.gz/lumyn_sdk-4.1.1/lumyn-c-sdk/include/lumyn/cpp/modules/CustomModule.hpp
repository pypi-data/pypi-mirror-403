#pragma once

#include <functional>
#include <utility>

#include "lumyn/cpp/modules/ModuleBase.hpp"

namespace lumyn::modules
{
  template <typename T>
  class LUMYN_SDK_CPP_API CustomModule : public ModuleBase<T>
  {
  public:
    using Parser = std::function<T(const ModuleDataEntry &)>;

    CustomModule(lumyn::device::ConnectorX &device, std::string module_id, Parser parser)
        : ModuleBase<T>(device, std::move(module_id)), parser_(std::move(parser))
    {
    }

  protected:
    T Parse(const ModuleDataEntry &entry) override
    {
      if (parser_)
      {
        return parser_(entry);
      }
      return T{};
    }

  private:
    Parser parser_;
  };

} // namespace lumyn::modules
