import subprocess
import signal
import sys
import os
import threading
import re
import time
from pathlib import Path

from localstream.Downloader import get_client_path, get_tun2proxy_path, client_exists, tun2proxy_exists, download_client, download_tun2proxy, privoxy_exists, download_privoxy, is_windows, is_linux
from localstream.SystemProxy import set_system_proxy, unset_system_proxy
from localstream.PrivoxyManager import start_privoxy, stop_privoxy
from localstream.Fragmenter import TlsFragmenter


CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


LOG_PATTERNS = {
    r"INFO.*Listening on TCP port (\d+)": lambda m: f"{GREEN}●{RESET} Listening on port {WHITE}{m.group(1)}{RESET}",
    r"INFO.*Connection ready": lambda m: f"{GREEN}●{RESET} {GREEN}Connection ready!{RESET}",
    r"INFO.*accepted new client": lambda m: f"{BLUE}→{RESET} New client connected",
    r"INFO.*client disconnected": lambda m: f"{BLUE}←{RESET} Client disconnected",
    r"WARN.*certificate pinning": lambda m: f"{YELLOW}!{RESET} {DIM}Certificate pinning disabled{RESET}",
    r"ERROR|FATAL": lambda m: f"{RED}✗{RESET} {m.group(0)}",
    r"INFO.*bytes.*transferred": lambda m: f"{DIM}↔{RESET} {DIM}Data transferred{RESET}",
    r"actively refused": lambda m: None,
}


def format_log_line(line: str) -> str:
    line = line.strip()
    if not line:
        return None
    
    if any(x in line for x in ["actively refused", "HostUnreachable", "connection failed", "tun2proxy"]):
        return None
    
    for pattern, formatter in LOG_PATTERNS.items():
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return formatter(match)
    
    if "INFO" in line or "DEBUG" in line:
        return None
    
    return f"{DIM}│{RESET} {line}"


def is_admin() -> bool:
    if is_windows():
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0


def run_as_admin():
    if is_windows():
        try:
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
        except:
            return False
    else:
        print(f"{YELLOW}!{RESET} Please run with sudo for VPN mode")
        return False


