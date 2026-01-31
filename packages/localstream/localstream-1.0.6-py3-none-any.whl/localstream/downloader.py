import os
import sys
import platform
import subprocess
import requests
import zipfile
import tempfile
from pathlib import Path

from localstream.Config import get_config_dir


CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


SLIPSTREAM_WINDOWS_URL = "https://github.com/AliRezaBeigy/slipstream-rust-deploy/releases/latest/download/slipstream-client-windows-amd64.exe"
SLIPSTREAM_LINUX_URL = "https://github.com/AliRezaBeigy/slipstream-rust-deploy/releases/latest/download/slipstream-client-linux-amd64"

TUN2PROXY_WINDOWS_URL = "https://github.com/tun2proxy/tun2proxy/releases/download/v0.7.19/tun2proxy-x86_64-pc-windows-msvc.zip"
TUN2PROXY_LINUX_URL = "https://github.com/tun2proxy/tun2proxy/releases/download/v0.7.19/tun2proxy-x86_64-unknown-linux-gnu.zip"

WINTUN_URL = "https://www.wintun.net/builds/wintun-0.14.1.zip"

PRIVOXY_WINDOWS_URL = "https://github.com/ssrlive/privoxy/releases/latest/download/privoxy-windows-x64.zip"


def get_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    return "unsupported"


def is_windows() -> bool:
    return get_platform() == "windows"


def is_linux() -> bool:
    return get_platform() == "linux"


def get_bin_dir() -> Path:
    bin_dir = get_config_dir() / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


def get_client_path() -> Path:
    if is_windows():
        return get_bin_dir() / "slipstream-client.exe"
    return get_bin_dir() / "slipstream-client"


def get_tun2proxy_path() -> Path:
    if is_windows():
        return get_bin_dir() / "tun2proxy.exe"
    return get_bin_dir() / "tun2proxy"


def get_wintun_path() -> Path:
    return get_bin_dir() / "wintun.dll"


def client_exists() -> bool:
    return get_client_path().exists()


def tun2proxy_exists() -> bool:
    tun2proxy_path = get_tun2proxy_path()
    if is_windows():
        return tun2proxy_path.exists() and get_wintun_path().exists()
    return tun2proxy_path.exists()


