import requests

class HTTPClient():
    """Handles HTTP requests with optional custom headers, cookies, and settings."""

    def __init__(self, base_url, headers=None, cookies=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers or {})
        self.session.cookies.update(cookies or {})

    def send_request(self, path, verb, **kwargs):
        """
        Send an HTTP  reuqest.

        :param path: API path to append to the base URL
        :param verb: HTTP method/verb (e.g., GET, POST, etc.)
        :param kwargs: Optional request parameters (headers, json, data, etc.)
        :return: Response object
        """
        try:
            final_url = f"{self.base_url}{path}"
            response = self.session.request(verb.upper(), final_url, **kwargs)
            return response
        except requests.RequestException as e:
            print(f"Error sending request: {e}")
            return None