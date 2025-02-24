import random

class Cors:
    TEST_ORIGINS = ["null", "https://evil.com"]

    def __init__(self, http_client, parsed_schema, args):
        """Initialize with HTTP client and pre-parsed OpenAPI schema."""
        self.http_client = http_client
        self.openapi_paths = list(parsed_schema["paths"].keys()) if parsed_schema else []
        self.endpoints = args.cors_endpoints.split(",") if args.cors_endpoints else None
        self.custom_origin = args.cors_custom_origin
        self.results = []
        if self.custom_origin:
            self.TEST_ORIGINS.append(self.custom_origin)

    @classmethod
    def add_arguments(cls, parser):
        """Defines CLI arguments specific to this module."""
        parser.add_argument("--cors-endpoints", help="A comma-separated list of target endpoints.")
        parser.add_argument("--cors-custom-origin", help="Custom origin to test against the target API.")

    def run_check(self):
        """Runs the CORS security test."""
        if self.endpoints:
            selected_endpoints = self.endpoints
        else:
            if not self.openapi_paths:
                print("No OpenAPI schema provided and no endpoints specified. Skipping CORS check.")
                return []
            selected_endpoints = random.sample(self.openapi_paths, min(3, len(self.openapi_paths)))

        for endpoint in selected_endpoints:
            for test_origin in self.TEST_ORIGINS:
                response = self._send_request(endpoint, headers={"Origin": test_origin})
                acao = response.headers.get("Access-Control-Allow-Origin", "Not Present")
                acac = response.headers.get("Access-Control-Allow-Credentials", "Not Present")

                # Security Issues
                if acao == test_origin:
                    if acac == "true":
                        security_issue = "ACAO reflects Origin and ACAC: true (High Risk)"
                    else:
                        security_issue = "ACAO reflects Origin (Potential Risk)"
                elif acao == "*":
                    if acac == "true":
                        security_issue = "ACAC: true with wildcard ACAO (Blocked by Browsers, but Bad Config)"
                    else:
                        security_issue = "ACAO accepts wildcard (Potential Risk)"
                elif acao == "null":
                    if acac == "true":
                        security_issue = "ACAO: null and ACAC: true (High Risk)"
                    else:
                        security_issue = "ACAO: null (Potential Risk)"
                else:
                    security_issue = "No obvious misconfiguration"

                # Store results
                self.results.append([endpoint, test_origin, acao, acac, security_issue])

        return self.results

    def _send_request(self, path, headers=None):
        """Sends a GET request with optional CORS headers."""
        return self.http_client.send_request(path, "GET", headers=headers)

    def format_results(self, unformatted_results):
        """Formats the results for output."""
        description_paragraphs = [
            '''Cross-Origin Resource Sharing (CORS) is a security mechanism that controls how web applications from 
            different origins interact with an API. A misconfigured CORS policy can allow unauthorized websites to access 
            sensitive data on behalf of authenticated users.''',
            '''This module sends requests using different <strong>Origin</strong> values to check if they are allowed. 
            If you want to test a particular origin, use the <strong>--cors-custom-origin</strong> option.''',
            '''<ul><li>ACAO = Access-Control-Allow-Origin header</li>''',
            '''<li>ACAC = Access-Control-Allow-Credentials header</li></ul>'''
        ]

        references = [
            {"Exploiting CORS - How to Pentest Cross-Origin Resource Sharing Vulnerabilities":"https://www.freecodecamp.org/news/exploiting-cors-guide-to-pentesting"},
            {"Tenable: Understanding Cross-Origin Resource Sharing Vulnerabilities":"https://www.tenable.com/blog/understanding-cross-origin-resource-sharing-vulnerabilities"},
            {"PortSwigger: CORS": "https://portswigger.net/web-security/cors"}
        ]

        remediation_paragraphs = [
            "Implement proper CORS headers: The server can add appropriate CORS headers to allow cross-origin requests from only trusted sites.",
            "Restrict access to sensitive data: It is important to restrict access to sensitive data to only trusted domains. This can be done by implementing access control measures such as authentication and authorization."
        ]

        verification_commands = [
            '''curl -k -I -H 'Origin: https://evil.com' https://<DOMAIN NAME/IP ADDRESS>/api/v1/example'''
        ]

        return {
            "module": "CORS Security",
            "description_paragraphs": description_paragraphs,
            "references": references,
            "remediation_paragraphs": remediation_paragraphs,
            "verification_commands": verification_commands,
            "table": {
                "headers": [
                    "Endpoint",
                    "Tested Origin",
                    "Response ACAO",
                    "Response ACAC",
                    "Test Result"
                ],
                "rows": unformatted_results,
            }
        }
