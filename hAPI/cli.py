import argparse
import sys
import os
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

def show_help_for_modules(selected_modules, available_modules):
    """ Dynamically generate help for selected modules. """
    if "all" in selected_modules:
        selected_modules = list(available_modules.keys())  # Expand "all" to include all modules

    print("\n=== hAPI - A Security Testing Tool for OpenAPI-based REST APIs ===\n")
    print("Usage: python3 cli.py -u <URL> -i <SpecFile> -f <Format> <Modules> [Module Arguments]\n")
    print("Global Options:")
    print("  -u, --url         Target API URL")
    print("  -i, --input       Path to OpenAPI Spec file (YAML/JSON)")
    print("  -f, --format      Report format (HTML, JSON)")
    print("  -x, --proxy       HTTP proxy (e.g. 'http://127.0.0.1:8080')")
    print("  -H, --headers     Custom headers (e.g. 'User-Agent: test; X-Api-Key: testapikey')")
    print("  -C, --cookies     Custom cookies (e.g. 'SessionID=test; AuthToken=xyz')")
    print("  --ignore-ssl      Ignore SSL certificate verification")
    
    print("\nAvailable Modules:")
    for module in available_modules.keys():
        print(f"  - {module}")

    print("\nModule-Specific Arguments:")
    for module_name in selected_modules:
        if module_name in available_modules:
            module_class = available_modules[module_name]
            module_parser = argparse.ArgumentParser(prog=f"{module_name} module", add_help=False)
            if hasattr(module_class, 'add_arguments'):
                module_class.add_arguments(module_parser)
            print(f"\n{module_name} Options:")
            module_parser.print_help()

    sys.exit(0)

def main():
    # Load available modules dynamically
    available_modules = load_modules()

    # If "-h" or "--help" is provided, check for modules in the arguments
    if "-h" in sys.argv or "--help" in sys.argv:
        # Extract modules from command-line arguments (if any)
        modules_from_cli = [arg for arg in sys.argv[1:] if arg in available_modules or arg == "all"]
        show_help_for_modules(modules_from_cli, available_modules)

    parser = argparse.ArgumentParser(
        description="hAPI - A Security Testing Tool for OpenAPI-based REST APIs",
        allow_abbrev=False
    )

    # Global arguments
    parser.add_argument("-u", "--url", required=True, help="Target API URL")
    parser.add_argument("-i", "--input", required=True, help="Path to OpenAPI Spec file (YAML/JSON)")
    parser.add_argument("-f", "--format", required=True, choices=["HTML", "JSON"], help="Report format")
    parser.add_argument("-x", "--proxy", help="HTTP proxy (e.g. 'http://127.0.0.1:8080')")
    parser.add_argument("-H", "--headers", help="Custom headers (e.g. 'User-Agent: test; X-Api-Key: testapikey')")
    parser.add_argument("-C", "--cookies", help="Custom cookies (e.g. 'SessionID=test; AuthToken=xyz')")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate verification")

    # Add module selection (multiple choices allowed)
    parser.add_argument(
        "modules",
        nargs="+",
        choices=list(available_modules.keys()) + ["all"],
        help="Security modules to run (e.g., 'verb_tampering rate_limiting')"
    )

    # Parse initial known args
    known_args, remaining_args = parser.parse_known_args()

    # Normalize URL
    if known_args.url[-1] == "/":
        known_args.url = known_args.url[:-1]
    
    # Parse headers and cookies
    known_args.cookies = parse_cookies(known_args.cookies)
    known_args.headers = parse_headers(known_args.headers)

    # Expand "all" to include all available modules
    selected_modules = list(available_modules.keys()) if "all" in known_args.modules else known_args.modules

    # Dynamically parse module-specific arguments for all selected modules
    module_specific_args = {}
    for module_name in selected_modules:
        module_parser = argparse.ArgumentParser(add_help=False)
        if module_name in available_modules and hasattr(available_modules[module_name], 'add_arguments'):
            available_modules[module_name].add_arguments(module_parser)
            module_specific_args[module_name], _ = module_parser.parse_known_args(remaining_args)
        else:
            module_specific_args[module_name] = argparse.Namespace()  # Ensure module gets an empty Namespace

    # Pass arguments to main logic
    run_hapi(known_args, module_specific_args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
