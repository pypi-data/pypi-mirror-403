import subprocess
import os
import sys
from pathlib import Path
from localstream.Downloader import get_privoxy_dir, get_privoxy_exe

def start_privoxy(socks_port, http_port):
    privoxy_dir = get_privoxy_dir()
    privoxy_exe = get_privoxy_exe()
    config_path = privoxy_dir / "config.txt"
    
    config_content = f"""listen-address 127.0.0.1:{http_port}
forward-socks5 / 127.0.0.1:{socks_port} .
keep-alive-timeout 5
toggle 1
enable-remote-toggle 0
enable-remote-http-toggle 0
enable-edit-actions 0
enforce-blocks 0
buffer-limit 4096"""
    
    with open(config_path, "w") as f:
        f.write(config_content)
        
    process = subprocess.Popen(
        [str(privoxy_exe), str(config_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    return process

def stop_privoxy(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
