import random

class CommonSecurityHeaders:
    HEADERS_TO_CHECK = {
        "Strict-Transport-Security": {"expected": True, "display": "Strict-Transport-Security"},
        "X-Content-Type-Options": {"expected": True, "display": "X-Content-Type-Options"},
        "Server": {"expected": False, "display": "Server"},
        "X-Powered-By": {"expected": False, "display": "X-Powered-By"}
    }

    def __init__(self, http_client, parsed_schema, args):
        """Initialize with HTTP client and OpenAPI schema."""
        self.http_client = http_client
        self.openapi_paths = parsed_schema["paths"]
        self.endpoints = args.csh_endpoints.split(",") if args.csh_endpoints else list(self.openapi_paths.keys())
        self.results = []

    @classmethod
    def add_arguments(cls, parser):
        """Defines CLI arguments for this module."""
        parser.add_argument("--csh-endpoints", help="A comma-separated list of endpoints to check security headers.")

    def run_check(self):
        """Checks if security headers are properly set against a randomly chosen endpoint."""
        if not self.endpoints:
            print("No available endpoints to test security headers.")
            return []

        endpoint = random.choice(self.endpoints)
        try:
            response = self._send_request(endpoint)
            headers = response.headers

            for header, details in self.HEADERS_TO_CHECK.items():
                is_present = header in headers
                expected = details["expected"]
                header_value = headers.get(header, "N/A")
                test_result = "PASS" if is_present == expected else "FAIL"

                self.results.append([
                    endpoint,
                    details["display"],
                    "Yes" if is_present else "No",
                    header_value,
                    test_result
                ])

        except Exception as e:
            print(f"Error: Failed to process endpoint '{endpoint}' due to: {e}. Skipping.")
        
        return self.results

    def _send_request(self, path):
        """Sends a GET request and returns the response object."""
        try:
            response = self.http_client.send_request(path, "GET")
            return response
        except Exception as e:
            print(f"Warning: Request to '{path}' failed: {e}")
            return type("FakeResponse", (), {"headers": {}})()  # Return empty headers to prevent crashes

    def format_results(self, unformatted_results):
        """Formats the results into a structured format for output."""
        description_paragraphs = [
            "This module checks for some common HTTP security headers used in REST APIs.",
            '''<ul><li>HTTP Strict Transport Security (HSTS) - ensures that browsers only communicate with a website over HTTPS, 
            preventing protocol downgrade attacks and mitigating man-in-the-middle (MITM) attacks.</li>''',
            '''<li>X-Content-Type-Options - Prevents MIME-type sniffing by forcing the browser to respect the declared Content-Type header, 
            mitigating certain types of cross-site scripting (XSS) and content injection attacks.</li>''',
            '''<li>Server - reveals details about the web server software (e.g., Apache/2.4.41), 
            which attackers can use to fingerprint the system and target known vulnerabilities.</li>''',
            '''<li>X-Powered-By - Similar to the Server header, X-Powered-By exposes backend technology (e.g., X-Powered-By: 
            PHP/7.4 or Express), making it easier for attackers to craft targeted exploits.</li></ul>'''
        ]

        references = [
            {"Mozilla Security Headers Guide": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"},
            {"HTTP security headers: An easy way to harden your web applications": "https://www.invicti.com/blog/web-security/http-security-headers/"}
        ]

        remediation_paragraphs = [
            "Ensure that security headers like 'Strict-Transport-Security' and 'X-Content-Type-Options' are present to enhance protection.",
            "Remove 'Server' and 'X-Powered-By' headers to prevent unnecessary exposure of technology stack information."
        ]

        return {
            "module": "Common Security Headers",
            "description_paragraphs": description_paragraphs,
            "references": references,
            "remediation_paragraphs": remediation_paragraphs,
            "table": {
                "headers": ["Endpoint", "Header", "Is Present?", "Header Value", "Test Result"],
                "rows": unformatted_results,
            }
        }
