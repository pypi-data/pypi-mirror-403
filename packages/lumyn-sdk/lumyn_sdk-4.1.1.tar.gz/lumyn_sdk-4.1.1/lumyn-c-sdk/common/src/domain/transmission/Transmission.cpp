#include "lumyn/domain/transmission/Transmission.h"

#include <cstring>

#include "lumyn/Constants.h"
#include "lumyn/util/logging/ConsoleLogger.h"
#include "lumyn/version.h"

namespace lumyn::internal::Transmission {

using Logger = ConsoleLogger;

// ------------------------------------------------------
// Constructor / Destructor
// ------------------------------------------------------
Transmission::Transmission(TransmissionSlot* slot) : _slot(slot) {
  // slot->refCount is already 1 from TransmissionPool::acquire
}

Transmission::~Transmission() {
  Logger::getInstance().logVerbose("Transmission",
      "Destructor called, releasing slot");
  if (_slot) {
    Logger::getInstance().logVerbose("Transmission",
        "Releasing slot back to pool");
    TransmissionPool::instance().release(_slot);
    _slot = nullptr;
  }
}

// ------------------------------------------------------
// build() from payload
// ------------------------------------------------------
Transmission* Transmission::build(TransmissionType type, const void* payload,
                                  size_t payloadSize, uint16_t packetCount) {
  size_t totalSize = sizeof(TransmissionHeader) + payloadSize;
  auto& pool = TransmissionPool::instance();
  TransmissionSlot* slot = pool.acquire(totalSize);
  if (!slot) {
    Logger::getInstance().logError("Transmission",
                                   "build: pool acquire failed for %u bytes",
                                   static_cast<unsigned>(totalSize));
    return nullptr;
  }

  auto* hdr = reinterpret_cast<TransmissionHeader*>(slot->buffer);
  hdr->type = type;
  hdr->dataLength = static_cast<uint32_t>(payloadSize);
  hdr->packetCount = packetCount;
  hdr->flags.reserved = 0;
  hdr->flags.compressed = 0;
  hdr->version = LUMYN_VERSION_MAJOR;

  if (payload && payloadSize > 0) {
    std::memcpy(slot->buffer + sizeof(TransmissionHeader), payload,
                payloadSize);
  }

  slot->length = totalSize;

  return new Transmission(slot);
}

// ------------------------------------------------------
// createFromBuffer()  [header + payload] -> pool
// ------------------------------------------------------
Transmission* Transmission::createFromBuffer(const uint8_t* data,
                                             size_t totalSize) {
  if (!data || totalSize < sizeof(TransmissionHeader)) {
    Logger::getInstance().logError("Transmission",
                                   "createFromBuffer: invalid input");
    return nullptr;
  }

  auto& pool = TransmissionPool::instance();
  TransmissionSlot* slot = pool.acquire(totalSize);
  if (!slot) {
    Logger::getInstance().logError(
        "Transmission", "createFromBuffer: pool acquire failed (%u bytes)",
        static_cast<unsigned>(totalSize));
    return nullptr;
  }

  std::memcpy(slot->buffer, data, totalSize);
  slot->length = totalSize;
  auto* hdr = reinterpret_cast<TransmissionHeader*>(slot->buffer);
  hdr->version = LUMYN_VERSION_MAJOR;
  
  return new Transmission(slot);
}

// ------------------------------------------------------
// create() overloads using std::vector as source only
// ------------------------------------------------------
Transmission* Transmission::create(const std::vector<uint8_t>& buffer) {
  if (buffer.empty()) return nullptr;
  return createFromBuffer(buffer.data(), buffer.size());
}

Transmission* Transmission::create(std::vector<uint8_t>&& buffer) {
  if (buffer.empty()) return nullptr;
  return createFromBuffer(buffer.data(), buffer.size());
}

// ------------------------------------------------------
// adoptSlot()  (RX path)
// ------------------------------------------------------
Transmission* Transmission::adoptSlot(TransmissionSlot* slot) {
  if (!slot) return nullptr;
  // slot->refCount is already 1 from acquire()
  return new Transmission(slot);
}

// ------------------------------------------------------
// appendPayload()
// ------------------------------------------------------
void Transmission::appendPayload(const uint8_t* data, size_t length) {
  if (!data || length == 0 || !_slot) return;

  auto* hdr = getHeaderMutable();
  if (!hdr) return;

  // We only allow append while staying within declared payload size.
  // If you want to stream-build without known final size, you'd need
  // a different API.
  size_t currentPayloadBytes =
      (_slot->length > sizeof(TransmissionHeader))
          ? (_slot->length - sizeof(TransmissionHeader))
          : 0;

  if (currentPayloadBytes + length > hdr->dataLength ||
      sizeof(TransmissionHeader) + currentPayloadBytes + length >
          _slot->capacity) {
    Logger::getInstance().logError(
        "Transmission", "appendPayload overflow (curr=%u, add=%u, decl=%u)",
        static_cast<unsigned>(currentPayloadBytes),
        static_cast<unsigned>(length), static_cast<unsigned>(hdr->dataLength));
    return;
  }

  uint8_t* dst =
      _slot->buffer + sizeof(TransmissionHeader) + currentPayloadBytes;
  std::memcpy(dst, data, length);

  _slot->length = sizeof(TransmissionHeader) + currentPayloadBytes + length;

  // hdr->dataLength stays as the final payload length, *not* bytes received
}

// ------------------------------------------------------
// Accessors
// ------------------------------------------------------
const TransmissionHeader* Transmission::getHeader() const {
  if (!_slot || _slot->length < sizeof(TransmissionHeader)) return nullptr;
  return reinterpret_cast<const TransmissionHeader*>(_slot->buffer);
}

TransmissionHeader* Transmission::getHeaderMutable() {
  if (!_slot || _slot->length < sizeof(TransmissionHeader)) return nullptr;
  return reinterpret_cast<TransmissionHeader*>(_slot->buffer);
}

const uint8_t* Transmission::getBuffer() const {
  return _slot ? _slot->buffer : nullptr;
}

uint8_t* Transmission::getBufferMutable() {
  return _slot ? _slot->buffer : nullptr;
}

uint32_t Transmission::getTotalSize() const {
  auto* h = getHeader();
  if (!h) return 0;
  return sizeof(TransmissionHeader) + h->dataLength;
}

const uint8_t* Transmission::getPayloadBytes() const {
  auto* h = getHeader();
  if (!h) return nullptr;
  return getBuffer() + sizeof(TransmissionHeader);
}

uint8_t* Transmission::getPayloadBytesMutable() {
  auto* h = getHeaderMutable();
  if (!h) return nullptr;
  return getBufferMutable() + sizeof(TransmissionHeader);
}

}  // namespace lumyn::internal::Transmission
