# Copyright (c) 2025 Adam Karpierz
# SPDX-License-Identifier: Zlib

from __future__ import annotations

from typing import Any, NamedTuple
import sys
import os
from pathlib import Path
import importlib.metadata  # noqa: F401
from importlib.metadata import PackageMetadata
from functools import partial  # noqa: F401
import sysconfig
import json
import warnings  # noqa: F401

import nox
import build.util
import packaging.version
import packaging.tags
from packaging.utils import canonicalize_name
from packaging.utils import canonicalize_version

__all__ = ('print', 'pprint', 'Session')
__dir__ = lambda: __all__

# Nox default configuration

nox.needs_version = ">=2025.11.12"
nox.options.default_venv_backend = "uv|virtualenv"
nox.options.reuse_existing_virtualenvs = True

nox.options.error_on_missing_interpreters = False

# Helpers & Utils

print = print  # noqa: A001
from rich import print as pprint  # noqa: E402


class PackageData(NamedTuple):
    NAME: str
    VERSION: str
    FULLNAME: str
    TOP_LEVELS: list[str]
    version: packaging.version.Version
    metadata: PackageMetadata

def _get_package_data(package_path: Path | str | None = None) -> PackageData:
    pkg_globals = sys._getframe(1).f_globals
    package_path = (Path(pkg_globals["__file__"]).resolve().parents[0]
                    if package_path is None else Path(package_path))
    pkg_metadata = build.util.project_wheel_metadata(package_path)
    return PackageData(
        NAME     = pkg_metadata["Name"],
        VERSION  = pkg_metadata["Version"],
        FULLNAME = "{}-{}".format(
            canonicalize_name(pkg_metadata["Name"] or "UNKNOWN").replace("-", "_"),
            canonicalize_version(pkg_metadata["Version"] or "0.0.0", strip_trailing_zero=False)),
        TOP_LEVELS = [pkg_metadata["Name"]],
        version  = packaging.version.parse(pkg_metadata["Version"]),
        metadata = pkg_metadata,
    )

# Attach helper to Session class
nox.get_package_data = _get_package_data  # noqa: E305


class version_info(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

class Session(nox.sessions.Session):

    __slots__ = ()

    def run_quiet(self: nox.Session, *args: Any, **kwargs: Any) -> Any | None:
        """Run a command silently: no 'nox > ...' header and no output."""
        kwargs.setdefault("silent", True)
        kwargs.setdefault("log", False)
        return self.run(*args, **kwargs)

    def py(self: nox.Session, *args: Any, **kwargs: Any) -> Any | None:
        """Run session python."""
        return self.run("python", *args, **kwargs)

    def py_quiet(self: nox.Session, *args: Any, **kwargs: Any) -> Any | None:
        """Run session python silently: no 'nox > ...' header and no output."""
        kwargs.setdefault("silent", True)
        kwargs.setdefault("log", False)
        return self.py(*args, **kwargs)

    @property
    def is_initial_build(self: nox.Session) -> bool:
        return os.environ.get("PKG_INITIAL_BUILD") == "1"

    @property
    def site_packages(self: nox.Session) -> Path:
        # Monkey-patch: deterministic, explicit, contributor-friendly
        return self._get_site_packages(Path(self.virtualenv.location))

    @staticmethod
    def _get_site_packages(venv_dir: Path) -> Path:
        paths = sysconfig.get_paths(vars={"base": str(venv_dir),
                                          "platbase": str(venv_dir)})
        return Path(paths["purelib"])

    @property
    def python_version_info(self: nox.Session) -> version_info:
        return version_info(*json.loads(self.run_quiet("python",
            "-c", "import sys, json ; print(json.dumps(sys.version_info))").strip()))

    @property
    def python_version_nodot(self: nox.Session) -> str:
        return self.run_quiet("python",
            "-c", "from sys import version_info as v ; print(f'{v.major}{v.minor}')").strip()

    @property
    def python_implementation(self: nox.Session) -> str:
        return self.run_quiet("python",
            "-c", "import platform ; print(platform.python_implementation())").strip()

    @property
    def PKG_PVER(self: nox.Session) -> str:
        return self.python_version_nodot

    @property
    def PKG_IMPL(self: nox.Session) -> str:
        # from packaging.tags.interpreter_name()
        name = self.run_quiet("python",
            "-c", "import sys ; print(sys.implementation.name)").strip()
        return packaging.tags.INTERPRETER_SHORT_NAMES.get(name) or name

# Attach helpers to Session class
nox.sessions.Session = Session  # noqa: E305
