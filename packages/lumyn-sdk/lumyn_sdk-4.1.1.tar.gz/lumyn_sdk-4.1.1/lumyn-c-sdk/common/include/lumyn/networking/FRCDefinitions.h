#pragma once

#include <cstdint>

#include "lumyn/packed.h"

namespace lumyn::internal::frc {

// =============================================================================
// CAN Arbitration ID Bit Layout (29-bit Extended)
// =============================================================================
// [28:24] Device Type (5 bits)
// [23:16] Manufacturer (8 bits)
// [15:10] API Class (6 bits)
// [9:6]   API Index (4 bits)
// [5:0]   Device Number (6 bits)

struct CanIdLayout {
  static constexpr uint8_t DEVICE_TYPE_WIDTH = 5;
  static constexpr uint8_t MANUFACTURER_WIDTH = 8;
  static constexpr uint8_t API_CLASS_WIDTH = 6;
  static constexpr uint8_t API_INDEX_WIDTH = 4;
  static constexpr uint8_t DEVICE_NUMBER_WIDTH = 6;

  static constexpr uint32_t DEVICE_TYPE_SHIFT = 24;
  static constexpr uint32_t MANUFACTURER_SHIFT = 16;
  static constexpr uint32_t API_CLASS_SHIFT = 10;
  static constexpr uint32_t API_INDEX_SHIFT = 6;
  static constexpr uint32_t DEVICE_NUMBER_SHIFT = 0;

  static constexpr uint32_t DEVICE_TYPE_MASK = ((1u << DEVICE_TYPE_WIDTH) - 1)
                                               << DEVICE_TYPE_SHIFT;
  static constexpr uint32_t MANUFACTURER_MASK = ((1u << MANUFACTURER_WIDTH) - 1)
                                                << MANUFACTURER_SHIFT;
  static constexpr uint32_t API_CLASS_MASK = ((1u << API_CLASS_WIDTH) - 1)
                                             << API_CLASS_SHIFT;
  static constexpr uint32_t API_INDEX_MASK = ((1u << API_INDEX_WIDTH) - 1)
                                             << API_INDEX_SHIFT;
  static constexpr uint32_t DEVICE_NUMBER_MASK =
      ((1u << DEVICE_NUMBER_WIDTH) - 1) << DEVICE_NUMBER_SHIFT;

  // Combination masks for filtering
  static constexpr uint32_t DEVICE_TYPE_MANUFACTURER_MASK =
      DEVICE_TYPE_MASK | MANUFACTURER_MASK;
  static constexpr uint32_t API_MASK = API_CLASS_MASK | API_INDEX_MASK;
  static constexpr uint32_t FULL_API_MASK =
      DEVICE_TYPE_MASK | MANUFACTURER_MASK | API_MASK;

  // Special device numbers
  static constexpr uint8_t DEVICE_BROADCAST = 0x3F;
  static constexpr uint8_t DEVICE_DEFAULT = 0x00;
};

// =============================================================================
// Device Types (5-bit)
// =============================================================================
enum class DeviceType : uint8_t {
  BroadcastMessages = 0,
  RobotController = 1,
  MotorController = 2,
  RelayController = 3,
  GyroSensor = 4,
  Accelerometer = 5,
  DistanceSensor = 6,
  Encoder = 7,
  PowerDistributionModule = 8,
  PneumaticsController = 9,
  Miscellaneous = 10,
  IOBreakout = 11,
  ServoController = 12,
  ColorSensor = 13,
  Reserved14 = 14,
  Reserved15 = 15,
  // Reserved 16-30
  FirmwareUpdate = 31
};

// =============================================================================
// Manufacturers (8-bit)
// =============================================================================
enum class Manufacturer : uint8_t {
  Broadcast = 0,
  NI = 1,
  LuminaryMicro = 2,
  DEKA = 3,
  CTRElectronics = 4,
  REVRobotics = 5,
  Grapple = 6,
  MindSensors = 7,
  TeamUse = 8,
  KauaiLabs = 9,
  Copperforge = 10,
  PlayingWithFusion = 11,
  Studica = 12,
  TheThriftyBot = 13,
  ReduxRobotics = 14,
  AndyMark = 15,
  VividHosting = 16,
  VertosRobotics = 17,
  SWYFTRobotics = 18,
  LumynLabs = 19,
  BrushlandLabs = 20
  // Reserved 21-255
};

// =============================================================================
// Broadcast Messages (API Class = 0)
// =============================================================================
enum class BroadcastMessage : uint8_t {
  Disable = 0,
  SystemHalt = 1,
  SystemReset = 2,
  DeviceAssign = 3,
  DeviceQuery = 4,
  Heartbeat = 5,
  Sync = 6,
  Update = 7,
  FirmwareVersion = 8,
  Enumerate = 9,
  SystemResume = 10
};

// =============================================================================
// CAN ID Builder/Parser Class
// =============================================================================
class CanId {
 public:
  constexpr CanId() : _id(0) {}

  constexpr CanId(uint32_t rawId) : _id(rawId) {}

