import json
from hAPI.parsers.openapi_parser import OpenAPIParser
from hAPI.exceptions import OpenAPISchemaError

TEST_JSON_FILE = "tests/openapi.json"

parser = OpenAPIParser(TEST_JSON_FILE)

try:
    print("\n=== Testing OpenAPIParser ===")

    # Test schema parsing
    schema = parser.parse_openapi_schema()
    print("Parsed Schema:", schema)

    # Extract paths
    paths = parser.create_paths_dict(schema)
    print("\nExtracted Paths:", paths)

    # Get path names
    path_names = parser.get_path_names(paths)
    print("\nAvailable Paths:", path_names)

    # Get HTTP verbs for a specific path
    path_to_test = "/pet"
    verbs = parser.get_expected_http_verbs_for_path(paths, path_to_test)
    print(f"\nExpected HTTP verbs for {path_to_test}:", verbs)

    # Get expected HTTP status codes for a specific path and verb
    verb_to_test = "put"
    status_codes = parser.get_expected_http_codes_for_path_and_verb(paths, path_to_test, verb_to_test)
    print(f"\nExpected status codes for {path_to_test} {verb_to_test.upper()}:", status_codes)

except OpenAPISchemaError as e:
    print(f"\nError during parsing: {e}")

    