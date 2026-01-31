import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    config_dir = Path.home() / ".localstream"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def config_exists() -> bool:
    return get_config_path().exists()


def _read_raw_config() -> dict:
    config_path = get_config_path()
    if not config_path.exists():
        return {"active_profile": "default", "profiles": {"default": get_default_config()}}
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if "server_ip" in data:
        new_data = {
            "active_profile": "default",
            "profiles": {
                "default": data
            }
        }
        _write_raw_config(new_data)
        return new_data
        
    return data


def _write_raw_config(data: dict) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    raw = _read_raw_config()
    active = raw.get("active_profile", "default")
    return raw.get("profiles", {}).get(active, get_default_config())


def save_config(config: dict) -> None:
    raw = _read_raw_config()
    active = raw.get("active_profile", "default")
    if "profiles" not in raw:
        raw["profiles"] = {}
    raw["profiles"][active] = config
    _write_raw_config(raw)


def get_default_config() -> dict:
    return {
        "server_ip": "",
        "server_port": 53,
        "local_port": 5201,
        "domain": "",
        "is_locked": False,
        "keep_alive_interval": 200,
        "congestion_control": "bbr",
        "enable_gso": False,
        "enable_fragmentation": False,
        "fragment_size": 77,
        "fragment_delay": 200,
        "auto_restart_minutes": 0
    }


def is_profile_locked(name: str = None) -> bool:
    raw = _read_raw_config()
    if name is None:
        name = raw.get("active_profile", "default")
    profile = raw.get("profiles", {}).get(name, {})
    return profile.get("is_locked", False)


def create_profile_with_lock(name: str, config: dict, is_locked: bool) -> None:
    raw = _read_raw_config()
    if "profiles" not in raw:
        raw["profiles"] = {}
    config["is_locked"] = is_locked
    raw["profiles"][name] = config
    _write_raw_config(raw)


def list_profiles() -> list:
    raw = _read_raw_config()
    return list(raw.get("profiles", {}).keys())


def get_active_profile_name() -> str:
    raw = _read_raw_config()
    return raw.get("active_profile", "default")


def switch_profile(name: str) -> bool:
    raw = _read_raw_config()
    if name in raw.get("profiles", {}):
        raw["active_profile"] = name
        _write_raw_config(raw)
        return True
    return False


def create_profile(name: str, config: dict = None) -> None:
    raw = _read_raw_config()
    if config is None:
        config = get_default_config()
    if "profiles" not in raw:
        raw["profiles"] = {}
    raw["profiles"][name] = config
    _write_raw_config(raw)


def delete_profile(name: str) -> bool:
    raw = _read_raw_config()
    if name == "default":
        return False
    if name == raw.get("active_profile"):
        return False
    
    if name in raw.get("profiles", {}):
        del raw["profiles"][name]
        _write_raw_config(raw)
        return True
    return False
