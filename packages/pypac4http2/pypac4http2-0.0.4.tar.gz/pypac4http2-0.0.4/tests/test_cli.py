import json
import sys
import pytest
import socks
from io import StringIO
from unittest.mock import patch, MagicMock
from pypac4http2.cli import main


def test_cli_basic(monkeypatch):
    mock_pac = MagicMock()
    mock_pac.find_proxy_for_url.return_value = "PROXY proxy.example.com:8080"

    with patch("pypac4http2.cli.get_pac", return_value=mock_pac):
        # Redirect stdout
        captured_output = StringIO()
        monkeypatch.setattr(sys, "stdout", captured_output)

        # Call main with arguments
        with patch("sys.argv", ["pypac4http2", "http://example.com"]):
            main()

        output = captured_output.getvalue()
        assert "Proxy choice: PROXY proxy.example.com:8080" in output

        # Parse JSON part (everything after the first line)
        json_str = "\n".join(output.splitlines()[1:])
        data = json.loads(json_str)

        assert data["target_url"] == "http://example.com"
        assert data["pac_result"] == "PROXY proxy.example.com:8080"
        assert data["proxy_info"]["proxy_host"] == "proxy.example.com"
        assert data["proxy_info"]["proxy_port"] == 8080
        assert data["proxy_info"]["proxy_type"] == "HTTP"


def test_cli_pac_url(monkeypatch):
    mock_pac = MagicMock()
    mock_pac.find_proxy_for_url.return_value = "DIRECT"

    with patch("pypac4http2.cli.get_pac") as mock_get_pac:
        mock_get_pac.return_value = mock_pac

        captured_output = StringIO()
        monkeypatch.setattr(sys, "stdout", captured_output)

        with patch(
            "sys.argv",
            ["pypac4http2", "--pac-url", "http://pac.url", "http://example.com"],
        ):
            main()

        mock_get_pac.assert_called_once_with(url="http://pac.url")
        assert "Proxy choice: DIRECT" in captured_output.getvalue()


def test_cli_no_pac(monkeypatch):
    with patch("pypac4http2.cli.get_pac", return_value=None):
        # With no PAC, it should fallback to DIRECT (if no env vars)
        captured_output = StringIO()
        monkeypatch.setattr(sys, "stdout", captured_output)

        with patch("sys.argv", ["pypac4http2", "http://example.com"]):
            main()

        assert "Proxy choice: DIRECT" in captured_output.getvalue()


def test_cli_error(monkeypatch):
    with patch("pypac4http2.cli.get_pac", side_effect=Exception("Test Error")):
        captured_stderr = StringIO()
        monkeypatch.setattr(sys, "stderr", captured_stderr)

        with patch("sys.argv", ["pypac4http2", "http://example.com"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

        assert "Error: Test Error" in captured_stderr.getvalue()


import pytest  # needed for pytest.raises

import pytest  # needed for pytest.raises


def test_cli_env_fallback(monkeypatch):
    with patch("pypac4http2.cli.get_pac", return_value=None):
        with patch("httplib2.proxy_info_from_environment") as mock_env_proxy:
            expected_proxy = MagicMock()
            expected_proxy.proxy_host = "envproxy"
            expected_proxy.proxy_port = 8080
            expected_proxy.proxy_type = socks.PROXY_TYPE_HTTP
            mock_env_proxy.return_value = expected_proxy

            captured_output = StringIO()
            monkeypatch.setattr(sys, "stdout", captured_output)

            with patch("sys.argv", ["pypac4http2", "http://example.com"]):
                main()

            output = captured_output.getvalue()
            assert "Proxy choice: ENV (envproxy:8080)" in output
            assert '"proxy_host": "envproxy"' in output


def test_cli_pac_js(monkeypatch):
    pac_js = 'function FindProxyForURL(url, host) { return "PROXY cli-js-proxy:8080"; }'
    captured_output = StringIO()
    monkeypatch.setattr(sys, "stdout", captured_output)

    with patch("sys.argv", ["pypac4http2", "--pac-js", pac_js, "http://example.com"]):
        main()

    output = captured_output.getvalue()
    assert "Proxy choice: PROXY cli-js-proxy:8080" in output
    assert '"proxy_host": "cli-js-proxy"' in output


def test_cli_pac_url_env_var(monkeypatch):
    mock_pac = MagicMock()
    mock_pac.find_proxy_for_url.return_value = "PROXY env-var-proxy:8080"

    with patch("pypac4http2.cli.get_pac", return_value=mock_pac) as mock_get_pac:
        with patch.dict("os.environ", {"PAC_URL": "http://env.pac"}):
            captured_output = StringIO()
            monkeypatch.setattr(sys, "stdout", captured_output)

            with patch("sys.argv", ["pypac4http2", "http://example.com"]):
                main()

            mock_get_pac.assert_called_once_with(url="http://env.pac")
            output = captured_output.getvalue()
            assert "Proxy choice: PROXY env-var-proxy:8080" in output
            assert '"proxy_host": "env-var-proxy"' in output
