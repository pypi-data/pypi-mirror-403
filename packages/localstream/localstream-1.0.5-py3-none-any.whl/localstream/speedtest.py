import time
import requests
import sys

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

TEST_URL = "http://speedtest.tele2.net/10MB.zip"

def run_speedtest(proxy_port):
    proxies = {
        "http": f"socks5://127.0.0.1:{proxy_port}",
        "https": f"socks5://127.0.0.1:{proxy_port}"
    }
    
    print(f"\n{CYAN}╔═══════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║{RESET}  {YELLOW}⟳{RESET} Running Speed Test...                               {CYAN}║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════╝{RESET}\n")
    
    try:
        start_time = time.time()
        requests.head(TEST_URL, proxies=proxies, timeout=5)
        latency = (time.time() - start_time) * 1000
        print(f"  {GREEN}●{RESET} Latency: {latency:.1f} ms")
        
        start_time = time.time()
        response = requests.get(TEST_URL, proxies=proxies, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                bar_length = 40
                filled = int(bar_length * downloaded / total_size)
                bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (bar_length - filled)}{RESET}"
                
                elapsed = time.time() - start_time
                if elapsed > 0:
                    speed_mbps = (downloaded * 8) / (elapsed * 1024 * 1024)
                    print(f"\r  {bar} {speed_mbps:6.2f} Mbps", end="", flush=True)
        
        duration = time.time() - start_time
        speed_mbps = (downloaded * 8) / (duration * 1024 * 1024)
        print(f"\n\n  {GREEN}✓{RESET} Speed: {speed_mbps:.2f} Mbps")
        return True, speed_mbps, latency
        
    except Exception as e:
        print(f"\n\n  {RED}✗{RESET} Speed test failed: {e}")
        return False, 0.0, 0.0
