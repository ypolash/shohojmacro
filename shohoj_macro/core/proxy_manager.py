import os
import random
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ProxyConfig:
    raw_string: str           # Full original string
    country_code: str         # "gb"
    network: str              # "res_mob"
    session_id: str           # "c8jariy45"
    username: str             # "country-gb-network-res_mob-rotate-requests_100-session-c8jariy45"
    password: str             # "O8FsFmZJcy"
    host: str                 # "proxy.soax.com"
    port: int                 # 1337
    proxy_url: str            # "http://username:password@host:port"

class ProxySessionManager:
    """Manages SOAX proxy session files."""
    
    def __init__(self, proxy_dir: str):
        self.proxy_dir = proxy_dir
        self.proxies: List[ProxyConfig] = []
        self.current_file = ""
        
    def load_session_file(self, filename: str) -> int:
        """Loads proxies from a specific file in the proxy directory."""
        filepath = os.path.join(self.proxy_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Proxy file not found: {filepath}")
            
        self.current_file = filename
        self.proxies = []
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            proxy = self.parse_proxy_string(line)
            if proxy:
                self.proxies.append(proxy)
                
        return len(self.proxies)
        
    def get_random_proxy(self) -> Optional[ProxyConfig]:
        """Returns a random proxy from the loaded list."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
        
    def parse_proxy_string(self, raw: str) -> Optional[ProxyConfig]:
        """
        Parses a SOAX format proxy string.
        Format: username:password@host:port
        Where username is like: country-gb-network-res_mob-rotate-requests_100-session-c8jariy45
        """
        # regex to parse format: username:password@host:port
        match = re.match(r'^([^:]+):([^@]+)@([^:]+):(\d+)$', raw)
        if not match:
            # Maybe it doesn't have the @ symbol and is just username:password:host:port
            match_alternate = re.match(r'^([^:]+):([^:]+):([^:]+):(\d+)$', raw)
            if match_alternate:
                username, password, host, port = match_alternate.groups()
            else:
                return None
        else:
            username, password, host, port = match.groups()
            
        # Extract country code and session id from username
        # Expected: country-gb-network-...-session-c8jariy45
        country_code = ""
        country_match = re.search(r'country-([a-zA-Z]+)-', username)
        if country_match:
            country_code = country_match.group(1).lower()
            
        session_id = ""
        session_match = re.search(r'session-([a-zA-Z0-9]+)', username)
        if session_match:
            session_id = session_match.group(1)
            
        network = ""
        network_match = re.search(r'network-([a-zA-Z_]+)-', username)
        if network_match:
            network_match = network_match.group(1)
            
        proxy_url = f"http://{username}:{password}@{host}:{port}"
        
        return ProxyConfig(
            raw_string=raw,
            country_code=country_code,
            network=network,
            session_id=session_id,
            username=username,
            password=password,
            host=host,
            port=int(port),
            proxy_url=proxy_url
        )
