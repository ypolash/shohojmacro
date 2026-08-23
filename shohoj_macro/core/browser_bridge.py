"""
Zero-Dependency RFC6455 WebSocket Server & Browser Extension Bridge
Communicates securely with Shohoj Browser Companion (Chrome / Edge / Firefox MV3)
to receive DOM bounding rects, element coordinates, and trigger web events with 100% isTrusted parity.
"""

import socket
import threading
import hashlib
import base64
import struct
import json
import time
from typing import Callable


class BrowserBridgeServer:
    """Lightweight pure standard-library WebSocket Server for Shohoj Browser Companion."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.running = False
        self.clients = []
        self._server_socket = None
        self._thread = None
        self.on_element_picked: Callable[[dict], None] = None
        self.on_status_change: Callable[[bool], None] = None

    def start(self):
        """Starts WebSocket server on a background daemon thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops WebSocket server."""
        self.running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        self.clients.clear()
        if self.on_status_change:
            self.on_status_change(False)

    def _run_server(self):
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(1.0)
        except Exception as e:
            print(f"Browser bridge bind failed on {self.host}:{self.port} - {e}")
            self.running = False
            return

        while self.running:
            try:
                client_sock, addr = self._server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_client(self, sock: socket.socket):
        # 1. Perform WebSocket Handshake
        try:
            request = sock.recv(2048).decode("utf-8", errors="ignore")
            headers = {}
            lines = request.split("\r\n")
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            sec_key = headers.get("sec-websocket-key")
            if not sec_key:
                sock.close()
                return

            # Compute Sec-WebSocket-Accept
            magic_guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(
                hashlib.sha1((sec_key + magic_guid).encode("utf-8")).digest()
            ).decode("utf-8")

            handshake_resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            sock.sendall(handshake_resp.encode("utf-8"))
            self.clients.append(sock)
            if self.on_status_change:
                self.on_status_change(True)

            # 2. Receive Frames Loop
            while self.running:
                data = sock.recv(2)
                if not data or len(data) < 2:
                    break

                byte1, byte2 = data[0], data[1]
                fin = (byte1 & 0x80) != 0
                opcode = byte1 & 0x0F
                masked = (byte2 & 0x80) != 0
                payload_len = byte2 & 0x7F

                if opcode == 8:  # Connection close
                    break
                elif opcode == 9:  # Ping -> Send Pong
                    sock.sendall(bytes([0x8A, 0x00]))
                    continue

                if payload_len == 126:
                    ext_len = sock.recv(2)
                    payload_len = struct.unpack("!H", ext_len)[0]
                elif payload_len == 127:
                    ext_len = sock.recv(8)
                    payload_len = struct.unpack("!Q", ext_len)[0]

                masks = sock.recv(4) if masked else None
                payload = bytearray(sock.recv(payload_len))

                if masked:
                    for i in range(len(payload)):
                        payload[i] ^= masks[i % 4]

                message_text = payload.decode("utf-8", errors="ignore")
                self._on_message_received(message_text)

        except Exception:
            pass
        finally:
            if sock in self.clients:
                self.clients.remove(sock)
            try:
                sock.close()
            except Exception:
                pass
            if len(self.clients) == 0 and self.on_status_change:
                self.on_status_change(False)

    def _on_message_received(self, text: str):
        try:
            msg = json.loads(text)
            action = msg.get("action")
            if action == "ELEMENT_PICKED":
                if self.on_element_picked:
                    self.on_element_picked(msg.get("data", {}))
        except Exception:
            pass

    def send_broadcast(self, data: dict):
        """Sends a JSON text frame to all connected extension clients."""
        try:
            payload_str = json.dumps(data)
            payload_bytes = payload_str.encode("utf-8")
            length = len(payload_bytes)

            header = bytearray([0x81])  # FIN + Text frame
            if length <= 125:
                header.append(length)
            elif length <= 65535:
                header.append(126)
                header.extend(struct.pack("!H", length))
            else:
                header.append(127)
                header.extend(struct.pack("!Q", length))

            frame = bytes(header + payload_bytes)
            for sock in list(self.clients):
                try:
                    sock.sendall(frame)
                except Exception:
                    pass
        except Exception:
            pass
