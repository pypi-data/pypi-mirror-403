#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace lumyn::internal::module
{
  enum class FieldType : uint8_t
  {
    kUInt8,
    kUInt16,
    kUInt32,
    kInt8,
    kInt16,
    kInt32,
    kFloat,
    kDouble,
  };

  struct ModuleFieldDescriptor
  {
    std::string name;
    FieldType type{FieldType::kUInt8};
  };

  struct ModulePayloadDescriptor
  {
    std::string type;
    std::vector<ModuleFieldDescriptor> fields;
  };
} // namespace lumyn::internal::module
