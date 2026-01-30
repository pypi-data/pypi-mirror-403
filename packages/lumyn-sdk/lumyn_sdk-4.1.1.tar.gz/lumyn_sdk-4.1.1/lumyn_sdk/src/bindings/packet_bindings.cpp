#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <lumyn/domain/transmission/Packet.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_packet_bindings(py::module &m)
  {
    // Packet types
    auto packet_m = m.def_submodule("packet", "Packet related types");

    // PacketHeader struct
    py::class_<lumyn::internal::PacketHeader>(packet_m, "PacketHeader")
        .def(py::init<>())
        .def_readwrite("packetId", &lumyn::internal::PacketHeader::packetId)
        .def_readwrite("length", &lumyn::internal::PacketHeader::length)
        .def_readwrite("crc", &lumyn::internal::PacketHeader::crc)
        .def_static("baseSize", &lumyn::internal::PacketHeader::baseSize);

    // PacketCANHeader struct
    py::class_<lumyn::internal::PacketCANHeader>(packet_m, "PacketCANHeader")
        .def(py::init<>())
        .def_readwrite("packetId", &lumyn::internal::PacketCANHeader::packetId)
        .def_readwrite("length", &lumyn::internal::PacketCANHeader::length)
        .def_static("baseSize", &lumyn::internal::PacketCANHeader::baseSize);

    // Packet (standard serial packet)
    py::class_<lumyn::internal::Packet>(packet_m, "Packet")
        .def(py::init<>())
        .def_readwrite("header", &lumyn::internal::Packet::header)
        .def_property("buf", [](const lumyn::internal::Packet &p)
                      { return py::bytes(reinterpret_cast<const char *>(p.buf), p.header.length); }, [](lumyn::internal::Packet &p, const py::bytes &bytes)
                      {
                    std::string str = bytes;
                    constexpr size_t maxBodySize = lumyn::internal::PacketTraits<lumyn::internal::PacketHeader>::MAX_PACKET_BODY_SIZE;
                    if (str.size() > maxBodySize) {
                        throw std::runtime_error("Data exceeds maximum packet body size");
                    }
                    std::memcpy(p.buf, str.data(), str.size());
                    p.header.length = static_cast<uint8_t>(str.size()); })
        .def_static("fromBuffer", &lumyn::internal::Packet::fromBuffer)
        .def_static("maxPacketSize", &lumyn::internal::Packet::maxPacketSize)
        .def_static("maxBodySize", &lumyn::internal::Packet::maxBodySize);

    // CANPacket
    py::class_<lumyn::internal::CANPacket>(packet_m, "CANPacket")
        .def(py::init<>())
        .def_readwrite("header", &lumyn::internal::CANPacket::header)
        .def_property("buf", [](const lumyn::internal::CANPacket &p)
                      { return py::bytes(reinterpret_cast<const char *>(p.buf), p.header.length); }, [](lumyn::internal::CANPacket &p, const py::bytes &bytes)
                      {
                    std::string str = bytes;
                    constexpr size_t maxBodySize = lumyn::internal::PacketTraits<lumyn::internal::PacketCANHeader>::MAX_PACKET_BODY_SIZE;
                    if (str.size() > maxBodySize) {
                        throw std::runtime_error("Data exceeds maximum CAN packet body size");
                    }
                    std::memcpy(p.buf, str.data(), str.size());
                    p.header.length = static_cast<uint8_t>(str.size()); })
        .def_static("fromBuffer", &lumyn::internal::CANPacket::fromBuffer)
        .def_static("maxPacketSize", &lumyn::internal::CANPacket::maxPacketSize)
        .def_static("maxBodySize", &lumyn::internal::CANPacket::maxBodySize);

    // Constants
    packet_m.attr("PACKET_MARKER") = lumyn::internal::PACKET_MARKER;
    packet_m.attr("COBS_OVERHEAD") = lumyn::internal::COBS_OVERHEAD;
  }
}
