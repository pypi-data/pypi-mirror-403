import sys
import os
import argparse
import time

try:
    import colorama
    colorama.init()
except ImportError:
    pass

from localstream.Config import (
    config_exists, load_config, save_config, get_default_config,
    list_profiles, get_active_profile_name, switch_profile,
    create_profile, delete_profile, is_profile_locked, create_profile_with_lock
)
from localstream.ConfigFile import export_config, import_config, is_valid_local_file
from localstream.Connection import ConnectionManager, is_admin
from localstream.Downloader import (
    client_exists, download_client, tun2proxy_exists, download_tun2proxy,
    privoxy_exists, download_privoxy, is_windows, is_linux
)
from localstream.Speedtest import run_speedtest
from localstream.Autostart import enable_autostart, disable_autostart, is_autostart_enabled


CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


LOGO = f"""
{CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  {MAGENTA}██╗      ██████╗  ██████╗ █████╗ ██╗     {CYAN}                    ║
║  {MAGENTA}██║     ██╔═══██╗██╔════╝██╔══██╗██║     {CYAN}                    ║
║  {MAGENTA}██║     ██║   ██║██║     ███████║██║     {CYAN}                    ║
║  {MAGENTA}██║     ██║   ██║██║     ██╔══██║██║     {CYAN}                    ║
║  {MAGENTA}███████╗╚██████╔╝╚██████╗██║  ██║███████╗{CYAN}                    ║
║  {MAGENTA}╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝{CYAN}                    ║
║                                                               ║
║  {BLUE}███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗{CYAN}         ║
║  {BLUE}██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║{CYAN}         ║
║  {BLUE}███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║{CYAN}         ║
║  {BLUE}╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║{CYAN}         ║
║  {BLUE}███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║{CYAN}         ║
║  {BLUE}╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝{CYAN}         ║
║                                                               ║
║         {DIM}SlipStream DNS Tunnel • Python CLI Client{CYAN}             ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
"""

