class RateLimiting:
    DEFAULT_THRESHOLD = 100

    SENSITIVE_ENDPOINTS = [
        '/auth',
        '/login',
        '/token',
        '/access-token'
    ]

    SUSPICIOUS_STATUS_CODES = [
        429,  # Too Many Requests
        403,  # Forbidden (can be a sign of rate limiting)
        503   # Service Unavailable (can indicate a rate limit hit or service unavailability)
    ]

    RATE_LIMIT_HEADERS = [
        "Retry-After",
        "X-RateLimit-Remaining"
    ]

    def __init__(self, http_client, parsed_schema, args):
        """Initialize with HTTP client and pre-parsed OpenAPI schema."""
        self.http_client = http_client
        self.openapi_schema = parsed_schema["full_schema"]
        self.openapi_paths = parsed_schema["paths"]
        self.threshold = args.rl_threshold if args.rl_threshold else self.DEFAULT_THRESHOLD
        self.endpoints = args.rl_endpoints if args.rl_endpoints else None
        self.results = []

    @classmethod
    def add_arguments(cls, parser):
        """Defines CLI arguments specific to this module."""
        parser.add_argument("--rl-threshold", type=int, help="Threshold for rate limiting detection.")
        parser.add_argument("--rl-endpoints", help="A comma-separated list of target endpoints.")

    def run_check(self):
        """Runs the rate limiting check across endpoints with error handling."""
        
        request_threshold = self.threshold
        sensitive_endpoints = self.find_endpoints()
        baseline_endpoint = self._find_baseline_endpoint(sensitive_endpoints)

        if baseline_endpoint:
            endpoint_list = [baseline_endpoint]
        else:
            endpoint_list = []

        if self.endpoints:
            endpoint_list = []
            endpoints_to_test = self.endpoints.split(",")
        elif sensitive_endpoints:
            endpoints_to_test = sensitive_endpoints
        else:
            endpoints_to_test = []

        endpoint_list.extend(endpoints_to_test)

        for endpoint in endpoint_list:
            try:
                result_row = [endpoint]
                found_headers = []
                found_status_codes = set()
                response_times = []

                for i in range(request_threshold):
                    resp = self._send_request(endpoint)
                    response_times.append(round(resp.elapsed.total_seconds() * 1000, 4))  # Ensure 4 decimal places
                    
                    for header in self.RATE_LIMIT_HEADERS:
                        if header in resp.headers:
                            found_headers.append((header, resp.headers[header]))

                    if resp.status_code in self.SUSPICIOUS_STATUS_CODES:
                        found_status_codes.add(resp.status_code)

                batch_size = request_threshold // 3
                batch_1_avg = round(sum(response_times[:batch_size]) / batch_size, 4)
                batch_2_avg = round(sum(response_times[batch_size:2 * batch_size]) / batch_size, 4)
                batch_3_avg = round(sum(response_times[2 * batch_size:]) / batch_size, 4)

                heuristic_result = self.determine_heuristic_result(
                    found_headers, found_status_codes, batch_1_avg, batch_2_avg, batch_3_avg
                )

                result_row.extend([
                    found_headers if found_headers else None,
                    list(found_status_codes) if found_status_codes else None,
                    batch_1_avg,
                    batch_2_avg,
                    batch_3_avg,
                    heuristic_result
                ])

                self.results.append(result_row)

            except Exception as e:
                print(f"Error: Failed to process endpoint '{endpoint}' due to: {e}. Skipping to next.")
                continue  # Skip this endpoint and move to the next

        return self.results

    def _send_request(self, path):
        """Sends an HTTP request and returns the response object."""
        http_verb = self._get_verbs_for_path(path)[0].upper()
        response = self.http_client.send_request(path, http_verb)
        return response  # Keep it as a Response object
    
    def _get_verbs_for_path(self, path):
        """Returns the available HTTP verbs for a given path, handling variations like trailing slashes."""
        
        normalized_path = path.rstrip("/")  # Remove trailing slashes
        available_paths = {p.rstrip("/"): p for p in self.openapi_paths.keys()}  # Normalize all schema paths

        # Find a matching path
        matched_path = available_paths.get(normalized_path)

        if not matched_path:
            raise ValueError(f"Error: The provided endpoint '{path}' was not found in the OpenAPI schema. "
                            f"Did you mean '{self._suggest_similar_path(path)}'?")

        verbs = self.openapi_paths[matched_path].keys()
        return list(verbs) if verbs else ["GET"]
    
    def _suggest_similar_path(self, user_path):
        """Suggests the closest matching path from the OpenAPI schema."""
        
        from difflib import get_close_matches  # Helps find similar strings

        normalized_path = user_path.rstrip("/")
        available_paths = [p.rstrip("/") for p in self.openapi_paths.keys()]
        
        close_matches = get_close_matches(normalized_path, available_paths, n=1, cutoff=0.7)
        
        return close_matches[0] if close_matches else "Check your OpenAPI schema for valid paths."

    def _find_baseline_endpoint(self, sensitive_endpoints_list):
        """Extracts a non-senstive endpoint from the OpenAPI schema to serve as baseline for the rate limiting checks."""
        all_paths = list(self.openapi_paths.keys())
        sensitive_endpoints_set = set(sensitive_endpoints_list)

        for path in all_paths:
            if path not in sensitive_endpoints_set:
                return path  # Found a suitable baseline endpoint
        return None

    def find_endpoints(self):
        """Cross-checks the OpenAPI schema with predefined sensitive endpoints."""
        sensitive_found = []
        for path in self.openapi_paths.keys():
            if any(endpoint in path for endpoint in self.SENSITIVE_ENDPOINTS):
                sensitive_found.append(path)
        return sensitive_found

    def _check_throttling(self, request_times):
        """Checks if there's a significant increase in response times, which could indicate throttling."""
        if not request_times:
            return "No Data"

        avg_time = sum(request_times) / len(request_times)
        max_time = max(request_times)

        if max_time > avg_time * 2:
            return "Throttling Detected"
        
        return "No Throttling"

    def determine_heuristic_result(self, found_headers, found_status_codes, batch_1_avg, batch_2_avg, batch_3_avg):
        """Provides a heuristic conclusion if rate limiting is present based on headers, status codes, and response time changes."""
        
        result_messages = []

        # Check for rate limiting headers
        if found_headers:
            result_messages.append("<p>Rate limiting detected (headers found).</p>")

        # Check for rate limiting status codes
        if found_status_codes:
            result_messages.append(f"<p>Rate limiting detected (status codes found: {', '.join(map(str, found_status_codes))}).</p>")

        # Check for increasing response times
        if batch_1_avg and batch_2_avg and batch_3_avg:
            if batch_2_avg > batch_1_avg * 1.5 and batch_3_avg > batch_2_avg * 1.5:
                result_messages.append("<p>Possible throttling detected (> 50% increase in response time).</p>")
            elif batch_2_avg > batch_1_avg and batch_3_avg > batch_2_avg:
                result_messages.append("<p>Possible throttling detected (< 50% increase in response time). Possible false positive.</p>")

        # 4. If no indicators found
        if not result_messages:
            return "No clear signs of rate limiting detected"
        return "; ".join(result_messages)  # Combine all findings into one string


    def format_results(self, unformatted_results):
        description = f'''Tests whether a target REST API has any rate limiting measures. 
        <p>A value of None for the columns <strong>Rate Limit Headers Present</strong> or 
        <strong>Rate Limit Response Status Codes</strong> indicates that no such headers were returned by the API.</p>
        <p>The number of requests - {self.threshold} - has been split into 3 batches. If you notice a sensible increase 
        in response time between batches, this is a good sign that the API has request throttling enabled.'''
        references = [
            {"OWASP: API Security":"https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/"},
            {"OWASP: Blocking Brute Force Attacks":"https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks"}
        ]
        remediation = '''Rate limiting involves enforcing quotas on the number of requests allowed from a single source within a fixed time window (such as 10 requests per second from an IP address). This is an effective technique against brute force attacks which aim to constantly flood the application with login attempts. By analyzing legitimate user traffic patterns, the application can establish reasonable thresholds for a rate limiting policy. Additionally, account lockout policies can automatically disable login access after a predefined number of consecutive failed attempts. This denies adversaries further retries on guessed or leaked credentials.Combined with CAPTCHA challenges on login pages, which force automation to solve visual puzzles, these rate limiting and lockout mechanisms create artificial roadblocks that force brute force methods to consume precious time and resources, rendering wide scale attacks largely infeasible. Proper configuration ensures legitimate users face minimal disruption from these defenses.'''
        return {
            "module": "Rate Limiting",
            "description": description,
            "references": references,
            "remediation": remediation,
            "table": {
                "headers": [
                    "Endpoint", 
                    "Rate Limit Headers Present", 
                    "Rate Limit Response Status Codes", 
                    "Batch 1 Avg Response Time (ms)", 
                    "Batch 2 Avg Response Time (ms)", 
                    "Batch 3 Avg Response Time (ms)", 
                    "Heuristic Test Result"
                ],
                "rows": unformatted_results,
            }
        }