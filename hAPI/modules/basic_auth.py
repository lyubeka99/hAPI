import random

class BasicAuth:
    DEFAULT_TEST_USERNAME = "testuser"
    DEFAULT_TEST_PASSWORD = "testpass"

    def __init__(self, http_client, parsed_schema, args):
        """Initialize with HTTP client and pre-parsed OpenAPI schema."""
        self.http_client = http_client
        self.openapi_paths = list(parsed_schema["paths"].keys()) if parsed_schema else []
        self.endpoints = args.ba_endpoints.split(",") if args.ba_endpoints else None
        self.username = args.ba_username
        self.password = args.ba_password
        self.results = []
        self.warning_message = None

    @classmethod
    def add_arguments(cls, parser):
        """Defines CLI arguments specific to this module."""
        parser.add_argument("--ba-endpoints", help="A comma-separated list of target endpoints.")
        parser.add_argument("--ba-username", help="Valid username for basic authentication testing.")
        parser.add_argument("--ba-password", help="Valid password for basic authentication testing.")

    def run_check(self):
        """Runs the HTTP Basic Authentication test."""
        if self.endpoints:
            selected_endpoints = self.endpoints
        else:
            if not self.openapi_paths:
                print("No OpenAPI schema provided and no endpoints specified. Skipping HTTP Basic Auth check.")
                return []
            selected_endpoints = random.sample(self.openapi_paths, min(5, len(self.openapi_paths)))  # Pick 5 random endpoints

        for endpoint in selected_endpoints:
            result_row = [endpoint]

            # Test without authentication
            no_auth_response = self._send_request(endpoint, auth=None)
            no_auth_status = no_auth_response.status_code
            www_auth_header = no_auth_response.headers.get("WWW-Authenticate", "Not Present")

            # Test with test credentials
            test_auth_response = self._send_request(endpoint, auth=(self.DEFAULT_TEST_USERNAME, self.DEFAULT_TEST_PASSWORD))
            test_auth_status = test_auth_response.status_code

            # Test with real credentials (if provided)
            real_auth_status = None
            if self.username and self.password:
                real_auth_response = self._send_request(endpoint, auth=(self.username, self.password))
                real_auth_status = real_auth_response.status_code

                # Log a warning if test creds succeed but real creds fail
                if test_auth_status < 400 and real_auth_status >= 400:
                    self.warning_message = (
                        "<strong>Warning: The API accepted default test credentials (testuser:testpass) but rejected the provided valid credentials. "
                        "This may indicate weak default credentials or a misconfiguration.<strong>"
                    )

            # Determine test result
            if www_auth_header != "Not Present":
                test_result = "Supports Basic Auth"
            elif no_auth_status != test_auth_status:
                test_result = "Supports Basic Auth"
            else:
                test_result = "No Basic Auth Detected"

            result_row.extend([
                no_auth_status, 
                test_auth_status, 
                real_auth_status if real_auth_status is not None else "Not Tested", 
                www_auth_header,
                test_result
            ])

            self.results.append(result_row)

        return self.results

    def _send_request(self, path, auth):
        """Sends a GET request with optional Basic Authentication."""
        return self.http_client.send_request(path, "GET", auth=auth)

    def format_results(self, unformatted_results):
        """Formats the results for output."""
        description_paragraphs = [
            '''HTTP Basic Authentication transmits credentials (username and password) in the Authorization header as a Base64-encoded string, 
            making it suceptible to multiple attack verctors.''',
            "<ul><li>If used over HTTP (instead of HTTPS), credentials can be easily captured by attackers.</li>",
            "<li>Since there is no challenge-response mechanism, an attacker who captures the request can reuse the credentials.</li>",
            "<li>Browsers and some clients may persistently store credentials, increasing exposure.</li></ul>",
            "This authentication method is outdated and should be replaced with more secure alternatives."
        ]

        if not self.username or not self.password:
            description_paragraphs.append(
                "<mark>If your API supports password-based authentication, rerun this test with --ba-username and --ba-password for more accurate results. "
                "If your API doesn't support password-based authentication and uses keys instead, you can disregard this message.<mark>"
            )

        if self.warning_message:
            description_paragraphs.append(self.warning_message)

        references = [
            {"PortSwigger: Basic Authentication": "https://portswigger.net/web-security/authentication/password-based#http-basic-authentication"},
            {"MDN Web Docs: HTTP authentication":"https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication"}
        ]

        remediation_paragraphs = [
            '''Migrate to More Secure Authentication Methods: Use OAuth 2.0, API tokens, JWTs, or mutual TLS authentication instead. 
            If password-based authentication is required, implement Digest Auth or modern authentication mechanisms (e.g., OpenID Connect).''',
            '''Enforce HTTPS: If Basic Auth must be used, never transmit credentials over HTTP - always enforce HTTPS.'''
        ]

        verification_commands = [
            '''curl -k -u username:password https://<DOMAIN NAME/IP ADDRESS>/api/v1/example'''
        ]

        return {
            "module": "HTTP Basic Authentication",
            "description_paragraphs": description_paragraphs,
            "references": references,
            "remediation_paragraphs": remediation_paragraphs,
            "verification_commands": verification_commands,
            "table": {
                "headers": [
                    "Endpoint", 
                    "Response Code without Basic Auth", 
                    "Response Code with Test Credentials", 
                    "Response Code with Real Credentials", 
                    "WWW-Authenticate Header",
                    "Test Result"
                ],
                "rows": unformatted_results,
            }
        }
