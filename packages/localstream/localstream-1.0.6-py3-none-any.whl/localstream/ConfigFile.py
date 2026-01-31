import json
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet

FILE_HEADER = b"LOCALSTREAM_V1"
APP_SIGNATURE = b"LocalStream_SecureConfig_2024"


def _get_encryption_key() -> bytes:
    key_material = hashlib.sha256(APP_SIGNATURE).digest()
    return base64.urlsafe_b64encode(key_material)


def _get_fernet() -> Fernet:
    return Fernet(_get_encryption_key())


def export_config(config: dict, file_path: Path, locked: bool = False) -> bool:
    try:
        export_data = {
            "config": config,
            "locked": locked
        }
        json_data = json.dumps(export_data, ensure_ascii=False)
        
        fernet = _get_fernet()
        encrypted_data = fernet.encrypt(json_data.encode("utf-8"))
        
        with open(file_path, "wb") as f:
            f.write(FILE_HEADER + b"\n")
            f.write(b"1" if locked else b"0")
            f.write(b"\n")
            f.write(encrypted_data)
        
        return True
    except Exception:
        return False


def import_config(file_path: Path) -> tuple:
    try:
        with open(file_path, "rb") as f:
            header = f.readline().strip()
            if header != FILE_HEADER:
                return None, False, "Invalid file format"
            
            locked_flag = f.readline().strip()
            is_locked = locked_flag == b"1"
            
            encrypted_data = f.read()
        
        fernet = _get_fernet()
        decrypted_data = fernet.decrypt(encrypted_data)
        export_data = json.loads(decrypted_data.decode("utf-8"))
        
        config = export_data.get("config", {})
        is_locked = export_data.get("locked", False)
        
        return config, is_locked, None
    except Exception as e:
        return None, False, str(e)


def is_valid_local_file(file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            header = f.readline().strip()
            return header == FILE_HEADER
    except Exception:
        return False


def get_file_info(file_path: Path) -> dict:
    try:
        with open(file_path, "rb") as f:
            header = f.readline().strip()
            if header != FILE_HEADER:
                return None
            
            locked_flag = f.readline().strip()
            is_locked = locked_flag == b"1"
            
            return {
                "valid": True,
                "locked": is_locked,
                "path": str(file_path)
            }
    except Exception:
        return None
