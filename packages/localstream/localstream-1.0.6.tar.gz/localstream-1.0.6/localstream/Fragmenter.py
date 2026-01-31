import socket
import threading
import time
import sys


class TlsFragmenter:
    def __init__(self, 
                 listen_port: int = 5202,
                 upstream_host: str = "127.0.0.1",
                 upstream_port: int = 5201,
                 fragment_size: int = 77,
                 fragment_delay: int = 200):
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.fragment_size = fragment_size
        self.fragment_delay = fragment_delay
        self.running = False
        self.server_socket = None
        self._thread = None
        self._timeout = 60
    
    def _is_tls_client_hello(self, data: bytes) -> bool:
        if len(data) < 6:
            return False
        return data[0] == 0x16 and data[1] == 0x03 and data[5] == 0x01
    
    def _send_fragmented(self, sock: socket.socket, data: bytes):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        for i in range(0, len(data), self.fragment_size):
            chunk = data[i:i + self.fragment_size]
            sock.sendall(chunk)
            if i + self.fragment_size < len(data):
                time.sleep(self.fragment_delay / 1000.0)
    
    def _pipe_data(self, src: socket.socket, dst: socket.socket, name: str):
        try:
            while self.running:
                try:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass
    
    def _handle_client(self, client_sock: socket.socket, client_addr):
        upstream_sock = None
        try:
            client_sock.settimeout(self._timeout)
            
            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream_sock.settimeout(self._timeout)
            upstream_sock.connect((self.upstream_host, self.upstream_port))
            
            time.sleep(0.01)
            data = client_sock.recv(16384)
            
            if not data:
                return
            
            if self._is_tls_client_hello(data):
                self._send_fragmented(upstream_sock, data)
            else:
                upstream_sock.sendall(data)
            
            client_sock.settimeout(1)
            upstream_sock.settimeout(1)
            
            t1 = threading.Thread(
                target=self._pipe_data,
                args=(client_sock, upstream_sock, "client->upstream"),
                daemon=True
            )
            t2 = threading.Thread(
                target=self._pipe_data,
                args=(upstream_sock, client_sock, "upstream->client"),
                daemon=True
            )
            t1.start()
            t2.start()
            
            while self.running and (t1.is_alive() or t2.is_alive()):
                time.sleep(0.5)
                
        except Exception:
            pass
        finally:
            if client_sock:
                try:
                    client_sock.close()
                except:
                    pass
            if upstream_sock:
                try:
                    upstream_sock.close()
                except:
                    pass
    
    def _run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind(("127.0.0.1", self.listen_port))
            self.server_socket.listen(128)
        except OSError:
            self.running = False
            return
        
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    continue
                break
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
    
    def start(self) -> bool:
        if self.running:
            return True
        
        self.running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        time.sleep(0.5)
        return self.running
    
    def stop(self):
        self.running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
    
    def is_running(self) -> bool:
        return self.running and self._thread is not None and self._thread.is_alive()


def create_fragmenter(listen_port: int = 5202,
                      upstream_port: int = 5201,
                      fragment_size: int = 77,
                      fragment_delay: int = 200) -> TlsFragmenter:
    return TlsFragmenter(
        listen_port=listen_port,
        upstream_port=upstream_port,
        fragment_size=fragment_size,
        fragment_delay=fragment_delay
    )
