import argparse
import sys
import json
from core.http_client import HTTPClient
from core.module_loader import load_modules
from parsers.openapi_parser import OpenAPIParser
from reports.html_report import HTMLReport

def main():
    parser = argparse.ArgumentParser(
        description="hAPI - A Security Testing Tool for OpenAPI-based APIs"
    )

    # Global arguments
    parser.add_argument("-u", "--url", required=True, help="Target API URL")
    parser.add_argument("-i", "--input", required=True, help="Path to OpenAPI Spec file (YAML/JSON)")
    parser.add_argument("-f", "--format", required=True, help="Format for the report (HTML, JSON)")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate verification")
    parser.add_argument("-x", "--proxy", help="HTTP proxy (e.g. 'http://127.0.0.1:8080')")
    parser.add_argument("-H", "--header", help="Add a custom header (e.g. \"User-Agent: test\") ")
    parser.add_argument("-C", "--cookie", help="Add a custom cookie (e.g. \"Cookie: JSESSIONID=test\")")

    # Subparsers for modules
    subparsers = parser.add_subparsers(dest="module", help="Security module to run")

    # Dynamically load modules
    available_modules = load_modules()

    # Add arguments for each module
    for module_name, module_class in available_modules.items():
        module_parser = subparsers.add_parser(module_name, help=f"{module_name} module")
        if hasattr(module_class, 'add_arguments'):
            module_class.add_arguments(module_parser)

    # 'all' subcommand
    all_parser = subparsers.add_parser("all", help="Run all modules")
    
    # Now allow module-specific arguments to be passed under 'all'
    for module_name, module_class in available_modules.items():
        if hasattr(module_class, 'add_arguments'):
            module_class.add_arguments(all_parser)

    args = parser.parse_args()

    # Validate args
    if not args.module:
        parser.print_help()
        sys.exit(1)

    # Parse custom headers & cookies into dictionaries
    headers = {h.split("=")[0]: h.split("=")[1] for h in args.header} if args.header else {}
    cookies = {c.split("=")[0]: c.split("=")[1] for c in args.cookie} if args.cookie else {}
    proxies = {
        "http":f"{args.proxy}",
        "https":f"{args.proxy}"
    }

    ### DEBUG
    print(f"Proxy parameter contains: {args.proxy}")
    ### DEBUG

    # Create HTTP client with user settings
    http_client = HTTPClient(
        args.url,
        headers=headers,
        cookies=cookies,
        proxies=proxies,
        verify_ssl=not args.ignore_ssl
    )

    # Parse OpenAPI schema
    openapi_parser = OpenAPIParser(args.input)
    openapi_parsed_schema = openapi_parser.parse_openapi_schema()
    parsed_schema = {
        "full_schema": openapi_parsed_schema,
        "paths": openapi_parser.create_paths_dict(openapi_parsed_schema),
        "api_title": openapi_parser.get_api_title(openapi_parsed_schema)
    }

    results = []

    if args.module == "all":
        # Run all modules and pass relevant arguments to each module
        for module_name, module_class in available_modules.items():
            print(f"Running {module_name} module...")

            # Extract module-specific arguments dynamically
            module_specific_args = {}
            if hasattr(module_class, "add_arguments"):
                module_parser = argparse.ArgumentParser()
                module_class.add_arguments(module_parser)
                module_specific_args = {key: value for key, value in vars(args).items() if key in vars(module_parser.parse_args([]))}

            # Pass only relevant arguments to the module instance
            module_instance = module_class(http_client, parsed_schema, argparse.Namespace(**module_specific_args))
            raw_results = module_instance.run_check()
            results.append(module_instance.format_results(raw_results))
    else:
        # Run the selected module
        module_class = available_modules.get(args.module)
        if module_class:
            print(f"Running {args.module} module...")
            module_instance = module_class(http_client, parsed_schema, args)
            raw_results = module_instance.run_check()
            results.append(module_instance.format_results(raw_results))
        else:
            print(f"Module '{args.module}' not found.")
            sys.exit(1)

    # Generate Report
    try:
        api_title_formatted = parsed_schema["api_title"].replace(" ","_")

        if args.format.upper() == "HTML":
            report = HTMLReport(results)
            html_report = report.generate()
            report.save(html_report, api_title_formatted)
            print(f"Report saved to {api_title_formatted}_hAPI_report.html")
        elif args.format.upper() == "JSON":
            json_tmp_report = {
                "modules" : results
            }
            json_report = json.dumps(json_tmp_report, indent=4)
            try:
                with open(f"{api_title_formatted}_hAPI_report.json", "w") as json_file:
                    json_file.write(json_report)
                print(f"Report saved to {api_title_formatted}_hAPI_report.json")
            except Exception as e:
                print(f"Error writing JSON report to file: {e}")
                sys.exit(1)
        else:
            raise Exception("No such output format")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
