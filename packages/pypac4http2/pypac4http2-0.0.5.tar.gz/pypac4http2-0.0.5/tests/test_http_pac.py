import httplib2
import socks
from unittest.mock import patch, MagicMock
from pypac4http2.http_pac import HttpPac


def test_http_pac_proxy_resolution(mock_pac_file, mock_httplib2_http):
    http = HttpPac(pac=mock_pac_file)

    # Test proxy resolution for example.com
    http.request("http://test.example.com")

    # Check if proxy_info was set correctly
    assert http.proxy_info is not None
    assert http.proxy_info.proxy_host == "proxy.example.com"
    assert http.proxy_info.proxy_port == 8080
    assert http.proxy_info.proxy_type == socks.PROXY_TYPE_HTTP

    # Verify httplib2.Http.request was called
    mock_httplib2_http.assert_called_once()


def test_http_pac_socks_resolution(mock_pac_file, mock_httplib2_http):
    http = HttpPac(pac=mock_pac_file)

    # Test proxy resolution for socks.com
    http.request("http://test.socks.com")

    assert http.proxy_info is not None
    assert http.proxy_info.proxy_host == "proxy.socks.com"
    assert http.proxy_info.proxy_port == 1080
    assert http.proxy_info.proxy_type == socks.PROXY_TYPE_SOCKS5


def test_http_pac_direct_resolution(mock_pac_file, mock_httplib2_http):
    http = HttpPac(pac=mock_pac_file)

    # Test proxy resolution for other.com (DIRECT)
    # Even if environment variables exist, they should be ignored because PAC said DIRECT
    with patch("httplib2.proxy_info_from_environment") as mock_env:
        http.request("http://other.com")
        assert http.proxy_info is None
        mock_env.assert_not_called()


def test_http_pac_initialization():
    http = HttpPac(timeout=10, ca_certs="/path/to/certs")
    assert http.timeout == 10
    assert http.ca_certs == "/path/to/certs"


def test_http_pac_with_url(mock_httplib2_http):
    with patch("pypac4http2.http_pac.get_pac") as mock_get_pac:
        mock_pac = MagicMock()
        mock_pac.find_proxy_for_url.return_value = "DIRECT"
        mock_get_pac.return_value = mock_pac

        http = HttpPac(pac_url="http://test.pac")
        mock_get_pac.assert_called_once_with(url="http://test.pac")

        http.request("http://example.com")
        assert http._pac_file_instance == mock_pac


def test_http_pac_auto_discovery(mock_httplib2_http):
    with patch("pypac4http2.http_pac.get_pac") as mock_get_pac:
        mock_pac = MagicMock()
        mock_pac.find_proxy_for_url.return_value = "DIRECT"
        mock_get_pac.return_value = mock_pac

        http = HttpPac()
        http.request("http://example.com")
        mock_get_pac.assert_called_once_with()


def test_http_pac_env_fallback(mock_httplib2_http):
    with patch("pypac4http2.http_pac.get_pac", return_value=None):
        with patch("httplib2.proxy_info_from_environment") as mock_env_proxy:
            expected_proxy = httplib2.ProxyInfo(socks.PROXY_TYPE_HTTP, "envproxy", 8080)
            mock_env_proxy.return_value = expected_proxy

            http = HttpPac()
            http.request("http://example.com")

            assert http.proxy_info == expected_proxy
            mock_env_proxy.assert_called_once()


def test_http_pac_with_js(mock_httplib2_http):
    pac_js = """
    function FindProxyForURL(url, host) {
        return "PROXY jsproxy:8080";
    }
    """
    http = HttpPac(pac_js=pac_js)
    http.request("http://example.com")

    assert http.proxy_info is not None
    assert http.proxy_info.proxy_host == "jsproxy"
    assert http.proxy_info.proxy_port == 8080


def test_http_pac_with_env_var(mock_httplib2_http):
    with patch("pypac4http2.http_pac.get_pac") as mock_get_pac:
        mock_pac = MagicMock()
        mock_pac.find_proxy_for_url.return_value = "DIRECT"
        mock_get_pac.return_value = mock_pac

        with patch.dict("os.environ", {"PAC_URL": "http://env.pac"}):
            http = HttpPac()
            http.request("http://example.com")
            mock_get_pac.assert_called_once_with(url="http://env.pac")
