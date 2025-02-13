import requests
from hAPI.parsers.openapi_parser import OpenAPIParser

class VerbTamperingCheck:
    """Performs HTTP verb tampering checks against an OpenAPI-defined API."""

    UNSUPPORTED_VERB_STATUS_CODE = "405"

    DEFAULT_VERB_WORDLIST = [ "OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "TRACK", "DEBUG", "PURGE", "CONNECT", "PROPFIND", "PROPPATC", "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK", "VERSION-CONTROL", "REPORT", "CHECKOUT", "CHECKIN", "UNCHECKOUT", "MKWORKSPACE", "UPDATE", "LABEL", "MERGE", "BASELINE-CONTROL", "MKACTIVITY", "ORDERPATCH", "ACL", "PATCH", "SEARCH", "ARBITRARY", "BIND", "LINK", "MKCALENDAR", "MKREDIRECTREF", "PRI", "QUERY", "REBIND", "UNBIND", "UNLINK", "UPDATEREDIRECTREF" ]

    def __init__(self, url, openapi_file, http_verb_wordlist=DEFAULT_VERB_WORDLIST):
        """Initialize with OpenAPI schema and list of HTTP verbs to test."""
        self.url = url
        self.openapi_parser = OpenAPIParser(openapi_file)
        self.openapi_schema = self.openapi_parser.parse_openapi_schema()
        self.openapi_paths = self.openapi_parser.create_paths_dict(self.openapi_schema)
        self.http_verb_wordlist = http_verb_wordlist
        self.results = []
    
    def run_check(self):
        for path in self.openapi_paths:
            verbs_defined_in_openapi = self.openapi_parser.get_expected_http_verbs_for_path(
                self.openapi_paths, path
            )

            wordlist = self.http_verb_wordlist
            for verb in wordlist:
                # The first entry is the path, the second is the verb
                result_row = [path, verb] 

                # The third entry is either the expected response codes or 405
                if verb in verbs_defined_in_openapi:
                    expected_response_status_codes = self.openapi_parser.get_expected_response_status_codes_for_path_and_verb(
                        self.openapi_paths, path, verb
                    )
                    result_row.append(", ".join(expected_response_status_codes))
                else:
                    expected_response_status_codes = self.UNSUPPORTED_VERB_STATUS_CODE
                    result_row.append(expected_response_status_codes)

                # Send request
                response_status_code = self._send_request(path, verb)
                # Store actual response
                result_row.append(response_status_code)

                # Compare expected vs actual response
                result_row.append(self._compare_results(response_status_code,expected_response_status_codes))

                # Append to final result array
                self.results.append(result_row)
        return self.results

    def _send_request(self, path, verb):
        """Sends an HTTP request with the specified verb and returns a dictionary object with the response information."""
        try:
            final_url = f"{self.url}{path}"
            response = requests.request(verb.upper(), final_url)
            response_code = response.status_code

            return response_code
        except requests.RequestException as e:
            print(f"Error sending request: {e}")
            return "ERROR"
        
    def _compare_results(self, actual_status_code, expected_status_codes):
        """Compares the actual response code against expected codes."""

        if isinstance(expected_status_codes, str):
            expected_list = [expected_status_codes]
        else:
            expected_list = expected_status_codes
        
        return "PASS" if str(actual_status_code) in expected_list else "FAIL"

    def format_results(self, unformatted_results):
        """Formats the results of the verb tampering check in a way to be fed into the report."""
        module_name = "HTTP Verb Tampering"
        module_description = "Checks how the API responds to different HTTP verbs/methods."
        module_table_headers = [ "Path", "Verb", "Expected Response Code" , "Actual Response Code", "Test Result" ]

        module_table = {
            "headers": module_table_headers,
            "rows": unformatted_results
        }
        formatted_results = {
            "module": module_name,
            "description": module_description,
            "table": module_table
        }
        return formatted_results