def download_file(url: str, dest_path: Path, name: str) -> bool:
    print(f"\n{CYAN}╔═══════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║{RESET}  {YELLOW}⟳{RESET} Downloading {name}...{' ' * (37 - len(name))}{CYAN}║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════╝{RESET}")
    print(f"\n{DIM}  URL: {url[:50]}...{RESET}")
    print(f"{DIM}  Destination: {dest_path}{RESET}\n")
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 40
                        filled = int(bar_length * downloaded / total_size)
                        bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (bar_length - filled)}{RESET}"
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        print(f"\r  {bar} {percent:5.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
        
        print(f"\n\n{GREEN}✓{RESET} Download complete!")
        
        if is_linux() and not str(dest_path).endswith(".zip"):
            os.chmod(dest_path, 0o755)
        
        return True
        
    except requests.RequestException as e:
        print(f"\n\n{RED}✗{RESET} Download failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def download_client(force: bool = False) -> bool:
    client_path = get_client_path()
    
    if client_path.exists() and not force:
        return True
    
    if is_windows():
        url = SLIPSTREAM_WINDOWS_URL
    elif is_linux():
        url = SLIPSTREAM_LINUX_URL
    else:
        print(f"{RED}✗{RESET} Unsupported platform: {get_platform()}")
        return False
    
    return download_file(url, client_path, "slipstream-client")


def download_tun2proxy(force: bool = False) -> bool:
    tun2proxy_path = get_tun2proxy_path()
    bin_dir = get_bin_dir()
    
    if is_windows():
        wintun_path = get_wintun_path()
        if tun2proxy_path.exists() and wintun_path.exists() and not force:
            return True
    else:
        if tun2proxy_path.exists() and not force:
            return True
    
    if is_windows():
        url = TUN2PROXY_WINDOWS_URL
    elif is_linux():
        url = TUN2PROXY_LINUX_URL
    else:
        print(f"{RED}✗{RESET} Unsupported platform: {get_platform()}")
        return False
    
    if not tun2proxy_path.exists() or force:
        print(f"\n{CYAN}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}║{RESET}  {YELLOW}⟳{RESET} Downloading tun2proxy...                            {CYAN}║{RESET}")
        print(f"{CYAN}╚═══════════════════════════════════════════════════════╝{RESET}")
        print(f"\n{DIM}  URL: {url[:50]}...{RESET}\n")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            bar_length = 40
                            filled = int(bar_length * downloaded / total_size)
                            bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (bar_length - filled)}{RESET}"
                            size_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            print(f"\r  {bar} {percent:5.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
            
            print(f"\n\n{YELLOW}⟳{RESET} Extracting tun2proxy...")
            
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                for file_info in zip_ref.namelist():
                    if is_windows():
                        if file_info.endswith("tun2proxy-bin.exe") or file_info.endswith("tun2proxy.exe"):
                            with zip_ref.open(file_info) as src:
                                with open(tun2proxy_path, "wb") as dst:
                                    dst.write(src.read())
                            break
                        elif file_info.endswith(".exe") and "tun2proxy" in file_info:
                            with zip_ref.open(file_info) as src:
                                with open(tun2proxy_path, "wb") as dst:
                                    dst.write(src.read())
                            break
                    else:
                        if "tun2proxy" in file_info and not file_info.endswith("/"):
                            with zip_ref.open(file_info) as src:
                                with open(tun2proxy_path, "wb") as dst:
                                    dst.write(src.read())
                            os.chmod(tun2proxy_path, 0o755)
                            break
            
            tmp_path.unlink()
            
            if not tun2proxy_path.exists():
                print(f"{RED}✗{RESET} Failed to extract tun2proxy from archive")
                return False
            
            print(f"{GREEN}✓{RESET} tun2proxy extracted!")
            
        except Exception as e:
            print(f"\n{RED}✗{RESET} Failed to download tun2proxy: {e}")
            return False
    
    if is_windows():
        wintun_path = get_wintun_path()
        if not wintun_path.exists() or force:
            print(f"\n{YELLOW}⟳{RESET} Downloading wintun driver...")
            
            try:
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                
                response = requests.get(WINTUN_URL, timeout=120)
                response.raise_for_status()
                
                with open(tmp_path, "wb") as f:
                    f.write(response.content)
                
                print(f"{YELLOW}⟳{RESET} Extracting wintun.dll...")
                
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    for file_info in zip_ref.namelist():
                        if file_info.endswith("amd64/wintun.dll"):
                            with zip_ref.open(file_info) as src:
                                with open(wintun_path, "wb") as dst:
                                    dst.write(src.read())
                            break
                
                tmp_path.unlink()
                
                if not wintun_path.exists():
                    print(f"{RED}✗{RESET} Failed to extract wintun.dll from archive")
                    return False
                
                print(f"{GREEN}✓{RESET} Wintun driver extracted!")
                
            except Exception as e:
                print(f"{RED}✗{RESET} Failed to download wintun: {e}")
                return False
    
    return True


def get_privoxy_dir() -> Path:
    return get_bin_dir() / "privoxy"


def get_privoxy_exe() -> Path:
    if is_windows():
        return get_privoxy_dir() / "privoxy.exe"
    return Path("/usr/sbin/privoxy")


def privoxy_exists() -> bool:
    if is_linux():
        result = subprocess.run(["which", "privoxy"], capture_output=True)
        return result.returncode == 0
    return get_privoxy_exe().exists()


def download_privoxy(force: bool = False) -> bool:
    if is_linux():
        print(f"\n{CYAN}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}║{RESET}  {YELLOW}⟳{RESET} Installing Privoxy via apt...                       {CYAN}║{RESET}")
        print(f"{CYAN}╚═══════════════════════════════════════════════════════╝{RESET}\n")
        
        try:
            result = subprocess.run(
                ["sudo", "apt", "install", "-y", "privoxy"],
                check=True
            )
            print(f"\n{GREEN}✓{RESET} Privoxy installed!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n{RED}✗{RESET} Failed to install Privoxy: {e}")
            print(f"{YELLOW}!{RESET} Try manually: sudo apt install privoxy")
            return False
        except FileNotFoundError:
            print(f"\n{RED}✗{RESET} apt not found. Install privoxy manually.")
            return False
    
    privoxy_dir = get_privoxy_dir()
    privoxy_exe = get_privoxy_exe()
    
    if privoxy_exe.exists() and not force:
        return True
    
    print(f"\n{DIM}  URL: {PRIVOXY_WINDOWS_URL[:60]}...{RESET}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
        print(f"  {DIM}Requesting...{RESET}")
        response = requests.get(PRIVOXY_WINDOWS_URL, headers=headers, stream=True, timeout=120, allow_redirects=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 40
                        filled = int(bar_length * downloaded / total_size)
                        bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (bar_length - filled)}{RESET}"
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        print(f"\r  {bar} {percent:5.1f}% ({size_mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)

        print(f"\n\n{YELLOW}⟳{RESET} Extracting Privoxy...")
        
        if privoxy_dir.exists():
            import shutil
            shutil.rmtree(privoxy_dir)
        privoxy_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            for file_info in zip_ref.namelist():
                if file_info.endswith(".exe") or file_info.endswith(".dll") or file_info.endswith(".conf") or file_info.endswith("config.txt"):
                    filename = os.path.basename(file_info)
                    if filename:
                        target = privoxy_dir / filename
                        with zip_ref.open(file_info) as src:
                            with open(target, "wb") as dst:
                                dst.write(src.read())

        tmp_path.unlink()
        
        if not privoxy_exe.exists():
            print(f"{RED}✗{RESET} Failed to extract privoxy.exe")
            return False
            
        print(f"{GREEN}✓{RESET} Privoxy installed!")
        return True
        
    except Exception as e:
        print(f"\n{RED}✗{RESET} Failed to download Privoxy: {e}")
        return False
