import os
import httplib2
from urllib.parse import urlparse
from pypac import get_pac
from pypac.parser import PACFile
from pypac4http2.utils import pac_result_to_proxy_info


class HttpPac(httplib2.Http):
    """
    Http subclass with PAC file proxy support.

    Uses pypac to resolve proxies based on the PAC file settings.
    """

    def __init__(
        self,
        cache=None,
        timeout=None,
        ca_certs=None,
        disable_ssl_certificate_validation=False,
        proxy_info=None,
        pac=None,
        pac_url=None,
        pac_js=None,
        **kwargs,
    ):
        """
        Initialize HttpPac.

        Args:
            pac: Optional pypac.PACFile instance.
            pac_url: Optional URL to PAC file.
            pac_js: Optional string containing PAC JavaScript code.
            All other args are passed to httplib2.Http.
        """
        super().__init__(
            cache=cache,
            timeout=timeout,
            ca_certs=ca_certs,
            disable_ssl_certificate_validation=disable_ssl_certificate_validation,
            proxy_info=proxy_info,
            **kwargs,
        )

        self._pac = pac
        self._pac_url = pac_url
        self._pac_js = pac_js
        self._pac_file_instance = None

        # Load PAC file if provided or auto-discover
        if self._pac:
            self._pac_file_instance = self._pac
        elif self._pac_js:
            self._pac_file_instance = PACFile(self._pac_js)
        elif self._pac_url:
            self._pac_file_instance = get_pac(url=self._pac_url)
        elif os.environ.get("PAC_URL"):
            self._pac_file_instance = get_pac(url=os.environ.get("PAC_URL"))
        else:
            # This will be resolved on first request if still None
            # or we can try to get it now
            pass

    def _ensure_pac(self):
        """Ensure PAC file is loaded."""
        if self._pac_file_instance is None:
            self._pac_file_instance = get_pac()

    def request(
        self,
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=httplib2.DEFAULT_MAX_REDIRECTS,
        connection_type=None,
    ):
        """
        Perform a request, resolving the proxy from PAC file first.
        """
        self._ensure_pac()

        if self._pac_file_instance:
            host = urlparse(uri).hostname or ""
            proxy_str = self._pac_file_instance.find_proxy_for_url(uri, host)
            if proxy_str and proxy_str.upper() != "DIRECT":
                self.proxy_info = pac_result_to_proxy_info(proxy_str)
            else:
                # PAC said DIRECT, so use no proxy
                self.proxy_info = None
        else:
            # No PAC file discovered/available, fall back to environment variables
            self.proxy_info = httplib2.proxy_info_from_environment()

        return super().request(
            uri,
            method=method,
            body=body,
            headers=headers,
            redirections=redirections,
            connection_type=connection_type,
        )
