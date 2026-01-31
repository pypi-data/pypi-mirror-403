__version__ = "1.0.5"

from localstream.Config import (
    get_config_dir,
    get_config_path,
    config_exists,
    load_config,
    save_config,
    get_default_config,
    list_profiles,
    get_active_profile_name,
    switch_profile,
    create_profile,
    delete_profile,
    is_profile_locked,
    create_profile_with_lock,
)

from localstream.ConfigFile import (
    export_config as export_config_file,
    import_config as import_config_file,
    is_valid_local_file,
    get_file_info,
)

from localstream.Connection import (
    ConnectionManager,
    is_admin,
    run_as_admin,
)

from localstream.Autostart import (
    enable_autostart,
    disable_autostart,
    is_autostart_enabled,
)

from localstream.Speedtest import run_speedtest

from localstream.SystemProxy import (
    set_system_proxy,
    unset_system_proxy,
)

from localstream.PrivoxyManager import (
    start_privoxy,
    stop_privoxy,
)

from localstream.Downloader import (
    get_bin_dir,
    get_client_path,
    get_tun2proxy_path,
    get_wintun_path,
    client_exists,
    tun2proxy_exists,
    privoxy_exists,
    download_client,
    download_tun2proxy,
    download_privoxy,
    get_platform,
    is_windows,
    is_linux,
)


from localstream.Fragmenter import (
    TlsFragmenter,
    create_fragmenter,
)

__all__ = [
    "__version__",
    "get_config_dir",
    "get_config_path",
    "config_exists",
    "load_config",
    "save_config",
    "get_default_config",
    "list_profiles",
    "get_active_profile_name",
    "switch_profile",
    "create_profile",
    "delete_profile",
    "is_profile_locked",
    "create_profile_with_lock",
    "export_config_file",
    "import_config_file",
    "is_valid_local_file",
    "get_file_info",
    "ConnectionManager",
    "is_admin",
    "run_as_admin",
    "enable_autostart",
    "disable_autostart",
    "is_autostart_enabled",
    "run_speedtest",
    "set_system_proxy",
    "unset_system_proxy",
    "start_privoxy",
    "stop_privoxy",
    "get_bin_dir",
    "get_client_path",
    "get_tun2proxy_path",
    "get_wintun_path",
    "client_exists",
    "tun2proxy_exists",
    "privoxy_exists",
    "download_client",
    "download_tun2proxy",
    "download_privoxy",
    "get_platform",
    "is_windows",
    "is_linux",

    "TlsFragmenter",
    "create_fragmenter",
]
