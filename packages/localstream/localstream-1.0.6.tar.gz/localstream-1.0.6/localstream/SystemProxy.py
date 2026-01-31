import platform

INTERNET_OPTION_REFRESH = 37
INTERNET_OPTION_SETTINGS_CHANGED = 39

def _is_windows():
    return platform.system().lower() == "windows"

def set_system_proxy(host, port, bypass=""):
    if not _is_windows():
        return
    import ctypes
    import winreg
    proxy_server = f"{host}:{port}"
    
    internet_settings = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        0, winreg.KEY_ALL_ACCESS
    )
    
    winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 1)
    winreg.SetValueEx(internet_settings, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
    winreg.SetValueEx(internet_settings, "ProxyOverride", 0, winreg.REG_SZ, bypass)
    
    winreg.CloseKey(internet_settings)
    _refresh_settings()

def unset_system_proxy():
    if not _is_windows():
        return
    import winreg
    internet_settings = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        0, winreg.KEY_ALL_ACCESS
    )
    
    winreg.SetValueEx(internet_settings, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    
    winreg.CloseKey(internet_settings)
    _refresh_settings()

def _refresh_settings():
    if not _is_windows():
        return
    import ctypes
    internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
    internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
    internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

