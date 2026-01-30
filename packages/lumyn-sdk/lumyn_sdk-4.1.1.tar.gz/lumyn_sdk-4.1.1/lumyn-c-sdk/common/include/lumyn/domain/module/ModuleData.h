#pragma once

#include "ModuleDataType.h"
#include "lumyn/packed.h"

namespace lumyn::internal::ModuleData {
PACK(struct ModuleDataUnitHeader {
  uint16_t id;
  uint16_t len;
});
PACK(struct ModulePushData {
  uint16_t id;
  uint16_t len;
});
PACK(union ModuleDataUnion {
  ModuleDataUnitHeader dataUnit;
  ModulePushData pushData;
});

PACK(struct ModuleDataHeader {
  ModuleDataType type;
  ModuleDataUnion data;
});
}  // namespace lumyn::internal::ModuleData