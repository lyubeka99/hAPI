import argparse
import sys
import json
from hapi import run_hapi
from core.module_loader import load_modules

def parse_headers(header_str):
    headers = {}
    if header_str:
        headers_tmp = header_str.split(";")
        for header_tmp in headers_tmp:
            if ":" not in header_tmp:
                print(f"Warning: Ignoring malformed header '{header_tmp}'.")
                continue
            key, value = header_tmp.split(":", 1)
            headers[key.strip()] = value.strip()
    return headers

def parse_cookies(cookie_str):
    cookies = {}
    if cookie_str:
        cookies_tmp = cookie_str.split(";")
        for cookie_tmp in cookies_tmp:
            if "=" not in cookie_tmp:
                print(f"Warning: Ignoring malformed cookie '{cookie_tmp}'.")
                continue
            key, value = cookie_tmp.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies

def main():
    parser = argparse.ArgumentParser(
        description="hAPI - A Security Testing Tool for OpenAPI-based REST APIs"
    )

    # Global arguments
    parser.add_argument("-u", "--url", required=True, help="Target API URL")
    parser.add_argument("-i", "--input", required=True, help="Path to OpenAPI Spec file (YAML/JSON)")
    parser.add_argument("-f", "--format", required=True, choices=["HTML", "JSON"], help="Report format")
    parser.add_argument("-x", "--proxy", help="HTTP proxy (e.g. 'http://127.0.0.1:8080')")
    parser.add_argument("-H", "--headers", help="Custom headers (e.g. 'User-Agent: test; X-Api-Key: testapikey')")
    parser.add_argument("-C", "--cookies", help="Custom cookies (e.g. 'SessionID=test; AuthToken=xyz')")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate verification")

    # Load modules BEFORE defining subcommands - prevents argparse error
    available_modules = load_modules()
    
    # Define subparsers for modules
    subparsers = parser.add_subparsers(dest="module", help="Security module to run")

    # Dynamically add available modules
    for module_name, module_class in available_modules.items():
        module_parser = subparsers.add_parser(module_name, help=f"{module_name} module")
        if hasattr(module_class, 'add_arguments'):
            module_class.add_arguments(module_parser)

    # 'all' subcommand - runs all modules
    all_parser = subparsers.add_parser("all", help="Run all modules")
    for module_name, module_class in available_modules.items():
        if hasattr(module_class, 'add_arguments'):
            module_class.add_arguments(all_parser)

    # Parse arguments
    args = parser.parse_args()

    # ✅ **Ensure a module was selected**
    if not args.module:
        parser.print_help()
        sys.exit(1)

    # Parse the cookies and headers before passing them to run_hapi()
    args.cookies = parse_cookies(args.cookies)
    args.headers = parse_headers(args.headers)

    # Pass the arguments to the main logic in hapi.py
    run_hapi(args)

if __name__ == "__main__":
    main()