  constexpr CanId(DeviceType deviceType, Manufacturer manufacturer,
                  uint8_t apiClass, uint8_t apiIndex, uint8_t deviceNumber)
      : _id(build(deviceType, manufacturer, apiClass, apiIndex, deviceNumber)) {
  }

  // Getters
  constexpr uint32_t raw() const { return _id; }

  constexpr DeviceType deviceType() const {
    return static_cast<DeviceType>((_id & CanIdLayout::DEVICE_TYPE_MASK) >>
                                   CanIdLayout::DEVICE_TYPE_SHIFT);
  }

  constexpr Manufacturer manufacturer() const {
    return static_cast<Manufacturer>((_id & CanIdLayout::MANUFACTURER_MASK) >>
                                     CanIdLayout::MANUFACTURER_SHIFT);
  }

  constexpr uint8_t apiClass() const {
    return (_id & CanIdLayout::API_CLASS_MASK) >> CanIdLayout::API_CLASS_SHIFT;
  }

  constexpr uint8_t apiIndex() const {
    return (_id & CanIdLayout::API_INDEX_MASK) >> CanIdLayout::API_INDEX_SHIFT;
  }

  constexpr uint8_t deviceNumber() const {
    return (_id & CanIdLayout::DEVICE_NUMBER_MASK) >>
           CanIdLayout::DEVICE_NUMBER_SHIFT;
  }

  // Setters (returns new CanId for constexpr)
  constexpr CanId withDeviceType(DeviceType type) const {
    return CanId(
        (_id & ~CanIdLayout::DEVICE_TYPE_MASK) |
        (static_cast<uint32_t>(type) << CanIdLayout::DEVICE_TYPE_SHIFT));
  }

  constexpr CanId withManufacturer(Manufacturer mfr) const {
    return CanId(
        (_id & ~CanIdLayout::MANUFACTURER_MASK) |
        (static_cast<uint32_t>(mfr) << CanIdLayout::MANUFACTURER_SHIFT));
  }

  constexpr CanId withApiClass(uint8_t apiClass) const {
    return CanId((_id & ~CanIdLayout::API_CLASS_MASK) |
                 ((apiClass & 0x3F) << CanIdLayout::API_CLASS_SHIFT));
  }

  constexpr CanId withApiIndex(uint8_t apiIndex) const {
    return CanId((_id & ~CanIdLayout::API_INDEX_MASK) |
                 ((apiIndex & 0x0F) << CanIdLayout::API_INDEX_SHIFT));
  }

  constexpr CanId withDeviceNumber(uint8_t deviceNum) const {
    return CanId((_id & ~CanIdLayout::DEVICE_NUMBER_MASK) |
                 ((deviceNum & 0x3F) << CanIdLayout::DEVICE_NUMBER_SHIFT));
  }

  // Status checks
  constexpr bool isBroadcast() const {
    return deviceType() == DeviceType::BroadcastMessages &&
           manufacturer() == Manufacturer::Broadcast;
  }

  constexpr bool isDeviceBroadcast() const {
    return deviceNumber() == CanIdLayout::DEVICE_BROADCAST;
  }

  constexpr bool isHeartbeat() const {
    return isBroadcast() &&
           apiClass() == static_cast<uint8_t>(BroadcastMessage::Heartbeat);
  }

  constexpr bool isConnectorX() const {
    return deviceType() == DeviceType::Miscellaneous &&
           manufacturer() == Manufacturer::LumynLabs;
  }

  // Operators
  constexpr bool operator==(const CanId& other) const {
    return _id == other._id;
  }
  constexpr bool operator!=(const CanId& other) const {
    return _id != other._id;
  }
  constexpr bool operator==(uint32_t rawId) const { return _id == rawId; }
  constexpr bool operator!=(uint32_t rawId) const { return _id != rawId; }

  // Static factory methods
  static constexpr CanId broadcast(BroadcastMessage message) {
    return CanId(DeviceType::BroadcastMessages, Manufacturer::Broadcast, 0,
                 static_cast<uint8_t>(message), 0);
  }

  static constexpr CanId heartbeat() { return CanId(0x01011840); }

 private:
  static constexpr uint32_t build(DeviceType deviceType,
                                  Manufacturer manufacturer, uint8_t apiClass,
                                  uint8_t apiIndex, uint8_t deviceNumber) {
    return (static_cast<uint32_t>(deviceType)
            << CanIdLayout::DEVICE_TYPE_SHIFT) |
           (static_cast<uint32_t>(manufacturer)
            << CanIdLayout::MANUFACTURER_SHIFT) |
           ((apiClass & 0x3F) << CanIdLayout::API_CLASS_SHIFT) |
           ((apiIndex & 0x0F) << CanIdLayout::API_INDEX_SHIFT) |
           ((deviceNumber & 0x3F) << CanIdLayout::DEVICE_NUMBER_SHIFT);
  }

  uint32_t _id;
};

// =============================================================================
// CAN Filter/Mask Helper
// =============================================================================
class CanFilter {
 public:
  constexpr CanFilter(uint32_t id, uint32_t mask) : _id(id), _mask(mask) {}

