"""Code Interpreter — sandboxed Python execution with timeout."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool

_SAFETY_HEADER = """\
import socket as _socket

def _blocked(*a, **kw):
    raise OSError("网络访问已在沙筗中禁用")

_socket.socket = _blocked

import builtins as _b
_orig_open = _b.open

def _safe_open(f, mode="r", *a, **kw):
    if isinstance(mode, str) and any(c in mode for c in ("w", "a", "x")):
        raise PermissionError("文件写入已在沙筗中禁用")
    return _orig_open(f, mode, *a, **kw)

_b.open = _safe_open

"""


@tool
def code_interpreter(code: str) -> str:
    """在安全沙筗中执行 Python 代码，返回输出结果。
    支持：数学计算、数据处理、正则表达式、字符串操作、JSON/CSV 解析、算法验证等。
    限制：无网络访问、无文件写入、执行时间≤ 10 秒。

    Args:
        code: 要执行的 Python 代码字符串
    """
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(_SAFETY_HEADER + "\n" + code)
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        parts: list[str] = []
        if result.stdout.strip():
            parts.append(f"```\n{result.stdout.strip()[:3000]}\n```")
        if result.stderr.strip():
            parts.append(f"错误信息:\n{result.stderr.strip()[:500]}")
        if result.returncode != 0 and not parts:
            parts.append(f"非零退出码: {result.returncode}")

        return "\n".join(parts) if parts else "代码执行完毕，无输出"

    except subprocess.TimeoutExpired:
        return "执行超时（上限 10 秒），请优化代码效率"
    except Exception as e:
        return f"沙筗启动失败: {e}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
