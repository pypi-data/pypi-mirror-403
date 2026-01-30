#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>

// Add includes for utility classes
#include <lumyn/util/serial/ISerialIO.h>
#include <lumyn/util/serial/IEncoder.h>
#include <lumyn/util/serial/PacketSerial.h>
#include <lumyn/util/serial/COBSEncoder.h>
#include <lumyn/util/serial/LumynTP.h>
#include <lumyn/util/serial/RLECompressor.h>
#include <lumyn/util/serial/DeltaCompressor.h>
#include <lumyn/version.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_serial_bindings(py::module &m)
  {
    // Serial namespace and types
    auto serial_m = m.def_submodule("serial", "Serial communication related types");

    // IEncoder interface (abstract base class) - note it's in global namespace
    py::class_<IEncoder>(serial_m, "IEncoder")
        .def("encode", [](IEncoder &self, py::bytes data) -> py::bytes
             {
                std::string str_data = data;
                uint8_t input_buffer[256];
                uint8_t encoded[256];
                
                // Copy input data to mutable buffer
                size_t input_size = std::min(str_data.size(), sizeof(input_buffer));
                std::memcpy(input_buffer, str_data.c_str(), input_size);
                
                size_t encoded_size = self.encode(input_buffer, input_size, encoded);
                return py::bytes(reinterpret_cast<const char*>(encoded), encoded_size); })
        .def("decode", [](IEncoder &self, py::bytes data) -> py::bytes
             {
                std::string str_data = data;
                uint8_t input_buffer[256];
                uint8_t decoded[256];
                
                // Copy input data to mutable buffer
                size_t input_size = std::min(str_data.size(), sizeof(input_buffer));
                std::memcpy(input_buffer, str_data.c_str(), input_size);
                
                size_t decoded_size = self.decode(input_buffer, input_size, decoded);
                return py::bytes(reinterpret_cast<const char*>(decoded), decoded_size); })
        .def("getEncodedBufferSize", &IEncoder::getEncodedBufferSize);

    // Add this trampoline class
    class PySerialIO : public lumyn::internal::ISerialIO
    {
    public:
      using lumyn::internal::ISerialIO::ISerialIO;

      void writeBytes(const uint8_t *data, size_t length) override
      {
        PYBIND11_OVERRIDE_PURE(
            void,
            lumyn::internal::ISerialIO,
            writeBytes,
            data, length);
      }

      void setReadCallback(std::function<void(const uint8_t *, size_t)> callback) override
      {
        PYBIND11_OVERRIDE_PURE(
            void,
            lumyn::internal::ISerialIO,
            setReadCallback,
            callback);
      }
    };

    // ISerialIO interface
    py::class_<lumyn::internal::ISerialIO, PySerialIO>(serial_m, "ISerialIO")
        .def(py::init<>())
        .def("writeBytes", [](lumyn::internal::ISerialIO &self, py::bytes data)
             {
                std::string str_data = data;
                self.writeBytes(reinterpret_cast<const uint8_t*>(str_data.c_str()), str_data.size()); })
        .def("setReadCallback", [](lumyn::internal::ISerialIO &self, py::function callback)
             { self.setReadCallback([callback](const uint8_t *data, size_t length)
                                    {
                    py::gil_scoped_acquire acquire;
                    py::bytes data_bytes(reinterpret_cast<const char*>(data), length);
                    callback(data_bytes); }); });

    // COBSEncoder
    py::class_<lumyn::internal::COBSEncoder, IEncoder>(serial_m, "COBSEncoder")
        .def(py::init<>());

    // StandardPacketSerial (template instantiation for standard serial protocol)
    py::class_<lumyn::internal::StandardPacketSerial>(serial_m, "PacketSerial")
        .def(py::init<IEncoder *, size_t>(), py::arg("encoder"), py::arg("maxPacketSize") = lumyn::internal::Packet::maxPacketSize())
        .def("startReading", &lumyn::internal::StandardPacketSerial::startReading)
        .def("stopReading", &lumyn::internal::StandardPacketSerial::stopReading)
        .def("send", &lumyn::internal::StandardPacketSerial::send)
        .def("maxPacketBodySize", &lumyn::internal::StandardPacketSerial::maxPacketBodySize)
        .def("processReadData", [](lumyn::internal::StandardPacketSerial &self, py::bytes data)
             {
                std::string str_data = data;
                self.processReadData(reinterpret_cast<const uint8_t*>(str_data.c_str()), str_data.size()); })
        .def("setOnNewPacket", [](lumyn::internal::StandardPacketSerial &self, py::function callback)
             { self.setOnNewPacket([callback](lumyn::internal::Packet &packet)
                                   {
                    py::gil_scoped_acquire acquire;
                    callback(packet); }); })
        .def("setOnOverflow", [](lumyn::internal::StandardPacketSerial &self, py::function callback)
             { self.setOnOverflow([callback]()
                                  {
                    py::gil_scoped_acquire acquire;
                    callback(); }); })
        .def("setOnPacketOverflow", [](lumyn::internal::StandardPacketSerial &self, py::function callback)
             { self.setOnPacketOverflow([callback]()
                                        {
                    py::gil_scoped_acquire acquire;
                    callback(); }); })
        .def("setWriteCallback", [](lumyn::internal::StandardPacketSerial &self, py::function callback)
             { self.setWriteCallback([callback](const uint8_t *data, size_t length)
                                     {
                    py::gil_scoped_acquire acquire;
                    py::bytes data_bytes(reinterpret_cast<const char*>(data), length);
                    callback(data_bytes); }); });

    // StandardLumynTP (template instantiation for standard serial protocol)
    py::class_<lumyn::internal::StandardLumynTP>(serial_m, "LumynTP")
        .def(py::init<lumyn::internal::StandardPacketSerial &>())
        .def("start", &lumyn::internal::StandardLumynTP::start)
        .def("sendTransmission", [](lumyn::internal::StandardLumynTP &self, py::bytes data, lumyn::internal::Transmission::TransmissionType type)
             {
                std::string str_data = data;
                self.sendTransmission(reinterpret_cast<const uint8_t*>(str_data.c_str()), str_data.size(), type); })
        .def("setOnNewTransmission", [](lumyn::internal::StandardLumynTP &self, py::function callback)
             { self.setOnNewTransmission([callback](lumyn::internal::Transmission::Transmission *transmission)
                                         {
                    py::gil_scoped_acquire acquire;
                    callback(transmission); }); });

    // RLECompressor - static methods for compression
    py::class_<lumyn::internal::RLECompressor>(serial_m, "RLECompressor")
        .def_static("compress", [](lumyn::internal::Transmission::Transmission *tx) -> lumyn::internal::Transmission::Transmission *
                    { return lumyn::internal::RLECompressor::compress(tx); }, py::return_value_policy::reference)
        .def_static("decompress", [](lumyn::internal::Transmission::Transmission *tx) -> lumyn::internal::Transmission::Transmission *
                    { return lumyn::internal::RLECompressor::decompress(tx); }, py::return_value_policy::reference);

    // DeltaCompressor - XOR-based delta encoding for efficient buffer updates
    py::class_<lumyn::internal::DeltaCompressor>(serial_m, "DeltaCompressor")
        .def_static("encode", [](py::bytes current, py::bytes previous, size_t size) -> py::bytes
                    {
                std::string current_str = current;
                std::string previous_str = previous;
                std::vector<uint8_t> delta;
                lumyn::internal::DeltaCompressor::encode(
                    reinterpret_cast<const uint8_t*>(current_str.c_str()),
                    reinterpret_cast<const uint8_t*>(previous_str.c_str()),
                    size,
                    delta);
                return py::bytes(reinterpret_cast<const char*>(delta.data()), delta.size()); })
        .def_static("decode", [](py::bytes delta, py::bytes previous, size_t size) -> py::bytes
                    {
                std::string delta_str = delta;
                std::string previous_str = previous;
                std::vector<uint8_t> current;
                lumyn::internal::DeltaCompressor::decode(
                    reinterpret_cast<const uint8_t*>(delta_str.c_str()),
                    reinterpret_cast<const uint8_t*>(previous_str.c_str()),
                    size,
                    current);
                return py::bytes(reinterpret_cast<const char*>(current.data()), current.size()); });

    // Version information
    serial_m.attr("DRIVER_VERSION_MAJOR") = DRIVER_VERSION_MAJOR;
    serial_m.attr("DRIVER_VERSION_MINOR") = DRIVER_VERSION_MINOR;
    serial_m.attr("DRIVER_VERSION_PATCH") = DRIVER_VERSION_PATCH;
  }
}
