# pypac4http2
Python package which builds on pypac to add pac file support for httplib2 Http

This package adds proxy auto configure pac support to the [httplib2](https://github.com/httplib2/httplib2) library Http classby sub-classing the class and adding a new constructor parameter for a resolver class. 

## Installation

```bash
pip install pypac4http2
```

## Usage

### HttpPac Class

The `HttpPac` class extends `httplib2.Http` and automatically resolves the proxy for each request using a PAC file.

```python
from pypac4http2 import HttpPac

# Automatically discover PAC using OS settings or WPAD
http = HttpPac()
response, content = http.request("http://example.org")

# Specify a PAC URL
http = HttpPac(pac_url="http://internal.corp/proxy.pac")
response, content = http.request("http://example.org")

# Provide PAC as a JavaScript string
pac_js = "function FindProxyForURL(url, host) { return 'PROXY proxy:8080'; }"
http = HttpPac(pac_js=pac_js)
response, content = http.request("http://example.org")

# The library also supports the PAC_URL environment variable:
# export PAC_URL=http://internal.corp/proxy.pac
```

### Usage with Google API Client

`HttpPac` is designed to be a drop-in replacement for `httplib2.Http`, making it ideal for use with the [Google API Python Client](https://github.com/googleapis/google-api-python-client).

In a typical enterprise environment, you may also need your authentication flow (which often uses [google-auth](https://github.com/googleapis/google-auth-library-python) and `requests`) to respect the same PAC settings. You can use `pypac.PACSession` alongside `HttpPac`.

```python
import os
from googleapiclient.discovery import build
import google.auth
from google.auth.transport.requests import Request
from pypac import PACSession
from pypac4http2 import HttpPac

# 1. Use PACSession for authentication flows that use 'requests'
# pypac.PACSession doesn't natively check PAC_URL, so we pass it explicitly if set
pac_url = os.environ.get("PAC_URL")
auth_session = PACSession(url=pac_url) if pac_url else PACSession()
auth_request = Request(session=auth_session)

# 2. Get default credentials using the proxy-aware request
credentials, project = google.auth.default(request=auth_request)

# 3. Refresh credentials using the proxy-aware session
credentials.refresh(auth_request)

# 4. Use HttpPac for the Google API service calls (which use 'httplib2')
# Both will respect PAC settings (e.g. via PAC_URL environment variable)
http = HttpPac()
service = build('drive', 'v3', http=http, credentials=credentials)

# All API calls will now automatically resolve proxies via PAC
files = service.files().list().execute()
```

### CLI Tool

The package includes a CLI tool `pypac4http2` to resolve proxies for a given URL.

```bash
# Resolve proxy using OS auto-discovery (or PAC_URL env var if set)
pypac4http2 https://google.com

# Resolve proxy using a specific PAC URL
pypac4http2 --pac-url http://example.com/proxy.pac https://google.com

# Resolve proxy using a PAC JavaScript string
pypac4http2 --pac-js "function FindProxyForURL(url, host) { return 'DIRECT'; }" https://google.com
```

**Output Example:**
```json
Proxy choice: PROXY proxy.example.com:8080
{
  "target_url": "https://google.com",
  "pac_result": "PROXY proxy.example.com:8080",
  "proxy_info": {
    "proxy_type": "HTTP",
    "proxy_host": "proxy.example.com",
    "proxy_port": 8080
  }
}
```

