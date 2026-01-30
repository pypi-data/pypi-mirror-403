"""Setup script for jzip-zig Python bindings using Zig."""

import shutil
import subprocess
import sys
import sysconfig
import platform
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class ZigBuildExt(build_ext):
    """Custom build_ext that uses Zig to build native Python bindings."""

    def build_extension(self, ext):
        python_include = sysconfig.get_path("include")

        ext_fullpath = Path(self.get_ext_fullpath(ext.name))
        ext_dir = ext_fullpath.parent
        ext_dir.mkdir(parents=True, exist_ok=True)

        project_root = Path(__file__).parent

        cmd = [
            "zig",
            "build",
            "python-bindings",
            f"-Dpython-include={python_include}",
            "-Doptimize=ReleaseFast",
        ]

        # On macOS, build with a conservative deployment target for wheel tags.
        if sys.platform == "darwin":
            arch = platform.machine()
            if arch == "arm64":
                cmd.append("-Dtarget=aarch64-macos.11.0")
            elif arch == "x86_64":
                cmd.append("-Dtarget=x86_64-macos.11.0")

        # Extension modules should not link against libpython.

        print(f"Building with: {' '.join(cmd)}")
        subprocess.check_call(cmd, cwd=project_root)

        built_dir = project_root / "zig-out" / "bindings" / "python" / "jzip"
        built_lib = None
        for name in [
            "lib_jzip.so",
            "lib_jzip.dylib",
            "_jzip.so",
            "_jzip.dylib",
            "lib__jzip.so",
            "lib__jzip.dylib",
        ]:
            cand = built_dir / name
            if cand.exists():
                built_lib = cand
                break

        if built_lib is None:
            lib_dir = project_root / "zig-out" / "lib"
            for name in [
                "lib_jzip.so",
                "lib_jzip.dylib",
                "_jzip.so",
                "_jzip.dylib",
                "lib__jzip.so",
                "lib__jzip.dylib",
            ]:
                cand = lib_dir / name
                if cand.exists():
                    built_lib = cand
                    break

        if built_lib is None:
            raise RuntimeError(
                "Built library not found. Looked in:\n"
                f"  {built_dir}\n"
                f"  {project_root / 'zig-out' / 'lib'}"
            )

        target = ext_dir / f"_jzip{sysconfig.get_config_var('EXT_SUFFIX')}"
        print(f"Copying {built_lib} -> {target}")
        shutil.copy2(built_lib, target)


ext_modules = [
    Extension(
        "jzip._jzip",
        sources=[],
    )
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": ZigBuildExt},
)
