import os

class VerbTampering:
    """Performs HTTP verb tampering checks against an OpenAPI-defined API."""

    UNSUPPORTED_VERB_STATUS_CODE = "405"

    DEFAULT_VERB_WORDLIST = [
        "OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "TRACK", "DEBUG", "PURGE",
        "CONNECT", "PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK", "PATCH",
        "SEARCH", "BIND", "LINK", "MKCALENDAR", "REBIND", "UNBIND", "UNLINK", "QUERY"
    ]

    def __init__(self, http_client, parsed_schema, args):
        """Initialize with HTTP client and pre-parsed OpenAPI schema."""
        self.http_client = http_client
        self.openapi_schema = parsed_schema["full_schema"]
        self.openapi_paths = parsed_schema["paths"]
        self.http_verb_wordlist = self._load_wordlist(args.vt_wordlist)
        self.results = []

    @classmethod
    def add_arguments(cls, parser):
        """Defines CLI arguments specific to this module."""
        parser.add_argument("--vt-wordlist", help="Path to a custom wordlist for HTTP verbs for the verb tampering module.")

    def run_check(self):
        for path, details in self.openapi_paths.items():
            verbs_defined_in_openapi = list(details.keys())  # Extract available verbs

            for verb in self.http_verb_wordlist:
                result_row = [path, verb]

                # Determine expected response codes
                if verb.lower() in verbs_defined_in_openapi:
                    expected_response_status_codes = [
                        str(code) for code in details[verb.lower()]["responses"].keys()
                    ]
                else:
                    expected_response_status_codes = [self.UNSUPPORTED_VERB_STATUS_CODE]

                result_row.append(", ".join(expected_response_status_codes))

                # Send request and store response
                response_status_code = self._send_request(path, verb)
                result_row.append(str(response_status_code))

                # Compare expected vs actual
                result_row.append(self._compare_results(response_status_code, expected_response_status_codes))

                self.results.append(result_row)

        return self.results

    def _send_request(self, path, verb):
        """Sends an HTTP request with the specified verb and returns the response status code."""
        response = self.http_client.send_request(path, verb)
        return response.status_code

    def _compare_results(self, actual_status_code, expected_status_codes):
        """Compares actual vs expected response codes."""
        return "PASS" if str(actual_status_code) in expected_status_codes else "FAIL"
    
    def _load_wordlist(self, filepath):
        """Loads HTTP verbs from a file if provided; otherwise, uses default list."""
        if filepath:
            if os.path.exists(filepath) and os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8") as file:
                    return [line.strip().upper() for line in file if line.strip()]
            else:
                print(f"Warning: Wordlist file '{filepath}' not found. Using default verbs.")
        
        return self.DEFAULT_VERB_WORDLIST

    def format_results(self, unformatted_results):
        """Formats results for HTML reporting."""
        module_name = "HTTP Verb Tampering"
        description_paragraphs = [
            '''HTTP Verb Tampering is a security vulnerability where an attacker manipulates HTTP methods (verbs) such as 
            GET, POST, PUT, DELETE, and OPTIONS to bypass security controls and gain unauthorized access to restricted resources. 
            This issue arises when web applications enforce access controls based solely on HTTP methods but fail 
            to properly validate or restrict them.''',
            '''For example, an application may allow POST requests for user login but may not restrict HEAD or OPTIONS requests, 
            potentially leaking sensitive information. Similarly, if an application restricts DELETE requests for regular users 
            but fails to prevent them via alternative verbs like TRACE or PATCH, an attacker might exploit this oversight 
            to delete resources without proper authorization.''',
            '''Note that failed tests do not necessarily mean that a vulnerability is present in your API. They merely indicate that
            the API responded with a code that is not defined in your OpenAPI spec. This could be due to an error, malformed request 
            or even imprefect OpenAPI documentation.'''
            ]
        references = [
            {"OWASP API Security Top 10": "https://owasp.org/www-project-api-security/"},
            {"HTTP Methods Explained": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods"}
            ]
        remediation_paragraphs = [
            '''Enforce proper access controls: Implement server-side authorization based on roles and permissions, independent of the HTTP verb used. 
            Restrict sensitive operations (e.g., DELETE, PUT) to authenticated and authorized users only.''',
            '''Whitelist Allowed Methods - Explicitly define and enforce the allowed HTTP methods in the application and web server configuration. 
            Reject or return 405 Method Not Allowed for unsupported or unused HTTP verbs.''',
            '''Disable unnecessary HTTP methods (e.g., TRACE, OPTIONS) via web server configuration (Apache, Nginx, IIS).'''
        ]
        verification_commands = [
            '''curl -k -X PATCH https://<DOMAIN NAME/IP ADDRESS>/api/v1/example'''
        ]

        return {
            "module": module_name,
            "description_paragraphs": description_paragraphs,
            "references": references,
            "remediation_paragraphs": remediation_paragraphs,
            "verification_commands": verification_commands,
            "table": {
                "headers": ["Path", "Verb", "Expected Response Code", "Actual Response Code", "Test Result"],
                "rows": unformatted_results,
            }
        }
