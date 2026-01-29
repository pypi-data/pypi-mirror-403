import httplib2
import socks
from typing import Optional, Dict, Any


def pac_result_to_proxy_info(pac_proxy_str: str) -> Optional[httplib2.ProxyInfo]:
    """
    Convert a PAC proxy result string (e.g., "PROXY host:port" or "SOCKS host:port")
    to an httplib2 ProxyInfo object.

    Returns None if the result is "DIRECT" or empty.
    """
    if not pac_proxy_str or pac_proxy_str.upper() == "DIRECT":
        return None

    # Standard format is "TYPE host:port; TYPE host:port"
    # We take the first one
    first_choice = pac_proxy_str.split(";")[0].strip()
    parts = first_choice.split()

    if len(parts) < 2:
        return None

    proxy_type_str = parts[0].upper()
    host_port = parts[1]

    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 80  # Default for HTTP

    proxy_type = socks.PROXY_TYPE_HTTP
    if proxy_type_str == "SOCKS":
        proxy_type = socks.PROXY_TYPE_SOCKS5
    elif proxy_type_str == "SOCKS4":
        proxy_type = socks.PROXY_TYPE_SOCKS4
    elif proxy_type_str == "SOCKS5":
        proxy_type = socks.PROXY_TYPE_SOCKS5
    elif proxy_type_str == "PROXY":
        proxy_type = socks.PROXY_TYPE_HTTP

    return httplib2.ProxyInfo(proxy_type=proxy_type, proxy_host=host, proxy_port=port)


def get_proxy_info_dict(proxy_info: Optional[httplib2.ProxyInfo]) -> Dict[str, Any]:
    """Convert ProxyInfo object to a dictionary for JSON serialization."""
    if not proxy_info:
        return {"proxy_type": None, "proxy_host": None, "proxy_port": None}

    # Map back the proxy type to string
    type_map = {
        socks.PROXY_TYPE_HTTP: "HTTP",
        socks.PROXY_TYPE_SOCKS4: "SOCKS4",
        socks.PROXY_TYPE_SOCKS5: "SOCKS5",
    }

    return {
        "proxy_type": type_map.get(proxy_info.proxy_type, str(proxy_info.proxy_type)),
        "proxy_host": proxy_info.proxy_host,
        "proxy_port": proxy_info.proxy_port,
    }
