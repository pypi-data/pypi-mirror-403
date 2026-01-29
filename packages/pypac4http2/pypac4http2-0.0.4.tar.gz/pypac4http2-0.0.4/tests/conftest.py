import pytest
import httplib2
import socks
from unittest.mock import MagicMock
from pypac.parser import PACFile


@pytest.fixture
def sample_pac_content():
    return """
    function FindProxyForURL(url, host) {
        if (shExpMatch(host, "*.example.com")) {
            return "PROXY proxy.example.com:8080";
        }
        if (shExpMatch(host, "*.socks.com")) {
            return "SOCKS5 proxy.socks.com:1080";
        }
        return "DIRECT";
    }
    """


@pytest.fixture
def mock_pac_file(sample_pac_content):
    pac = PACFile(sample_pac_content)
    return pac


@pytest.fixture
def mock_httplib2_http(monkeypatch):
    mock_request = MagicMock(return_value=(httplib2.Response({"status": "200"}), b"OK"))
    monkeypatch.setattr(httplib2.Http, "request", mock_request)
    return mock_request
