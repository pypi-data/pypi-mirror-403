#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>  // only for argument types, not internal storage

#include "lumyn/domain/transmission/TransmissionType.h"
#include "lumyn/packed.h"
#include "lumyn/util/IntrusiveSharedPtr.h"
#include "lumyn/util/RefCounted.h"
#include "lumyn/util/serial/TransmissionPool.h"

namespace lumyn::internal::Transmission {

// === Header layout (unchanged) ===
PACK(struct TransmissionHeaderFlags {
  uint8_t reserved : 7;
  uint8_t compressed : 1;
});

PACK(struct TransmissionHeader {
  TransmissionType type;
  uint32_t dataLength;   // payload length (bytes)
  uint16_t packetCount;  // number of packets used to transport
  TransmissionHeaderFlags flags;
  uint8_t version;
  uint8_t reserved[3];
});

// Forward declaration
struct TransmissionSlot;

// ======================================================
//              Pool-backed Transmission
// ======================================================
class Transmission : public RefCounted {
 public:
  // Build from a payload buffer (header + payload go into pool)
  static Transmission* build(TransmissionType type, const void* payload,
                             size_t payloadSize, uint16_t packetCount = 1);

  // Create from a contiguous buffer that already contains:
  // [TransmissionHeader][payload bytes...]
  static Transmission* createFromBuffer(const uint8_t* data, size_t totalSize);

  // Legacy helpers: still allowed as *call sites*, but use pool inside
  static Transmission* create(const std::vector<uint8_t>& buffer);
  static Transmission* create(std::vector<uint8_t>&& buffer);

  // Adopt an already-acquired slot (for RX assembly)
  static Transmission* adoptSlot(TransmissionSlot* slot);

  // Append payload bytes after the header. This does NOT change dataLength;
  // it is caller’s responsibility to make sure header->dataLength is the
  // final payload size. This is mainly useful for TX-side manual building.
  void appendPayload(const uint8_t* data, size_t length);

  // Accessors
  const TransmissionHeader* getHeader() const;
  TransmissionHeader* getHeaderMutable();

  // Raw buffer (includes header at front)
  const uint8_t* getBuffer() const;
  uint8_t* getBufferMutable();

  // Size of header + payload, according to header->dataLength.
  uint32_t getTotalSize() const;

  // Pointer to payload start (after header)
  const uint8_t* getPayloadBytes() const;
  uint8_t* getPayloadBytesMutable();

  template <typename T>
  const T* getPayload() const {
    auto* h = getHeader();
    if (!h || sizeof(T) > h->dataLength) return nullptr;
    return reinterpret_cast<const T*>(getPayloadBytes());
  }

  template <typename T>
  const uint8_t* getVariableData() const {
    auto* h = getHeader();
    if (!h || h->dataLength <= sizeof(T)) return nullptr;
    return getPayloadBytes() + sizeof(T);
  }

  template <typename T>
  size_t getVariableDataSize() const {
    auto* h = getHeader();
    if (!h || h->dataLength <= sizeof(T)) return 0;
    return h->dataLength - sizeof(T);
  }

  void setPacketCount(uint16_t count) {
    auto* h = getHeaderMutable();
    if (h) h->packetCount = count;
  }

 private:
  explicit Transmission(TransmissionSlot* slot);
  virtual ~Transmission() override;

 private:
  TransmissionSlot* _slot = nullptr;
};

// ======================================================
// Packet types (unchanged public shape)
// ======================================================

struct PacketHeader {
  uint16_t packetId;
  uint8_t length;
  uint8_t crc;
};

constexpr uint16_t kMaxPacketSize = 256;
constexpr uint16_t kMaxPacketBodySize = kMaxPacketSize - sizeof(PacketHeader);

struct Packet {
  using HeaderType = PacketHeader;

  PacketHeader header;
  uint8_t buf[kMaxPacketBodySize];

  static constexpr size_t maxPacketSize() { return kMaxPacketSize; }
  static constexpr size_t headerSize() { return sizeof(PacketHeader); }

  // These should already exist in your code base; signatures shown for clarity:
  // static void   toBuffer(const Packet& p, uint8_t* out, size_t& outLen);
  // static Packet fromBuffer(const uint8_t* in, size_t len);

  struct Traits {
    static constexpr size_t kMaxSize = kMaxPacketSize;
    static constexpr size_t kHeaderSize = sizeof(PacketHeader);
  };
};

// Alias used elsewhere
using TransmissionPtr = lumyn::internal::IntrusiveSharedPtr<Transmission>;

}  // namespace lumyn::internal::Transmission
