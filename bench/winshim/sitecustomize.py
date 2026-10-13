"""Bench-only shim for native Windows: os.nice and os.getloadavg for the emulator's scripts.

Upstream's probe_throughput workers call os.nice(10), which Windows Python lacks. run_all.py puts
this folder on PYTHONPATH for bench runs only, so every spawned worker imports it at start-up.
A positive increment sets BELOW_NORMAL_PRIORITY_CLASS on the calling process; it returns 0.
os.getloadavg raises OSError, which probe_throughput._load_average already turns into [].
Upstream is not patched. run_all.py records this file's sha256 in 00_env.txt.
"""

import os
import sys

if sys.platform == "win32" and not hasattr(os, "nice"):

    def nice(increment: int) -> int:
        if increment > 0:
            import ctypes  # noqa: PLC0415
            from ctypes import wintypes  # noqa: PLC0415

            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            k32.SetPriorityClass.argtypes = (wintypes.HANDLE, wintypes.DWORD)
            k32.SetPriorityClass.restype = wintypes.BOOL
            if not k32.SetPriorityClass(k32.GetCurrentProcess(), 0x00004000):  # BELOW_NORMAL
                raise ctypes.WinError(ctypes.get_last_error())
        return 0

    os.nice = nice

if sys.platform == "win32" and not hasattr(os, "getloadavg"):

    def getloadavg():
        raise OSError("load average is not available on Windows")

    os.getloadavg = getloadavg
