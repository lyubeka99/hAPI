import argparse
import sys
from core.http_client import HTTPClient
from core.module_loader import load_modules
from reports.html_report import HTMLReport

def main():
    parser = argparse.ArgumentParser(
        description="hAPI - A Security Testing Tool for OpenAPI-based APIs"
    )

    # Required Arguments
    parser.add_argument("-u", "--url", required=True, help="Target API URL")
    parser.add_argument("-o", "--openapi", required=True, help="Path to OpenAPI Spec file (YAML/JSON)")
    
    # Optional Arguments
    parser.add_argument("-m", "--modules", required=True, help="Comma-separated list of security modules (e.g., verb-tampering,headers-check)")
    parser.add_argument("--header", action="append", help="Custom HTTP headers (e.g., 'Authorization: Bearer xyz')")
    parser.add_argument("--cookie", action="append", help="Custom cookies (e.g., 'session=123')")
    parser.add_argument("--proxy", help="HTTP proxy (e.g., 'http://127.0.0.1:8080')")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate verification")
    parser.add_argument("--report", help="Path to save the HTML report")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # List available modules
    list_parser = subparsers.add_parser("list", help="List available security modules")

    args = parser.parse_args()

    if args.command == "list":
        # Dynamically list available modules
        print("Available security modules:")
        for module in load_modules():
            print(f"- {module}")
        sys.exit(0)

    # Parse custom headers & cookies into dictionaries
    headers = {h.split(":")[0]: h.split(":")[1] for h in args.header} if args.header else {}
    cookies = {c.split("=")[0]: c.split("=")[1] for c in args.cookie} if args.cookie else {}

    # Create HTTP client with user settings
    http_client = HTTPClient(args.url, headers=headers, cookies=cookies, verify_ssl=not args.ignore_ssl)


    # Load selected modules
    available_modules = load_modules()  # This should return a dictionary of module names -> module classes

    if args.modules.lower() == "all":
        selected_modules = available_modules.keys()  # Run all modules
    else:
        selected_modules = args.modules.split(",")

    results = []

    for module_name in selected_modules:
        module = available_modules.get(module_name)
        if module:
            print(f"Running {module_name} module...")
            checker = module(args.url, args.openapi, http_client)
            results.append(checker.run_check())
        else:
            print(f"Module '{module_name}' not found.")

    # Generate Report (if specified)
    if args.report:
        report = HTMLReport(results)
        report.save(args.report)
        print(f"Report saved to {args.report}")

if __name__ == "__main__":
    main()
