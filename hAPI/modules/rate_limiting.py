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
        request_threshold = self.threshold
        sensitive_endpoints = self.find_endpoints()
        baseline_endpoint = self._find_baseline_endpoint(sensitive_endpoints)

        # If all endpoints are sensitive, there is no baseline endpoint
        if baseline_endpoint:
            endpoint_list = [baseline_endpoint]
        else:
            endpoint_list = []

        if self.endpoints:
            endpoints_to_test = self.endpoints.split(",")
        elif sensitive_endpoints:
            endpoints_to_test = sensitive_endpoints
        else:
            endpoints_to_test = []

        endpoint_list.extend(endpoints_to_test)

        for endpoint in endpoint_list:
            result_row = [endpoint]
            found_headers = []
            found_status_codes = set()
            response_times = []

            for i in range(request_threshold):
                resp = self._send_request(endpoint)
                response_times.append(resp.elapsed.total_seconds()*1000)
                
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
        return self.results

    def _send_request(self, path):
        """Sends an HTTP request and returns the response object."""
        http_verb = self._get_verbs_for_path(path)[0].upper()
        response = self.http_client.send_request(path, http_verb)
        return response  # Keep it as a Response object
    
    def _get_verbs_for_path(self, path):
        """ Returns the first HTTP verb defined for that path. """
        verbs = self.openapi_paths.get(path).keys()
        if verbs:
            return list(verbs)
        else:
            return ["GET"]

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

        return {
            "module": "Rate Limiting",
            "description": description,
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