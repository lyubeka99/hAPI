import requests
import urllib3

class HTTPClient:
    """Handles HTTP requests with optional custom headers, cookies, proxies, and SSL settings."""

    def __init__(self, base_url, headers=None, cookies=None, proxies=None, verify_ssl=True):
        """
        Initializes the HTTP client.

        :param base_url: The base URL of the API.
        :param headers: Dictionary of default headers.
        :param cookies: Dictionary of default cookies.
        :param proxies: Dictionary of proxies (e.g., {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}).
        :param verify_ssl: Boolean to enable/disable SSL verification (default: True).
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers or {})
        self.session.cookies.update(cookies or {})
        self.session.proxies.update(proxies or {})  # Proxy support
        self.session.verify = verify_ssl  # Can be set to False for private APIs with self-signed certs

        # Suppress SSL warnings if verification is disabled
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def send_request(self, path, verb, **kwargs):
        """
        Send an HTTP request.

        :param path: API path to append to the base URL.
        :param verb: HTTP method/verb (e.g., GET, POST, etc.).
        :param kwargs: Optional request parameters (headers, json, data, etc.).
        :return: Response object or None if request fails.
        """
        try:
            final_url = f"{self.base_url}{path}"
            response = self.session.request(verb.upper(), final_url, **kwargs)
            return response
        except requests.RequestException as e:
            print(f"Error sending request: {e}")
            return None
