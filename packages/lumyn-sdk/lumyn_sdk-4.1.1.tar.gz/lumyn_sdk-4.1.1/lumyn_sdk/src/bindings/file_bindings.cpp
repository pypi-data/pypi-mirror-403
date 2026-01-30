#include "bindings.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstring>

#include <lumyn/domain/file/Files.h>
#include <lumyn/domain/file/FileType.h>

namespace py = pybind11;

namespace lumyn_bindings
{
  void register_file_bindings(py::module &m)
  {
    // File namespace and types
    auto file_m = m.def_submodule("file", "File related types");

    py::enum_<lumyn::internal::Files::FileType>(file_m, "FileType")
        .value("Transfer", lumyn::internal::Files::FileType::Transfer)
        .value("SendConfig", lumyn::internal::Files::FileType::SendConfig)
        .value("SetPixelBuffer", lumyn::internal::Files::FileType::SetPixelBuffer)
        .export_values();

    // File structures
    py::class_<lumyn::internal::Files::FileTransferInfoHeader>(file_m, "FileTransferInfoHeader")
        .def(py::init<>())
        .def_property("path", [](const lumyn::internal::Files::FileTransferInfoHeader &header)
                      { return std::string(header.path, strnlen(header.path, 32)); }, [](lumyn::internal::Files::FileTransferInfoHeader &header, const std::string &path)
                      {
                    size_t len = std::min(path.size(), size_t(31));
                    std::strncpy(header.path, path.c_str(), len);
                    header.path[len] = '\0'; });

    py::class_<lumyn::internal::Files::SendConfigInfoHeader>(file_m, "SendConfigInfoHeader")
        .def(py::init<>());

    py::class_<lumyn::internal::Files::SetZonePixelBuffer>(file_m, "SetZonePixelBuffer")
        .def(py::init<>())
        .def_readwrite("zoneId", &lumyn::internal::Files::SetZonePixelBuffer::zoneId)
        .def_readwrite("zoneLength", &lumyn::internal::Files::SetZonePixelBuffer::zoneLength);

    // FilesInfo union
    py::class_<lumyn::internal::Files::FilesInfo>(file_m, "FilesInfo")
        .def(py::init<>())
        .def_property("fileTransfer", [](const lumyn::internal::Files::FilesInfo &info)
                      { return info.fileTransfer; }, [](lumyn::internal::Files::FilesInfo &info, const lumyn::internal::Files::FileTransferInfoHeader &v)
                      { info.fileTransfer = v; })
        .def_property("sendConfig", [](const lumyn::internal::Files::FilesInfo &info)
                      { return info.sendConfig; }, [](lumyn::internal::Files::FilesInfo &info, const lumyn::internal::Files::SendConfigInfoHeader &v)
                      { info.sendConfig = v; })
        .def_property("setZonePixels", [](const lumyn::internal::Files::FilesInfo &info)
                      { return info.setZonePixels; }, [](lumyn::internal::Files::FilesInfo &info, const lumyn::internal::Files::SetZonePixelBuffer &v)
                      { info.setZonePixels = v; });

    py::class_<lumyn::internal::Files::FilesHeader>(file_m, "FilesHeader")
        .def(py::init<>())
        .def_readwrite("type", &lumyn::internal::Files::FilesHeader::type)
        .def_readwrite("fileSize", &lumyn::internal::Files::FilesHeader::fileSize)
        .def_readwrite("info", &lumyn::internal::Files::FilesHeader::info);

    // Main Files structure
    py::class_<lumyn::internal::Files::Files>(file_m, "Files")
        .def(py::init<>())
        .def_readwrite("header", &lumyn::internal::Files::Files::header);
    // Note: bytes field is a pointer, handling would require custom logic
  }
}