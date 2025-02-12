import json
import os
import yaml
from hAPI.exceptions import OpenAPISchemaError

class OpenAPIParser:
    """Parses OpenAPI schemas in JSON or YAML format"""

    def __init__(self, schema_file):
        self.schema_file = schema_file

    def parse_openapi_schema(self):
        """
        Parses an OpenAPI schema file (JSON or YAML) and returns a dictionary.
        """
        _, file_extension = os.path.splitext(self.schema_file)
        if file_extension.lower() == '.json':
            return self._parse_openapi_schema_from_json()
        elif file_extension.lower() in ['.yml', '.yaml']:
            return self._parse_openapi_schema_from_yaml()
        else:
            raise OpenAPISchemaError("Unsupported file format. Only JSON or YAML files are accepted.")

    def _parse_openapi_schema_from_json(self):
        """
        Reads an OpenAPI JSON file and returns a dictionary.
        """
        try:
            with open(self.schema_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise OpenAPISchemaError(f"Invalid JSON format: {e}")
        except FileNotFoundError as e:
            raise OpenAPISchemaError(f"File not found: {self.schema_file}")
        except Exception as e:
            raise OpenAPISchemaError(f"An error occurred while parsing JSON: {e}")
        
    def _parse_openapi_schema_from_yaml(self):
        """
        Reads an OpenAPI YAML file and returns a dictionary.
        """
        try:
            with open(self.schema_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise OpenAPISchemaError(f"Invalid YAML format: {e}")
        except FileNotFoundError as e:
            raise OpenAPISchemaError(f"File not found: {self.schema_file}")
        except Exception as e:
            raise OpenAPISchemaError(f"An error occurred while parsing YAML: {e}")
    
    @staticmethod
    def create_paths_dict(parsed_openapi_schema):
        """
        Extracts the 'paths' section from the OpenAPI schema.
        """
        if "paths" not in parsed_openapi_schema:
            raise OpenAPISchemaError("The OpenAPI schema does not contain a 'paths' object.")
        return parsed_openapi_schema['paths']
    
    @staticmethod
    def get_path_names(openapi_paths):
        """
        Returns a list of all API endpoints defined in the OpenAPI schema.
        """
        return list(openapi_paths.keys())
    
    @staticmethod
    def get_expected_http_verbs_for_path(openapi_paths, path):
        """
        Returns a list of HTTP methods supported for a specific API endpoint.
        """
        if path not in openapi_paths:
            raise OpenAPISchemaError("Path '{path}' not found in the OpenAPI schema.")
        return list(openapi_paths[path].keys())
    
    @staticmethod
    def get_expected_response_status_codes_for_path_and_verb(openapi_paths, path, verb):
        """
        Returns the expected HTTP status codes for a given path and HTTP method.
        """
        if path not in openapi_paths:
            raise OpenAPISchemaError(f"Path '{path}' not found in the OpenAPI schema.")
        if verb not in openapi_paths[path]:
            raise OpenAPISchemaError(f"Verb '{verb}' not defined for the path '{path}'.")
        return list(openapi_paths[path][verb].get("responses", {}).keys())