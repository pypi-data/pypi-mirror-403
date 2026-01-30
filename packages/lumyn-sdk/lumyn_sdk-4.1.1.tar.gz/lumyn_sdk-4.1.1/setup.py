import os
import sys
import subprocess
import glob
import shutil
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        super().__init__(name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        # Get pybind11 cmake directory
        try:
            import pybind11
            pybind11_cmake_dir = pybind11.get_cmake_dir()
        except ImportError:
            pybind11_cmake_dir = None

        cmake_args = [
            f"-DPython_EXECUTABLE={sys.executable}",
        ]

        if pybind11_cmake_dir:
            cmake_args.append(f"-Dpybind11_DIR={pybind11_cmake_dir}")

        build_args = ["--config", "Release"]
        env = os.environ.copy()

        # On macOS, respect ARCHFLAGS for cross-compilation
        # cibuildwheel sets this to target x86_64 or arm64
        archflags = env.get("ARCHFLAGS", "")
        if sys.platform == "darwin" and archflags:
            # ARCHFLAGS looks like "-arch x86_64" or "-arch arm64"
            if "x86_64" in archflags:
                cmake_args.append("-DCMAKE_OSX_ARCHITECTURES=x86_64")
            elif "arm64" in archflags:
                cmake_args.append("-DCMAKE_OSX_ARCHITECTURES=arm64")

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(["cmake", ext.sourcedir] +
                              cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(["cmake", "--build", "."] +
                              build_args, cwd=self.build_temp)

        # Copy the built extension to the location setuptools expects
        # CMake outputs to lumyn_sdk/, but setuptools expects it in build/lib.*/lumyn_sdk/
        ext_fullpath = self.get_ext_fullpath(ext.name)
        ext_dir = os.path.dirname(ext_fullpath)
        os.makedirs(ext_dir, exist_ok=True)

        # Find the built extension in the source directory
        # CMakeLists.txt outputs to CMAKE_SOURCE_DIR which is lumyn_sdk/
        ext_suffix = self.get_ext_filename(ext.name).replace(
            ext.name.replace('.', os.sep), '')
        built_ext_patterns = [
            os.path.join(ext.sourcedir, f"_bindings_ext{ext_suffix}"),
            os.path.join(ext.sourcedir, f"_bindings_ext*.so"),
            os.path.join(ext.sourcedir, f"_bindings_ext*.pyd"),
        ]

        built_ext = None
        for pattern in built_ext_patterns:
            matches = glob.glob(pattern)
            if matches:
                built_ext = matches[0]
                break

        if built_ext and os.path.exists(built_ext):
            # Only copy if source and dest are different (avoid error in editable installs)
            if os.path.abspath(built_ext) != os.path.abspath(ext_fullpath):
                shutil.copy(built_ext, ext_fullpath)
                print(f"Copied {built_ext} -> {ext_fullpath}")
            else:
                print(f"Extension already at {ext_fullpath}")
        else:
            raise RuntimeError(
                f"Could not find built extension. Looked for: {built_ext_patterns}")

        # Also copy shared libraries (lumyn_sdk_cpp.so/dll/dylib) to the package
        # Only copy libraries that actually exist and are relevant for the current platform
        # Check multiple locations because multi-config generators (Visual Studio) may output to subdirs
        lib_patterns = [
            # Primary location (where CMAKE_SOURCE_DIR points)
            os.path.join(ext.sourcedir, "*.so"),
            os.path.join(ext.sourcedir, "*.so.*"),
            os.path.join(ext.sourcedir, "*.dll"),
            os.path.join(ext.sourcedir, "*.dylib"),
            # Fallback: build directory (for multi-config generators like Visual Studio)
            os.path.join(self.build_temp, "Release", "*.dll"),
            os.path.join(self.build_temp, "Debug", "*.dll"),
            os.path.join(self.build_temp, "*.dll"),
            # Fallback: lumyn-c-sdk build output
            os.path.join(self.build_temp, "lumyn-c-sdk", "Release", "*.dll"),
            os.path.join(self.build_temp, "lumyn-c-sdk", "*.dll"),
        ]

        # Debug: print what files exist in various directories
        print(f"Looking for shared libraries...")
        print(
            f"  Source dir ({ext.sourcedir}): {[f for f in os.listdir(ext.sourcedir) if f.endswith(('.dll', '.so', '.dylib'))]}")
        if os.path.exists(self.build_temp):
            print(
                f"  Build temp ({self.build_temp}): {os.listdir(self.build_temp)}")
            release_dir = os.path.join(self.build_temp, "Release")
            if os.path.exists(release_dir):
                print(
                    f"  Build Release ({release_dir}): {os.listdir(release_dir)}")
            csdk_dir = os.path.join(self.build_temp, "lumyn-c-sdk")
            if os.path.exists(csdk_dir):
                print(f"  lumyn-c-sdk build: {os.listdir(csdk_dir)}")
                csdk_release = os.path.join(csdk_dir, "Release")
                if os.path.exists(csdk_release):
                    print(f"  lumyn-c-sdk/Release: {os.listdir(csdk_release)}")

        libs_found = False
        for pattern in lib_patterns:
            for lib in glob.glob(pattern):
                # Don't copy the extension module itself again
                if "_bindings_ext" not in os.path.basename(lib):
                    libs_found = True
                    dest = os.path.join(ext_dir, os.path.basename(lib))
                    # Only copy if source and dest are different and source exists
                    if os.path.exists(lib) and os.path.abspath(lib) != os.path.abspath(dest):
                        if not os.path.exists(dest):
                            shutil.copy(lib, dest)
                            print(f"Copied shared library {lib} -> {dest}")

        if not libs_found:
            print(
                f"WARNING: No shared libraries found! The wheel may not work correctly.")
            print(f"  Searched patterns: {lib_patterns}")


setup(
    name="lumyn_sdk",
    version="4.1.1",  # x-release-please-version
    author="Lumyn Labs",
    author_email="info@lumynlabs.com",
    description="Lumyn Labs SDK",
    # Let pyproject.toml handle packages
    ext_modules=[
        # Extension name matches CMakeLists.txt pybind11_add_module(_bindings_ext, ...)
        # Named _bindings_ext to avoid conflict with _bindings/ package directory
        CMakeExtension("lumyn_sdk._bindings_ext", sourcedir="lumyn_sdk")
    ],
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.8",
    zip_safe=False,
)
