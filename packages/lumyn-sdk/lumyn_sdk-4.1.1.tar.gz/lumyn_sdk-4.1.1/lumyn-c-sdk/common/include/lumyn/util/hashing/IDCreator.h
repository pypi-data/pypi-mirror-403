#pragma once

#include "MD5.h"

#include <string>
#include <string_view>

namespace lumyn::internal
{
  class IDCreator
  {
  public:
    static uint16_t createId(const std::string &id)
    {
      std::string_view id2 = std::string_view(id);

      return createId(id2);
    }

    static uint16_t createId(std::string_view id)
    {
      uint16_t val = createIdHelper(id);

      return val;
    }

  private:
    static uint16_t createIdHelper(std::string_view id)
    {
      MD5 md5;

      md5.Update(id.data(), id.size());

      uint8_t hash[16];
      md5.Finalize(hash);

      return (hash[14] << 8) | hash[15];
    }
  };
} // namespace lumyn::internal