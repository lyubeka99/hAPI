import sys
import json
from core.http_client import HTTPClient
from core.module_loader import load_modules
from parsers.openapi_parser import OpenAPIParser
from reports.html_report import HTMLReport
import argparse

def run_hapi(args, module_specific_args):
    """ Main function to run hAPI with parsed arguments. """
    
    # Load modules dynamically
    available_modules = load_modules()
    
    # Parse OpenAPI schema
    openapi_parser = OpenAPIParser(args.input)
    openapi_parsed_schema = openapi_parser.parse_openapi_schema()
    parsed_schema = {
        "full_schema": openapi_parsed_schema,
        "paths": openapi_parser.create_paths_dict(openapi_parsed_schema),
        "api_title": openapi_parser.get_api_title(openapi_parsed_schema)
    }

    # Create HTTP client
    http_client = HTTPClient(
        args.url,
        headers=args.headers,
        cookies=args.cookies,
        proxies={"http": args.proxy, "https": args.proxy} if args.proxy else None,
        verify_ssl=not args.ignore_ssl
    )

    results = []

    # For each module, get its optional arguments, parse them and create pass them to the object instance
    if "all" in args.modules:
        selected_modules = list(available_modules.keys())  # Expand 'all' to include all modules
    else:
        selected_modules = args.modules  # Run only the selected modules

    for module_name in selected_modules:
        module_class = available_modules.get(module_name)
        if module_class:
            print(f"Running {module_name} module...")

            # Get the pre-parsed module args from the dictionary object
            module_args = module_specific_args.get(module_name, argparse.Namespace())

            # Pass the correct args to the module
            module_instance = module_class(http_client, parsed_schema, module_args)
            raw_results = module_instance.run_check()
            results.append(module_instance.format_results(raw_results))
        else:
            print(f"Module '{module_name}' not found.")
            sys.exit(1)


    # Generate report
    generate_report(parsed_schema["api_title"], results, args.format)


def generate_report(api_title, results, format):
    """ Generates and saves the report in the specified format. """
    try:
        api_title_formatted = api_title.replace(" ", "_")

        if format.upper() == "HTML":
            report = HTMLReport(results)
            html_report = report.generate()
            report.save(html_report, api_title_formatted)
            print(f"Report saved to {api_title_formatted}_hAPI_report.html")
        elif format.upper() == "JSON":
            json_tmp_report = {"modules": results}
            json_report = json.dumps(json_tmp_report, indent=4)
            with open(f"{api_title_formatted}_hAPI_report.json", "w") as json_file:
                json_file.write(json_report)
            print(f"Report saved to {api_title_formatted}_hAPI_report.json")
        else:
            raise ValueError("No such output format")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)
