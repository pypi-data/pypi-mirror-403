import argparse
import json
import sys
from pypac import get_pac
from pypac4http2.utils import pac_result_to_proxy_info, get_proxy_info_dict


def main():
    parser = argparse.ArgumentParser(
        description="pypac4http2 CLI tool to resolve proxy for a given URL using PAC file."
    )
    parser.add_argument(
        "--pac-url",
        help="Optional URL to PAC file. If not provided, uses OS auto-discovery.",
    )
    parser.add_argument("url", help="The target URL to resolve the proxy for.")

    args = parser.parse_args()

    try:
        if args.pac_url:
            pac = get_pac(url=args.pac_url)
        else:
            pac = get_pac()

        from urllib.parse import urlparse
        import httplib2

        host = urlparse(args.url).hostname or ""
        proxy_info = None

        if pac:
            proxy_str = pac.find_proxy_for_url(args.url, host)
            if proxy_str and proxy_str.upper() != "DIRECT":
                proxy_info = pac_result_to_proxy_info(proxy_str)
            else:
                proxy_str = "DIRECT"
        else:
            # Fallback to environment variables only if NO PAC FILE FOUND
            proxy_info = httplib2.proxy_info_from_environment()
            if proxy_info:
                proxy_str = f"ENV ({proxy_info.proxy_host}:{proxy_info.proxy_port})"
            else:
                proxy_str = "DIRECT"

        print(f"Proxy choice: {proxy_str}")

        output = {
            "target_url": args.url,
            "pac_result": proxy_str,
            "proxy_info": get_proxy_info_dict(proxy_info),
        }

        print(json.dumps(output, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
