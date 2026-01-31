from __future__ import annotations

import os
import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.dist import Distribution
from setuptools.command.build_py import build_py
from wheel.bdist_wheel import bdist_wheel

ROOT = Path(__file__).resolve().parent


class BuildPy(build_py):
    def run(self) -> None:
        # Ensure the shared library is built before packaging.
        if os.environ.get("PYGOREADABILITY_SKIP_BUILD") != "1":
            subprocess.check_call(["bash", "scripts/build_lib.sh"], cwd=ROOT)
        super().run()


class BDistWheel(bdist_wheel):
    def finalize_options(self) -> None:
        super().finalize_options()
        # Ensure the wheel is tagged as platform-specific because it bundles a shared library.
        self.root_is_pure = False


class BinaryDistribution(Distribution):
    def has_ext_modules(self) -> bool:
        return True


setup(
    cmdclass={"build_py": BuildPy, "bdist_wheel": BDistWheel},
    distclass=BinaryDistribution,
)
