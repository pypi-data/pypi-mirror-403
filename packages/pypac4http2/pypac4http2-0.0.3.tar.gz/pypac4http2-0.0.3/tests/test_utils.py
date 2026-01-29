import httplib2
import socks
from pypac4http2.utils import pac_result_to_proxy_info, get_proxy_info_dict


def test_pac_result_to_proxy_info_various():
    # Test DIRECT
    assert pac_result_to_proxy_info("DIRECT") is None
    assert pac_result_to_proxy_info("") is None

    # Test PROXY with default port
    info = pac_result_to_proxy_info("PROXY myproxy")
    assert info.proxy_host == "myproxy"
    assert info.proxy_port == 80
    assert info.proxy_type == socks.PROXY_TYPE_HTTP

    # Test SOCKS (defaults to SOCKS5)
    info = pac_result_to_proxy_info("SOCKS myproxy:1080")
    assert info.proxy_type == socks.PROXY_TYPE_SOCKS5

    # Test SOCKS4
    info = pac_result_to_proxy_info("SOCKS4 myproxy:1080")
    assert info.proxy_type == socks.PROXY_TYPE_SOCKS4

    # Test SOCKS5
    info = pac_result_to_proxy_info("SOCKS5 myproxy:1080")
    assert info.proxy_type == socks.PROXY_TYPE_SOCKS5

    # Test invalid format (less than 2 parts)
    assert pac_result_to_proxy_info("INVALID") is None


def test_get_proxy_info_dict_none():
    data = get_proxy_info_dict(None)
    assert data == {"proxy_type": None, "proxy_host": None, "proxy_port": None}


def test_get_proxy_info_dict_socks4():
    info = httplib2.ProxyInfo(socks.PROXY_TYPE_SOCKS4, "host", 1080)
    data = get_proxy_info_dict(info)
    assert data["proxy_type"] == "SOCKS4"


def test_get_proxy_info_dict_unknown():
    # Force an unknown type (999)
    info = httplib2.ProxyInfo(999, "host", 1080)
    data = get_proxy_info_dict(info)
    assert data["proxy_type"] == "999"