class ConnectionManager:
    def __init__(self):
        self.slipstream_process = None
        self.tun2proxy_process = None
        self.privoxy_process = None
        self.fragmenter = None
        self.restart_requested = False
        self.user_disconnected = False
        self.stop_listener = False
        self._original_sigint = None
        self._listener_thread = None
        self._monitor_thread = None
        self._auto_restart_thread = None
        self.start_time = None
        self.auto_restart_seconds = 0
    
    def _setup_signal_handlers(self):
        self._original_sigint = signal.signal(signal.SIGINT, self._sigint_handler)
    
    def _restore_signal_handlers(self):
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
    
    def _sigint_handler(self, signum, frame):
        print(f"\n\n{YELLOW}⟳{RESET} Disconnecting...")
        self.user_disconnected = True
        self.disconnect()
    
    def _keyboard_listener(self):
        if is_windows():
            try:
                import msvcrt
                while not self.stop_listener:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x04':
                            self.restart_requested = True
                            self.disconnect()
                            return
                    threading.Event().wait(0.1)
            except:
                pass
        else:
            try:
                import sys
                import select
                import tty
                import termios
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    while not self.stop_listener:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1)
                            if key == '\x04':
                                self.restart_requested = True
                                self.disconnect()
                                return
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except:
                pass
    
    def _start_keyboard_listener(self):
        self.stop_listener = False
        self._listener_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        self._listener_thread.start()
    
    def _stop_keyboard_listener(self):
        self.stop_listener = True
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=0.5)
    
    def _auto_restart_timer(self):
        start = time.time()
        while not self.user_disconnected and not self.restart_requested:
            elapsed = time.time() - start
            if elapsed >= self.auto_restart_seconds:
                print(f"\n  {YELLOW}⟳{RESET} Auto-restart triggered after {int(self.auto_restart_seconds // 60)} minutes")
                self.restart_requested = True
                return
            time.sleep(1)
    
    def _start_auto_restart_timer(self, minutes: int):
        if minutes > 0:
            self.auto_restart_seconds = minutes * 60
            self._auto_restart_thread = threading.Thread(target=self._auto_restart_timer, daemon=True)
            self._auto_restart_thread.start()
    
    def _stop_auto_restart_timer(self):
        if self._auto_restart_thread and self._auto_restart_thread.is_alive():
            self._auto_restart_thread.join(timeout=0.5)
        self._auto_restart_thread = None
    
    def get_uptime(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            return f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
        return "00:00"

    def connect_proxy(self, config: dict) -> str:
        if not client_exists():
            if not download_client():
                print(f"{RED}✗{RESET} Cannot connect: slipstream-client not available")
                return "error"
        
        client_path = get_client_path()
        server_ip = config.get("server_ip", "")
        server_port = config.get("server_port", 53)
        local_port = config.get("local_port", 5201)
        domain = config.get("domain", "")
        keep_alive = config.get("keep_alive_interval", 200)
        congestion = config.get("congestion_control", "bbr")
        enable_gso = config.get("enable_gso", False)
        enable_frag = config.get("enable_fragmentation", False)
        frag_size = config.get("fragment_size", 77)
        frag_delay = config.get("fragment_delay", 200)
        
        if not server_ip or not domain:
            print(f"{RED}✗{RESET} Invalid configuration: server_ip and domain are required")
            return "error"
        
        resolver = f"{server_ip}:{server_port}"
        
        exposed_port = local_port
        if enable_frag:
            fragmenter_port = 5202
            self.fragmenter = TlsFragmenter(
                listen_port=fragmenter_port,
                upstream_port=local_port,
                fragment_size=frag_size,
                fragment_delay=frag_delay
            )
            if self.fragmenter.start():
                print(f"  {GREEN}✓{RESET} TLS Fragmenter started (size={frag_size}, delay={frag_delay}ms)")
                exposed_port = fragmenter_port
            else:
                print(f"  {YELLOW}!{RESET} Fragmenter failed, using direct connection")
                self.fragmenter = None
        
        cmd = [
            str(client_path),
            "--resolver", resolver,
            "--domain", domain,
            "--tcp-listen-port", str(local_port),
            "--keep-alive-interval", str(keep_alive),
            "--congestion-control", congestion,
            "--gso", str(enable_gso).lower()
        ]
        
        auto_restart_minutes = config.get("auto_restart_minutes", 0)
        
        self._setup_signal_handlers()
        self.restart_requested = False
        self.user_disconnected = False
        reconnect_count = 0
        self.start_time = time.time()
        
        try:
            while True:
                self.slipstream_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                self._start_keyboard_listener()
                self._start_auto_restart_timer(auto_restart_minutes)
                
                if reconnect_count == 0:
                    print(f"\n{CYAN}┌{'─' * 50}┐{RESET}")
                    print(f"{CYAN}│{RESET}  {GREEN}●{RESET} {BOLD}PROXY Mode - Connection Status{RESET}{' ' * 16}{CYAN}│{RESET}")
                    print(f"{CYAN}└{'─' * 50}┘{RESET}\n")
                else:
                    print(f"\n  {GREEN}●{RESET} Reconnected! (attempt #{reconnect_count + 1})\n")
                
                if self.slipstream_process and self.slipstream_process.stdout:
                    for line in self.slipstream_process.stdout:
                        if self.restart_requested or self.user_disconnected:
                            break
                        formatted = format_log_line(line)
                        if formatted:
                            print(f"  {formatted}")
                
                if self.slipstream_process:
                    self.slipstream_process.wait()
                self._stop_keyboard_listener()
                
                if self.restart_requested:
                    return "restart"
                
                if self.user_disconnected:
                    return "done"
                
                return_code = self.slipstream_process.returncode
                if return_code != 0:
                    reconnect_count += 1
                    print(f"\n  {YELLOW}!{RESET} Connection dropped (code: {return_code})")
                    print(f"  {YELLOW}⟳{RESET} Auto-reconnecting in 3 seconds...")
                    time.sleep(3)
                    continue
                
                return "done"
            
        except KeyboardInterrupt:
            self._stop_keyboard_listener()
            return "done"
        except FileNotFoundError:
            print(f"{RED}✗{RESET} Client not found: {client_path}")
            return "error"
        except Exception as e:
            print(f"{RED}✗{RESET} Connection error: {e}")
            return "error"
        finally:
            self._restore_signal_handlers()
            self._stop_keyboard_listener()
            self.disconnect()
    
    def _monitor_slipstream(self, cmd):
        reconnect_count = 0
        while not self.user_disconnected and not self.restart_requested:
            if self.slipstream_process and self.slipstream_process.poll() is not None:
                return_code = self.slipstream_process.returncode
                if return_code != 0 and not self.user_disconnected:
                    reconnect_count += 1
                    print(f"\n  {YELLOW}!{RESET} Slipstream dropped (code: {return_code})")
                    print(f"  {YELLOW}⟳{RESET} Auto-reconnecting...")
                    time.sleep(2)
                    
                    try:
                        self.slipstream_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                        )
                        time.sleep(2)
                        if self.slipstream_process.poll() is None:
                            print(f"  {GREEN}●{RESET} Slipstream reconnected! (attempt #{reconnect_count + 1})")
                    except:
                        pass
            time.sleep(1)
    
    def connect_vpn(self, config: dict) -> str:
        if not is_admin():
            print(f"\n{RED}✗{RESET} VPN Mode requires Administrator privileges!")
            print(f"{YELLOW}!{RESET} Please run LocalStream as Administrator")
            return "error"
        
        if not client_exists():
            if not download_client():
                print(f"{RED}✗{RESET} Cannot connect: slipstream-client not available")
                return "error"
        
        if not tun2proxy_exists():
            if not download_tun2proxy():
                print(f"{RED}✗{RESET} Cannot connect: tun2proxy not available")
                return "error"
        
        client_path = get_client_path()
        tun2proxy_path = get_tun2proxy_path()
        server_ip = config.get("server_ip", "")
        server_port = config.get("server_port", 53)
        local_port = config.get("local_port", 5201)
        domain = config.get("domain", "")
        keep_alive = config.get("keep_alive_interval", 200)
        congestion = config.get("congestion_control", "bbr")
        enable_gso = config.get("enable_gso", False)
        enable_frag = config.get("enable_fragmentation", False)
        frag_size = config.get("fragment_size", 77)
        frag_delay = config.get("fragment_delay", 200)
        
        if not server_ip or not domain:
            print(f"{RED}✗{RESET} Invalid configuration: server_ip and domain are required")
            return "error"
        
        resolver = f"{server_ip}:{server_port}"
        
        proxy_port = local_port
        if enable_frag:
            fragmenter_port = 5202
            self.fragmenter = TlsFragmenter(
                listen_port=fragmenter_port,
                upstream_port=local_port,
                fragment_size=frag_size,
                fragment_delay=frag_delay
            )
            if self.fragmenter.start():
                print(f"  {GREEN}✓{RESET} TLS Fragmenter started (size={frag_size}, delay={frag_delay}ms)")
                proxy_port = fragmenter_port
            else:
                print(f"  {YELLOW}!{RESET} Fragmenter failed, using direct connection")
                self.fragmenter = None
        
        slipstream_cmd = [
            str(client_path),
            "--resolver", resolver,
            "--domain", domain,
            "--tcp-listen-port", str(local_port),
            "--keep-alive-interval", str(keep_alive),
            "--congestion-control", congestion,
            "--gso", str(enable_gso).lower()
        ]
        
        tun2proxy_cmd = [
            str(tun2proxy_path),
            "--setup",
            "--proxy", f"socks5://127.0.0.1:{proxy_port}",
            "--bypass", server_ip,
            "--dns", "virtual"
        ]
        
        self._setup_signal_handlers()
        self.restart_requested = False
        self.user_disconnected = False
        self.start_time = time.time()
        
        try:
            print(f"\n{CYAN}┌{'─' * 50}┐{RESET}")
            print(f"{CYAN}│{RESET}  {GREEN}●{RESET} {BOLD}VPN Mode - Starting Tunnel{RESET}{' ' * 21}{CYAN}│{RESET}")
            print(f"{CYAN}└{'─' * 50}┘{RESET}\n")
            
            print(f"  {YELLOW}⟳{RESET} Starting slipstream-client...")
            self.slipstream_process = subprocess.Popen(
                slipstream_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            time.sleep(2)
            
            if self.slipstream_process and self.slipstream_process.poll() is not None:
                print(f"  {RED}✗{RESET} Slipstream failed to start")
                return "error"
            
            print(f"  {GREEN}✓{RESET} Slipstream-client running on port {local_port}")
            
            print(f"  {YELLOW}⟳{RESET} Starting tun2proxy (VPN tunnel)...")
            self.tun2proxy_process = subprocess.Popen(
                tun2proxy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            time.sleep(2)
            
            if self.tun2proxy_process and self.tun2proxy_process.poll() is not None:
                print(f"  {RED}✗{RESET} tun2proxy failed to start")
                self.disconnect()
                return "error"
            
            print(f"  {GREEN}✓{RESET} VPN tunnel established!")
            print(f"\n{GREEN}{'═' * 52}{RESET}")
            print(f"{GREEN}  ✓ All traffic is now routed through the VPN!{RESET}")
            print(f"{GREEN}{'═' * 52}{RESET}")
            print(f"\n  {DIM}Press Ctrl+C to disconnect{RESET}\n")
            
            self._monitor_thread = threading.Thread(
                target=self._monitor_slipstream, 
                args=(slipstream_cmd,), 
                daemon=True
            )
            self._monitor_thread.start()
            
            auto_restart_minutes = config.get("auto_restart_minutes", 0)
            self._start_keyboard_listener()
            self._start_auto_restart_timer(auto_restart_minutes)
            
            ignore_patterns = [
                "brokenpipe",
                "tcp connection closed",
                "connection closed",
                "connectionnotallowed",
                "ending #",
                "info  tun2proxy",
                "actively refused",
                "os error 10061"
            ]
            
            if self.tun2proxy_process and self.tun2proxy_process.stdout:
                for line in self.tun2proxy_process.stdout:
                    if self.restart_requested:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    
                    line_lower = line.lower()
                    if any(pattern in line_lower for pattern in ignore_patterns):
                        continue
                    
                    if "error" in line_lower or "fatal" in line_lower:
                        print(f"  {RED}✗{RESET} {line}")
            
            if self.tun2proxy_process:
                self.tun2proxy_process.wait()
            self._stop_keyboard_listener()
            
            if self.restart_requested:
                return "restart"
            
            return "done"
            
        except KeyboardInterrupt:
            self._stop_keyboard_listener()
            return "done"
        except FileNotFoundError as e:
            print(f"{RED}✗{RESET} Binary not found: {e}")
            return "error"
        except Exception as e:
            print(f"{RED}✗{RESET} Connection error: {e}")
            return "error"
        finally:
            self._restore_signal_handlers()
            self._stop_keyboard_listener()
            self.disconnect()

    def connect_system_proxy(self, config: dict) -> str:
        if not client_exists():
            if not download_client():
                print(f"{RED}✗{RESET} Cannot connect: client not available")
                return "error"
                
        if not privoxy_exists():
            if not download_privoxy():
                print(f"{RED}✗{RESET} Cannot connect: Privoxy not available")
                return "error"
        
        client_path = get_client_path()
        server_ip = config.get("server_ip", "")
        server_port = config.get("server_port", 53)
        local_port = config.get("local_port", 5201)
        privoxy_port = 8118
        domain = config.get("domain", "")
        keep_alive = config.get("keep_alive_interval", 200)
        congestion = config.get("congestion_control", "bbr")
        enable_gso = config.get("enable_gso", False)
        enable_frag = config.get("enable_fragmentation", False)
        frag_size = config.get("fragment_size", 77)
        frag_delay = config.get("fragment_delay", 200)
        
        if not server_ip or not domain:
            print(f"{RED}✗{RESET} Invalid config")
            return "error"
        
        resolver = f"{server_ip}:{server_port}"
        
        proxy_port = local_port
        if enable_frag:
            fragmenter_port = 5202
            self.fragmenter = TlsFragmenter(
                listen_port=fragmenter_port,
                upstream_port=local_port,
                fragment_size=frag_size,
                fragment_delay=frag_delay
            )
            if self.fragmenter.start():
                print(f"  {GREEN}✓{RESET} TLS Fragmenter started (size={frag_size}, delay={frag_delay}ms)")
                proxy_port = fragmenter_port
            else:
                print(f"  {YELLOW}!{RESET} Fragmenter failed, using direct connection")
                self.fragmenter = None
        
        slipstream_cmd = [
            str(client_path),
            "--resolver", resolver,
            "--domain", domain,
            "--tcp-listen-port", str(local_port),
            "--keep-alive-interval", str(keep_alive),
            "--congestion-control", congestion,
            "--gso", str(enable_gso).lower()
        ]
        
        self._setup_signal_handlers()
        self.restart_requested = False
        self.user_disconnected = False
        self.start_time = time.time()
        
        try:
            print(f"\n{CYAN}┌{'─' * 50}┐{RESET}")
            print(f"{CYAN}│{RESET}  {GREEN}●{RESET} {BOLD}System Proxy Mode{RESET}{' ' * 30}{CYAN}│{RESET}")
            print(f"{CYAN}└{'─' * 50}┘{RESET}\n")
            
            print(f"  {YELLOW}⟳{RESET} Starting slipstream-client...")
            self.slipstream_process = subprocess.Popen(
                slipstream_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            time.sleep(2)
            
            if self.slipstream_process and self.slipstream_process.poll() is not None:
                print(f"  {RED}✗{RESET} Slipstream failed")
                return "error"
                
            print(f"  {GREEN}✓{RESET} Connection established")
            
            print(f"  {YELLOW}⟳{RESET} Starting Privoxy...")
            self.privoxy_process = start_privoxy(proxy_port, privoxy_port)
            time.sleep(2)
            
            if self.privoxy_process and self.privoxy_process.poll() is not None:
                print(f"  {RED}✗{RESET} Privoxy failed")
                self.disconnect()
                return "error"
                
            print(f"  {GREEN}✓{RESET} Proxy server ready")
            
            print(f"  {YELLOW}⟳{RESET} Setting system proxy...")
            set_system_proxy("127.0.0.1", privoxy_port, "<local>")
            
            print(f"\n{GREEN}{'═' * 52}{RESET}")
            print(f"{GREEN}  ✓ System Proxy Enabled: 127.0.0.1:{privoxy_port}{RESET}")
            print(f"{GREEN}{'═' * 52}{RESET}")
            print(f"\n  {DIM}Press Ctrl+C to disconnect{RESET}\n")
            
            self._monitor_thread = threading.Thread(
                target=self._monitor_slipstream, 
                args=(slipstream_cmd,), 
                daemon=True
            )
            self._monitor_thread.start()
            auto_restart_minutes = config.get("auto_restart_minutes", 0)
            self._start_keyboard_listener()
            self._start_auto_restart_timer(auto_restart_minutes)
            
            while not self.user_disconnected and not self.restart_requested:
                time.sleep(1)
                
            if self.restart_requested:
                return "restart"
            return "done"
            
        except KeyboardInterrupt:
            return "done"
        except Exception as e:
            print(f"{RED}✗{RESET} Error: {e}")
            return "error"
        finally:
            self._restore_signal_handlers()
            self._stop_keyboard_listener()
            self.disconnect()

    def disconnect(self):
        self.user_disconnected = True
        
        unset_system_proxy()
        
        if self.fragmenter:
            self.fragmenter.stop()
            self.fragmenter = None
        
        if self.privoxy_process:
            stop_privoxy(self.privoxy_process)
            print(f"{GREEN}✓{RESET} Privoxy stopped")
        self.privoxy_process = None
        
        if self.tun2proxy_process and self.tun2proxy_process.poll() is None:
            self.tun2proxy_process.terminate()
            try:
                self.tun2proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tun2proxy_process.kill()
            print(f"{GREEN}✓{RESET} VPN tunnel closed")
        self.tun2proxy_process = None
        
        if self.slipstream_process and self.slipstream_process.poll() is None:
            self.slipstream_process.terminate()
            try:
                self.slipstream_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.slipstream_process.kill()
            print(f"{GREEN}✓{RESET} Slipstream disconnected")
        self.slipstream_process = None