MINI_LOGO = f"""
{CYAN}╔═══════════════════════════════════════════╗
║  {MAGENTA}LocalStream{CYAN} • {DIM}SlipStream CLI Client{CYAN}      ║
╚═══════════════════════════════════════════╝{RESET}
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_logo(mini: bool = False):
    if mini:
        print(MINI_LOGO)
    else:
        print(LOGO)


import re

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def print_box(title: str, content: list, color: str = CYAN):
    # Calculate width based on visible length (stripping ANSI codes)
    visible_title_len = len(strip_ansi(title))
    max_len = 0
    if content:
        max_len = max(len(strip_ansi(line)) for line in content)
    
    max_len = max(max_len, visible_title_len + 4)
    width = max_len + 4
    
    print(f"\n{color}┌{'─' * width}┐{RESET}")
    # Title line
    padding_title = width - visible_title_len - 2
    print(f"{color}│{RESET}  {BOLD}{title}{RESET}{' ' * padding_title}{color}│{RESET}")
    print(f"{color}├{'─' * width}┤{RESET}")
    
    for line in content:
        visible_len = len(strip_ansi(line))
        padding = width - visible_len - 2
        print(f"{color}│{RESET}  {line}{' ' * padding}{color}│{RESET}")
    
    print(f"{color}└{'─' * width}┘{RESET}")


def print_config(config: dict):
    active_profile = get_active_profile_name()
    is_locked = is_profile_locked()
    admin_status = f"{GREEN}✓ Admin{RESET}" if is_admin() else f"{YELLOW}○ User{RESET}"
    
    if is_locked:
        server = f"{YELLOW}●●●●●●●●{RESET}"
        domain = f"{YELLOW}●●●●●●●●{RESET}"
        lock_badge = f" {RED}[LOCKED]{RESET}"
    else:
        server = f"{config.get('server_ip', 'N/A')}:{config.get('server_port', 53)}"
        domain = config.get('domain', 'N/A')
        lock_badge = ""
    
    content = [
        f"{GREEN}●{RESET} Profile    : {WHITE}{active_profile}{RESET}{lock_badge}",
        f"{GREEN}●{RESET} Server     : {WHITE}{server}{RESET}",
        f"{GREEN}●{RESET} Domain     : {WHITE}{domain}{RESET}",
        f"{GREEN}●{RESET} Local Port : {WHITE}{config.get('local_port', 5201)}{RESET}",
        f"{DIM}─────────────────────────────────{RESET}",
        f"{BLUE}●{RESET} Status     : {admin_status}",
    ]
    print_box("Current Configuration", content, CYAN)


def get_input(prompt: str, default: str = "") -> str:
    if default:
        result = input(f"  {GREEN}▸{RESET} {prompt} {DIM}[{default}]{RESET}: ").strip()
        return result if result else default
    return input(f"  {GREEN}▸{RESET} {prompt}: ").strip()


def get_int_input(prompt: str, default: int) -> int:
    while True:
        result = input(f"  {GREEN}▸{RESET} {prompt} {DIM}[{default}]{RESET}: ").strip()
        if not result:
            return default
        try:
            return int(result)
        except ValueError:
            print(f"  {RED}✗{RESET} Please enter a valid number")


def prompt_for_config() -> dict:
    print(f"\n{YELLOW}━━━ Server Configuration ━━━{RESET}\n")
    
    config = get_default_config()
    existing = load_config()
    
    config["server_ip"] = get_input("Server IP", existing.get("server_ip"))
    while not config["server_ip"]:
        print(f"  {RED}✗{RESET} Server IP is required")
        config["server_ip"] = get_input("Server IP")
            
    config["server_port"] = get_int_input("Server Port", existing.get("server_port", 53))
    config["local_port"] = get_int_input("Local Port", existing.get("local_port", 5201))
    
    config["domain"] = get_input("Domain", existing.get("domain"))
    while not config["domain"]:
        print(f"  {RED}✗{RESET} Domain is required")
        config["domain"] = get_input("Domain")
            
    return config


def print_connecting_banner(config: dict, mode: str):
    is_locked = is_profile_locked()
    
    if is_locked:
        server = f"{YELLOW}●●●●●●●●{RESET}"
        domain = f"{YELLOW}●●●●●●●●{RESET}"
    else:
        server = f"{config.get('server_ip')}:{config.get('server_port')}"
        domain = config.get('domain')
    local_port = str(config.get('local_port'))

    if mode == "vpn":
        mode_display = f"{GREEN}VPN{RESET}"
    elif mode == "system":
        mode_display = f"{MAGENTA}SYSTEM{RESET}"
    else:
        mode_display = f"{BLUE}PROXY{RESET}"
    
    width = 55
    
    def print_line(content):
        visible_len = len(strip_ansi(content))
        padding = width - visible_len
        print(f"{CYAN}║{RESET}  {content}{' ' * (padding - 4)}{CYAN}║{RESET}")

    print(f"\n{CYAN}╔{'═' * (width - 2)}╗{RESET}")
    
    header = f"{GREEN}●{RESET} {BOLD}Connecting in {mode_display} Mode...{RESET}"
    print_line(header)
    
    print(f"{CYAN}╟{'─' * (width - 2)}╢{RESET}")
    
    print_line(f"Resolver   : {WHITE}{server}{RESET}")
    print_line(f"Domain     : {WHITE}{domain}{RESET}")
    print_line(f"Local Port : {WHITE}{local_port}{RESET}")
    
    print(f"{CYAN}╟{'─' * (width - 2)}╢{RESET}")
    
    # Footer
    print_line(f"{DIM}Press Ctrl+C to disconnect • Ctrl+D to restart{RESET}")
    
    print(f"{CYAN}╚{'═' * (width - 2)}╝{RESET}\n")


def handle_connection(config: dict, mode: str):
    while True:
        clear_screen()
        print_logo(mini=True)
        print_connecting_banner(config, mode)
        
        manager = ConnectionManager()
        
        if mode == "vpn":
            result = manager.connect_vpn(config)
        elif mode == "system":
            result = manager.connect_system_proxy(config)
        else:
            result = manager.connect_proxy(config)
        
        if result == "restart":
            print(f"\n{YELLOW}⟳{RESET} Restarting connection...")
            continue
        break


def handle_profiles():
    while True:
        clear_screen()
        print_logo(mini=True)
        
        profiles = list_profiles()
        active = get_active_profile_name()
        
        print(f"\n{YELLOW}━━━ Profile Management ━━━{RESET}\n")
        
        for i, name in enumerate(profiles, 1):
            status = f"{GREEN}●{RESET}" if name == active else "○"
            locked = is_profile_locked(name)
            lock_badge = f" {RED}[LOCKED]{RESET}" if locked else ""
            print(f"  {status} {i}. {name}{lock_badge}")
            
        print(f"\n{DIM}─────────────────────────────────{RESET}")
        print(f"  {YELLOW}[S]{RESET} Switch Profile")
        print(f"  {YELLOW}[N]{RESET} New Profile")
        print(f"  {YELLOW}[D]{RESET} Delete Profile")
        print(f"  {YELLOW}[I]{RESET} Import Config (.local)")
        print(f"  {YELLOW}[E]{RESET} Export Config (.local)")
        print(f"  {YELLOW}[B]{RESET} Back")
        
        choice = input(f"\n  {MAGENTA}▸{RESET} Select option: ").strip().lower()
        
        if choice == 'b':
            break
            
        if choice == 's':
            name = get_input("Profile Name")
            if switch_profile(name):
                print(f"  {GREEN}✓{RESET} Switched to {name}")
                time.sleep(1)
            else:
                print(f"  {RED}✗{RESET} Profile not found")
                time.sleep(1)
        
        elif choice == 'n':
            name = get_input("New Profile Name")
            if name in profiles:
                print(f"  {RED}✗{RESET} Profile exists")
                time.sleep(1)
                continue
            
            print()
            config = prompt_for_config()
            create_profile(name, config)
            switch_profile(name)
            print(f"  {GREEN}✓{RESET} Profile created and selected")
            time.sleep(1)
            
        elif choice == 'd':
            name = get_input("Profile to delete")
            if delete_profile(name):
                print(f"  {GREEN}✓{RESET} Deleted {name}")
                time.sleep(1)
            else:
                print(f"  {RED}✗{RESET} Cannot delete {name}")
                time.sleep(1)
        
        elif choice == 'i':
            handle_import_config()
        
        elif choice == 'e':
            handle_export_config()


def handle_import_config():
    from pathlib import Path
    
    print(f"\n{YELLOW}━━━ Import Config ━━━{RESET}\n")
    
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Select LocalStream Config File",
            filetypes=[("LocalStream Config", "*.local"), ("All Files", "*.*")],
            initialdir=Path.home()
        )
        root.destroy()
        
        if not file_path:
            print(f"  {YELLOW}!{RESET} No file selected")
            time.sleep(1)
            return
            
    except Exception:
        print(f"  {YELLOW}!{RESET} File picker not available")
        file_path = get_input("Enter file path")
        if not file_path:
            return
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"  {RED}✗{RESET} File not found")
        time.sleep(2)
        return
    
    if not is_valid_local_file(file_path):
        print(f"  {RED}✗{RESET} Invalid LocalStream config file")
        time.sleep(2)
        return
    
    config, is_locked, error = import_config(file_path)
    
    if error:
        print(f"  {RED}✗{RESET} Import failed: {error}")
        time.sleep(2)
        return
    
    profile_name = get_input("Profile name for imported config", file_path.stem)
    
    existing_profiles = list_profiles()
    if profile_name in existing_profiles:
        overwrite = get_input(f"Profile '{profile_name}' exists. Overwrite? (y/n)", "n")
        if overwrite.lower() != 'y':
            print(f"  {YELLOW}!{RESET} Import cancelled")
            time.sleep(1)
            return
    
    create_profile_with_lock(profile_name, config, is_locked)
    switch_profile(profile_name)
    
    lock_status = f"{RED}[LOCKED]{RESET}" if is_locked else f"{GREEN}[UNLOCKED]{RESET}"
    print(f"  {GREEN}✓{RESET} Imported: {profile_name} {lock_status}")
    time.sleep(2)


def handle_export_config():
    from pathlib import Path
    
    print(f"\n{YELLOW}━━━ Export Config ━━━{RESET}\n")
    
    if is_profile_locked():
        print(f"  {RED}✗{RESET} Cannot export a locked profile")
        time.sleep(2)
        return
    
    config = load_config()
    active = get_active_profile_name()
    
    lock_choice = get_input("Lock config? (y/n)", "n")
    is_locked = lock_choice.lower() == 'y'
    
    if is_locked:
        print(f"  {YELLOW}!{RESET} Locked configs hide server info and cannot be edited")
    
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.asksaveasfilename(
            title="Save LocalStream Config",
            defaultextension=".local",
            filetypes=[("LocalStream Config", "*.local")],
            initialfile=f"{active}.local",
            initialdir=Path.home()
        )
        root.destroy()
        
        if not file_path:
            print(f"  {YELLOW}!{RESET} Export cancelled")
            time.sleep(1)
            return
            
    except Exception:
        print(f"  {YELLOW}!{RESET} File picker not available")
        file_path = get_input("Enter save path", f"{active}.local")
        if not file_path:
            return
    
    file_path = Path(file_path)
    
    export_data = {
        "server_ip": config.get("server_ip", ""),
        "server_port": config.get("server_port", 53),
        "local_port": config.get("local_port", 5201),
        "domain": config.get("domain", "")
    }
    
    if export_config(export_data, file_path, is_locked):
        lock_status = f"{RED}[LOCKED]{RESET}" if is_locked else f"{GREEN}[UNLOCKED]{RESET}"
        print(f"  {GREEN}✓{RESET} Exported: {file_path.name} {lock_status}")
    else:
        print(f"  {RED}✗{RESET} Export failed")
    
    time.sleep(2)


def handle_tools():
    while True:
        clear_screen()
        print_logo(mini=True)
        
        content = [
            f"{YELLOW}[1]{RESET} Speed Test",
            f"{YELLOW}[2]{RESET} Back"
        ]
        print_box("Tools", content, BLUE)
        
        choice = input(f"\n  {MAGENTA}▸{RESET} Select option: ").strip()
        
        if choice == '1':
            config = load_config()
            port = config.get("local_port", 5201)
            print(f"\n  {YELLOW}!{RESET} Ensure you are connected in another terminal!")
            input(f"  {DIM}Press Enter to start test...{RESET}")
            run_speedtest(port)
            input(f"\n  {DIM}Press Enter to continue...{RESET}")
        elif choice == '2':
            break


def handle_advanced_settings():
    while True:
        clear_screen()
        print_logo(mini=True)
        
        config = load_config()
        
        keep_alive = config.get("keep_alive_interval", 200)
        congestion = config.get("congestion_control", "bbr").upper()
        gso_status = f"{GREEN}ON{RESET}" if config.get("enable_gso", False) else f"{RED}OFF{RESET}"
        frag_status = f"{GREEN}ON{RESET}" if config.get("enable_fragmentation", False) else f"{RED}OFF{RESET}"
        frag_size = config.get("fragment_size", 77)
        frag_delay = config.get("fragment_delay", 200)
        auto_restart = config.get("auto_restart_minutes", 0)
        auto_restart_str = f"{WHITE}{auto_restart}{RESET} min" if auto_restart > 0 else f"{RED}OFF{RESET}"
        
        content = [
            f"{YELLOW}[1]{RESET} Keep-Alive Interval: {WHITE}{keep_alive}{RESET} ms",
            f"{YELLOW}[2]{RESET} Congestion Control: {WHITE}{congestion}{RESET}",
            f"{YELLOW}[3]{RESET} GSO (Segmentation Offload): {gso_status}",
            f"{DIM}─────────────────────────────────{RESET}",
            f"{YELLOW}[4]{RESET} TLS Fragmentation: {frag_status}",
            f"{YELLOW}[5]{RESET} Fragment Size: {WHITE}{frag_size}{RESET} bytes",
            f"{YELLOW}[6]{RESET} Fragment Delay: {WHITE}{frag_delay}{RESET} ms",
            f"{DIM}─────────────────────────────────{RESET}",
            f"{YELLOW}[7]{RESET} Auto Restart: {auto_restart_str}",
            f"{DIM}─────────────────────────────────{RESET}",
            f"{YELLOW}[8]{RESET} Back"
        ]
        print_box("Advanced Settings", content, MAGENTA)
        
        choice = input(f"\n  {MAGENTA}▸{RESET} Select option: ").strip()
        
        if choice == '1':
            new_interval = get_int_input("Keep-Alive Interval (ms)", config.get("keep_alive_interval", 200))
            if 50 <= new_interval <= 5000:
                config["keep_alive_interval"] = new_interval
                save_config(config)
                print(f"\n  {GREEN}✓{RESET} Keep-alive interval set to {new_interval}ms")
            else:
                print(f"\n  {RED}✗{RESET} Interval must be between 50 and 5000")
            time.sleep(1)
            
        elif choice == '2':
            print(f"\n{YELLOW}━━━ Congestion Control Algorithm ━━━{RESET}\n")
            print(f"  {YELLOW}[1]{RESET} BBR (recommended)")
            print(f"  {YELLOW}[2]{RESET} Cubic")
            cc_choice = input(f"\n  {MAGENTA}▸{RESET} Select: ").strip()
            if cc_choice == '1':
                config["congestion_control"] = "bbr"
            elif cc_choice == '2':
                config["congestion_control"] = "cubic"
            save_config(config)
            print(f"\n  {GREEN}✓{RESET} Congestion control set to {config['congestion_control'].upper()}")
            time.sleep(1)
        
        elif choice == '3':
            config["enable_gso"] = not config.get("enable_gso", False)
            save_config(config)
            status = "enabled" if config["enable_gso"] else "disabled"
            print(f"\n  {GREEN}✓{RESET} GSO {status}")
            time.sleep(1)
        
        elif choice == '4':
            config["enable_fragmentation"] = not config.get("enable_fragmentation", False)
            save_config(config)
            status = "enabled" if config["enable_fragmentation"] else "disabled"
            print(f"\n  {GREEN}✓{RESET} TLS Fragmentation {status}")
            time.sleep(1)
        
        elif choice == '5':
            new_size = get_int_input("Fragment Size (bytes)", config.get("fragment_size", 77))
            if 10 <= new_size <= 500:
                config["fragment_size"] = new_size
                save_config(config)
                print(f"\n  {GREEN}✓{RESET} Fragment size set to {new_size} bytes")
            else:
                print(f"\n  {RED}✗{RESET} Size must be between 10 and 500")
            time.sleep(1)
        
        elif choice == '6':
            new_delay = get_int_input("Fragment Delay (ms)", config.get("fragment_delay", 200))
            if 10 <= new_delay <= 1000:
                config["fragment_delay"] = new_delay
                save_config(config)
                print(f"\n  {GREEN}✓{RESET} Fragment delay set to {new_delay}ms")
            else:
                print(f"\n  {RED}✗{RESET} Delay must be between 10 and 1000")
            time.sleep(1)
        
        elif choice == '7':
            new_restart = get_int_input("Auto Restart (minutes, 0=off)", config.get("auto_restart_minutes", 0))
            if 0 <= new_restart <= 60:
                config["auto_restart_minutes"] = new_restart
                save_config(config)
                if new_restart > 0:
                    print(f"\n  {GREEN}✓{RESET} Auto restart set to every {new_restart} minutes")
                else:
                    print(f"\n  {GREEN}✓{RESET} Auto restart disabled")
            else:
                print(f"\n  {RED}✗{RESET} Must be between 0 and 60")
            time.sleep(1)
            
        elif choice == '8':
            break


def handle_settings():
    while True:
        clear_screen()
        print_logo(mini=True)
        
        if is_windows():
            autostart_status = f"{GREEN}ON{RESET}" if is_autostart_enabled() else f"{RED}OFF{RESET}"
            content = [
                f"{YELLOW}[1]{RESET} Edit Configuration",
                f"{YELLOW}[2]{RESET} Advanced Settings",
                f"{YELLOW}[3]{RESET} Auto-start: {autostart_status}",
                f"{YELLOW}[4]{RESET} Back"
            ]
        else:
            content = [
                f"{YELLOW}[1]{RESET} Edit Configuration",
                f"{YELLOW}[2]{RESET} Advanced Settings",
                f"{YELLOW}[3]{RESET} Back"
            ]
        print_box("Settings", content, BLUE)
        
        choice = input(f"\n  {MAGENTA}▸{RESET} Select option: ").strip()
        
        if choice == '1':
            if is_profile_locked():
                print(f"\n  {RED}✗{RESET} Cannot edit a locked profile")
                time.sleep(2)
                continue
            config = prompt_for_config()
            save_config(config)
            print(f"\n  {GREEN}✓{RESET} Saved!")
            time.sleep(1)
        elif choice == '2':
            if is_profile_locked():
                print(f"\n  {RED}✗{RESET} Cannot edit a locked profile")
                time.sleep(2)
                continue
            handle_advanced_settings()
        elif choice == '3':
            if is_windows():
                if is_autostart_enabled():
                    disable_autostart()
                else:
                    enable_autostart()
            else:
                break
        elif choice == '4' and is_windows():
            break


def handle_menu():
    while True:
        clear_screen()
        print_logo()
        
        config = load_config()
        print_config(config)
        
        content = [
            f"{YELLOW}[1]{RESET} Connect",
            f"{YELLOW}[2]{RESET} Profiles",
            f"{YELLOW}[3]{RESET} Settings",
            f"{YELLOW}[4]{RESET} Tools",
            f"{YELLOW}[5]{RESET} Exit",
        ]
        print_box("Menu", content, BLUE)
        
        choice = input(f"\n  {MAGENTA}▸{RESET} Select option [1-5]: ").strip()
        
        if choice == '1':
            vpn_status = f"{GREEN}●{RESET}" if is_admin() else f"{RED}○{RESET}"
            admin_note = "" if is_admin() else f" {DIM}(requires Admin/sudo){RESET}"
            
            if is_windows():
                content = [
                    f"{YELLOW}[1]{RESET} {vpn_status} VPN Mode       {DIM}(system-wide){RESET}{admin_note}",
                    f"{YELLOW}[2]{RESET} {GREEN}●{RESET} System Proxy   {DIM}(HTTP Global){RESET}",
                    f"{YELLOW}[3]{RESET} {GREEN}●{RESET} Local Proxy    {DIM}(SOCKS5 Only){RESET}",
                    f"{YELLOW}[4]{RESET} Back",
                ]
            else:
                content = [
                    f"{YELLOW}[1]{RESET} {vpn_status} VPN Mode       {DIM}(system-wide){RESET}{admin_note}",
                    f"{YELLOW}[2]{RESET} {GREEN}●{RESET} Local Proxy    {DIM}(SOCKS5 Only){RESET}",
                    f"{YELLOW}[3]{RESET} Back",
                ]
            print_box("Connection Mode", content, MAGENTA)
            
            max_opt = "4" if is_windows() else "3"
            mode = input(f"\n  {MAGENTA}▸{RESET} Select mode [1-{max_opt}]: ").strip()
            
            if mode == '1':
                if not is_admin():
                    if is_linux():
                        import subprocess
                        exe_path = os.path.join(os.path.dirname(sys.executable), 'LocalStream')
                        print(f"\n  {YELLOW}!{RESET} VPN mode requires sudo privileges...")
                        result = subprocess.run(['sudo', exe_path, '--vpn'])
                        sys.exit(result.returncode)
                    else:
                        print(f"\n  {RED}✗{RESET} Requires Administrator!")
                        time.sleep(3)
                        continue
                if not tun2proxy_exists():
                    download_tun2proxy()
                handle_connection(config, "vpn")
                
            elif mode == '2':
                if is_windows():
                    if not privoxy_exists():
                        if not download_privoxy():
                            print(f"\n{RED}✗{RESET} Privoxy download failed.")
                            input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
                            continue
                    handle_connection(config, "system")
                else:
                    if not client_exists():
                        if not download_client():
                            print(f"\n{RED}✗{RESET} Client download failed.")
                            input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
                            continue
                    handle_connection(config, "proxy")
                
            elif mode == '3':
                if is_windows():
                    if not client_exists():
                        if not download_client():
                            print(f"\n{RED}✗{RESET} Client download failed.")
                            input(f"\n  {DIM}Press Enter to return to menu...{RESET}")
                            continue
                    handle_connection(config, "proxy")
                
        elif choice == '2':
            handle_profiles()
            
        elif choice == '3':
            handle_settings()
            
        elif choice == '4':
            handle_tools()
            
        elif choice == '5':
            sys.exit(0)


def handle_first_run():
    clear_screen()
    print_logo()
    
    print(f"\n{GREEN}✓{RESET} Welcome to LocalStream!")
    print(f"{DIM}  First-time setup{RESET}")
    
    content = [
        f"{YELLOW}[1]{RESET} Manual Setup",
        f"{YELLOW}[2]{RESET} Import Config (.local)",
    ]
    print_box("Setup Options", content, MAGENTA)
    
    choice = input(f"\n  {MAGENTA}▸{RESET} Select option [1-2]: ").strip()
    
    if choice == '2':
        handle_import_config()
        if config_exists():
            handle_menu()
            return
        print(f"\n  {YELLOW}!{RESET} No profile configured, starting manual setup...")
        time.sleep(1)
    
    if not client_exists():
        download_client()
        
    config = prompt_for_config()
    save_config(config)
    handle_menu()


def main():
    parser = argparse.ArgumentParser(description="LocalStream CLI Client")
    parser.add_argument("--vpn", action="store_true", help="Connect in VPN mode")
    parser.add_argument("--system-proxy", action="store_true", help="Connect in System Proxy mode")
    parser.add_argument("--proxy", action="store_true", help="Connect in Local Proxy mode")
    parser.add_argument("--profile", help="Use specific profile")
    
    args = parser.parse_args()
    
    try:
        if not config_exists():
            handle_first_run()
            return

        if args.profile:
            if not switch_profile(args.profile):
                print(f"{RED}✗{RESET} Profile '{args.profile}' not found")
                sys.exit(1)
        
        config = load_config()
        
        if args.vpn:
            if not is_admin():
                if is_linux():
                    import subprocess
                    exe_path = os.path.join(os.path.dirname(sys.executable), 'LocalStream')
                    print(f"{YELLOW}!{RESET} VPN mode requires sudo privileges...")
                    result = subprocess.run(['sudo', exe_path, '--vpn'])
                    sys.exit(result.returncode)
                else:
                    print(f"{RED}✗{RESET} VPN mode requires Administrator privileges")
                    sys.exit(1)
            if not tun2proxy_exists():
                download_tun2proxy()
            handle_connection(config, "vpn")
            
        elif args.system_proxy:
            if not privoxy_exists():
                download_privoxy()
            handle_connection(config, "system")
            
        elif args.proxy:
            if not client_exists():
                download_client()
            handle_connection(config, "proxy")
            
        else:
            handle_menu()
            
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}✓{RESET} Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
