# ===----------------------------------------------------------------------=== #
#
# This file is Modular Inc proprietary.
#
# ===----------------------------------------------------------------------=== #

"""Contains entrypoints for the Mojo development wheel"""

import os
import sys

from mojo._entrypoints import _entrypoint
from mojo._package_root import get_package_root
from mojo.run import _mojo_env


def exec_gpu_query() -> None:
    _entrypoint("gpu-query")


def exec_lldb_argdumper() -> None:
    _entrypoint("lldb-argdumper")


def exec_lldb_dap() -> None:
    root = get_package_root()
    assert root
    env = _mojo_env()

    args = [
        "--pre-init-command",
        f"?!plugin load {env['MODULAR_MOJO_MAX_LLDB_PLUGIN_PATH']}",
        "--pre-init-command",
        f"?command script import {env['MODULAR_MOJO_MAX_LLDB_VISUALIZERS_PATH']}/lldbDataFormatters.py",
        "--pre-init-command",
        f"?command script import {env['MODULAR_MOJO_MAX_LLDB_VISUALIZERS_PATH']}/mlirDataFormatters.py",
    ] + sys.argv

    os.execve(root / "bin" / "lldb-dap", args, env)


def exec_lldb_server() -> None:
    _entrypoint("lldb-server")


def exec_llvm_symbolizer() -> None:
    _entrypoint("llvm-symbolizer")


def exec_mojo_lldb() -> None:
    _entrypoint("mojo-lldb")


def exec_mojo_lsp_server() -> None:
    _entrypoint("mojo-lsp-server")