  constexpr uint32_t id() const { return _id; }
  constexpr uint32_t mask() const { return _mask; }

  constexpr bool matches(uint32_t testId) const {
    return (_id & _mask) == (testId & _mask);
  }

  constexpr bool matches(const CanId& testId) const {
    return matches(testId.raw());
  }

  // Factory methods for common filters
  static constexpr CanFilter acceptAll() {
    return CanFilter(0x00000000, 0x00000000);
  }

  static constexpr CanFilter deviceType(DeviceType type) {
    return CanFilter(static_cast<uint32_t>(type)
                         << CanIdLayout::DEVICE_TYPE_SHIFT,
                     CanIdLayout::DEVICE_TYPE_MASK);
  }

  static constexpr CanFilter manufacturer(Manufacturer mfr) {
    return CanFilter(static_cast<uint32_t>(mfr)
                         << CanIdLayout::MANUFACTURER_SHIFT,
                     CanIdLayout::MANUFACTURER_MASK);
  }

  static constexpr CanFilter deviceTypeAndManufacturer(DeviceType type,
                                                       Manufacturer mfr) {
    return CanFilter(
        (static_cast<uint32_t>(type) << CanIdLayout::DEVICE_TYPE_SHIFT) |
            (static_cast<uint32_t>(mfr) << CanIdLayout::MANUFACTURER_SHIFT),
        CanIdLayout::DEVICE_TYPE_MANUFACTURER_MASK);
  }

  static constexpr CanFilter api(DeviceType type, Manufacturer mfr,
                                 uint8_t apiClass, uint8_t apiIndex) {
    return CanFilter(CanId(type, mfr, apiClass, apiIndex, 0).raw(),
                     CanIdLayout::FULL_API_MASK);
  }

  static constexpr CanFilter exactMatch(const CanId& id) {
    return CanFilter(id.raw(), 0x1FFFFFFF);  // All 29 bits
  }

  static constexpr CanFilter broadcastOnly() {
    return deviceTypeAndManufacturer(DeviceType::BroadcastMessages,
                                     Manufacturer::Broadcast);
  }

 private:
  uint32_t _id;
  uint32_t _mask;
};

// =============================================================================
// Universal Heartbeat (roboRIO)
// =============================================================================
constexpr uint32_t HEARTBEAT_INTERVAL_MS = 20;
constexpr uint32_t HEARTBEAT_TIMEOUT_MS = 100;

PACK(struct RobotState {
  uint64_t matchTimeSeconds : 8;  // Match time in seconds
  uint64_t matchNumber : 10;      // Match number
  uint64_t replayNumber : 6;      // Replay number
  uint64_t redAlliance : 1;       // 1 = red, 0 = blue
  uint64_t enabled : 1;           // Robot enabled
  uint64_t autonomous : 1;        // Autonomous mode
  uint64_t testMode : 1;          // Test mode
  uint64_t systemWatchdog : 1;    // Watchdog active (motors enabled)
  uint64_t tournamentType : 3;    // Tournament type
  uint64_t timeOfDay_yr : 6;      // Year (offset from 2000)
  uint64_t timeOfDay_month : 4;   // Month (1-12)
  uint64_t timeOfDay_day : 5;     // Day (1-31)
  uint64_t timeOfDay_sec : 6;     // Seconds (0-59)
  uint64_t timeOfDay_min : 6;     // Minutes (0-59)
  uint64_t timeOfDay_hr : 5;      // Hours (0-23)

  bool isEnabled() const { return enabled && systemWatchdog; }
  bool isDisabled() const { return !enabled || !systemWatchdog; }
  bool isAutonomous() const { return enabled && autonomous && !testMode; }
  bool isTeleop() const { return enabled && !autonomous && !testMode; }
  bool isTest() const { return enabled && testMode; }
});

static_assert(sizeof(RobotState) == 8, "RobotState must be 8 bytes");

// =============================================================================
// Common CAN IDs
// =============================================================================
namespace CommonIds {
constexpr CanId DISABLE = CanId::broadcast(BroadcastMessage::Disable);
constexpr CanId SYSTEM_HALT = CanId::broadcast(BroadcastMessage::SystemHalt);
constexpr CanId SYSTEM_RESET = CanId::broadcast(BroadcastMessage::SystemReset);
constexpr CanId HEARTBEAT = CanId::heartbeat();
}  // namespace CommonIds

// =============================================================================
// Common Filters
// =============================================================================
namespace CommonFilters {
constexpr CanFilter ACCEPT_ALL = CanFilter::acceptAll();
constexpr CanFilter BROADCAST_ONLY = CanFilter::broadcastOnly();
constexpr CanFilter HEARTBEAT_ONLY =
    CanFilter::exactMatch(CommonIds::HEARTBEAT);
constexpr CanFilter LUMYN_DEVICES =
    CanFilter::deviceTypeAndManufacturer(DeviceType::Miscellaneous, Manufacturer::LumynLabs);
}  // namespace CommonFilters

}  // namespace lumyn::internal::frc