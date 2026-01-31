import sys
import os
import platform

APP_NAME = "LocalStream"

def _is_windows():
    return platform.system().lower() == "windows"

def enable_autostart(args=""):
    if not _is_windows():
        return False
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        cmd = f'"{exe_path}" {args}'
    else:
        python_exe = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        safe_script_path = os.path.dirname(script_path)
        module_cmd = "-m localstream"
        cmd = f'"{python_exe}" {module_cmd} {args}'
    
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)
    return True

def disable_autostart():
    if not _is_windows():
        return False
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_ALL_ACCESS
    )
    try:
        winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
    winreg.CloseKey(key)
    return True

def is_autostart_enabled():
    if not _is_windows():
        return False
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_READ
    )
    try:
        winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(key)

