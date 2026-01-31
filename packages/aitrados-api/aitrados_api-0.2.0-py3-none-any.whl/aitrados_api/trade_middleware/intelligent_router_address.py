import os
import getpass
import socket
from abc import ABC
import platform
import ipaddress
import re
from typing import Dict


class IntelligentRouterAddress(ABC):
    TCP = None
    IPC = None
    INPROC = None
    @classmethod
    def get_array(cls):
        if platform.system() != "Windows":
            return [cls.TCP, cls.IPC, cls.INPROC]
        else:
            return [cls.TCP, cls.INPROC]


class FrontendIntelligentRouterAddress(IntelligentRouterAddress):
    TCP = "tcp://0.0.0.0:51591"
    IPC = f"ipc:///tmp/aitrados_frontend_{getpass.getuser()}.sock"
    INPROC = "inproc://aitrados_frontend"
class BackendIntelligentRouterAddress(IntelligentRouterAddress):
    TCP = "tcp://0.0.0.0:51592"
    IPC = f"ipc:///tmp/aitrados_backend_{getpass.getuser()}.sock"
    INPROC = "inproc://aitrados_backend"

class SubIntelligentRouterAddress(IntelligentRouterAddress):
    TCP = "tcp://0.0.0.0:51593"
    IPC = f"ipc:///tmp/aitrados_sub_{getpass.getuser()}.sock"
    INPROC = "inproc://aitrados_sub"
class PubIntelligentRouterAddress(IntelligentRouterAddress):
    TCP = "tcp://0.0.0.0:51594"
    IPC = f"ipc:///tmp/aitrados_pub_{getpass.getuser()}.sock"
    INPROC = "inproc://aitrados_pub"



def cleanup_sockets():
    from aitrados_api.trade_middleware.client_adresss_detector import CommAddressDetector
    import glob
    user = getpass.getuser()
    pattern = f"/tmp/aitrados_*_{user}.sock"
    for sock_file in glob.glob(pattern):
        try:
            os.unlink(sock_file)
        except OSError:
            pass
    CommAddressDetector.delete_machine_id()



def replace_middleware_tcp_address(host: str, ira:type[IntelligentRouterAddress]):
    return ira.TCP.replace("0.0.0.0",host)

class MiddlewareInternalIP:
    internal_ip_map:Dict[str|bytes,bool]={}
    @classmethod
    def get_internal_ip(cls,addr: bytes | str):
        return cls.internal_ip_map.get(addr,None)
    @classmethod
    def set_internal_ip(cls,addr: bytes | str,is_internal:bool):
        cls.internal_ip_map[addr]=is_internal


def check_middleware_internal_ip(addr: bytes | str) -> bool:
    """
    Check if the address is internal (including inproc, ipc, localhost, and private IP)

    Args:
        addr: ZeroMQ address, format like b"tcp://192.168.1.1:5555" or "ipc:///tmp/socket"

    Returns:
        bool: True if internal address, False if public address
    """
    # Check cache first with original addr
    if (check := MiddlewareInternalIP.get_internal_ip(addr)) is not None:
        return check

    # Convert to string
    if isinstance(addr, bytes):
        addr_str = addr.decode('utf-8', errors='ignore')
    else:
        addr_str = addr

    addr_str = addr_str.lower().strip()

    # 1. Priority check for inproc and ipc (inter-process and local socket)
    if addr_str.startswith('inproc://') or addr_str.startswith('ipc://'):
        MiddlewareInternalIP.set_internal_ip(addr, True)
        return True

    # 2. Extract IP address part (from tcp://IP:PORT)
    # Match format: tcp://IP:PORT
    match = re.search(r'tcp://([^:]+):\d+', addr_str)
    if not match:
        # If unable to parse, conservatively treat as internal
        MiddlewareInternalIP.set_internal_ip(addr, True)
        return True

    ip_or_domain = match.group(1)

    # 3. Check for localhost and 0.0.0.0
    if ip_or_domain in ('localhost', '127.0.0.1', '0.0.0.0', '::1', '::'):
        MiddlewareInternalIP.set_internal_ip(addr, True)
        return True

    # 4. Use ipaddress module to check if it's a private IP
    try:
        ip_obj = ipaddress.ip_address(ip_or_domain)
        # is_private checks the following private ranges:
        # - 10.0.0.0/8
        # - 172.16.0.0/12
        # - 192.168.0.0/16
        # - 127.0.0.0/8 (loopback)
        # - 169.254.0.0/16 (link-local)
        # - fe80::/10 (IPv6 link-local)
        # - fc00::/7 (IPv6 unique local)
        check_ = ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        MiddlewareInternalIP.set_internal_ip(addr, check_)
        return check_
    except ValueError:
        # Cannot parse as valid IP, might be domain
        pass

    # 5. Resolve domain name to IP
    try:
        resolved_ip = socket.gethostbyname(ip_or_domain)
        ip_obj = ipaddress.ip_address(resolved_ip)
        check_ = ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        MiddlewareInternalIP.set_internal_ip(addr, check_)
        return check_
    except (socket.gaierror, ValueError):
        # Cannot resolve domain, conservatively treat as internal
        MiddlewareInternalIP.set_internal_ip(addr, True)
        return True