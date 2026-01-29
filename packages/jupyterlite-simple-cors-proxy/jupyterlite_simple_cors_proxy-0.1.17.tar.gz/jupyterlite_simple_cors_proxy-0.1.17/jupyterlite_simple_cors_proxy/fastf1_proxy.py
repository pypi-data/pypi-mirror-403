# import functools
from urllib.parse import urlparse, quote
import requests
# import requests_cache
# from requests_cache.session import CachedSession
import fastf1
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ProxyConfig:
    """Configuration for the CORS proxy."""
    proxy_url: str = "https://api.allorigins.win/raw?url="
    domains: List[str] = None
    debug: bool = False
    retry_count: int = 3
    timeout: int = 30

class CORSProxyPatcher:
    """Patches FastF1 to handle CORS requests through a proxy service."""

    def __init__(self, config: ProxyConfig = None):
        """
        Initialize the CORS proxy patcher for FastF1.
        
        Args:
            config (ProxyConfig): Configuration object for the proxy
        """
        self.config = config or ProxyConfig()
        self.domains = self.config.domains or [
            "api.formula1.com",
            "livetiming.formula1.com",
        ]

        self._setup_logging()
        self._setup_session()

    def _setup_logging(self) -> None:
        """Configure logging based on debug setting."""
        self.logger = logging.getLogger('CORSProxyPatcher')
        if self.config.debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _setup_session(self) -> None:
        """Set up the requests session with retry functionality."""
        self.session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=self.config.retry_count,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def should_proxy(self, url: str) -> bool:
        """
        Check if the URL should be routed through proxy based on domain.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL should be proxied
        """
        parsed = urlparse(url)
        should_proxy = any(domain in parsed.netloc for domain in self.domains)
        if self.config.debug:
            self.logger.debug(f"URL: {url} - Should proxy: {should_proxy}")
        return should_proxy

    def get_proxied_url(self, url: str) -> str:
        """
        Get the proxied version of the URL if needed.
        
        Args:
            url (str): Original URL
            
        Returns:
            str: Proxied URL if needed, original URL otherwise
        """
        if self.should_proxy(url):
            if 'allorigins' in self.config.proxy_url:
                proxied = f"{self.config.proxy_url}{quote(url, safe='')}"
            else:
                proxied = f"{self.config.proxy_url}{url}"
            if self.config.debug:
                self.logger.debug(f"Original URL: {url}")
                self.logger.debug(f"Proxied URL: {proxied}")
            return proxied
        return url

    def modify_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Modify request headers to handle CORS.
        
        Args:
            headers (dict, optional): Original headers
            
        Returns:
            dict: Modified headers
        """
        modified_headers = headers.copy() if headers else {}
        modified_headers.update({
            'Origin': 'null',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (compatible; FastF1/Python)'
        })
        return modified_headers

    def log_response(self, response: requests.Response, url: str) -> None:
        """
        Log response details for debugging.
        
        Args:
            response (Response): Response object
            url (str): Original URL
        """
        if self.config.debug:
            self.logger.debug(f"\nRequest to: {url}")
            self.logger.debug(f"Status Code: {response.status_code}")
            self.logger.debug(f"Headers: {dict(response.headers)}")
            try:
                self.logger.debug(f"Response Text: {response.text[:500]}...")
            except Exception as e:
                self.logger.debug(f"Couldn't read response text: {e}")

    def make_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, 
                    **kwargs: Any) -> requests.Response:
        """
        Make an HTTP request with proper error handling and logging.
        
        Args:
            method (str): HTTP method ('get' or 'post')
            url (str): URL to request
            headers (dict, optional): Request headers
            **kwargs: Additional request parameters
            
        Returns:
            Response: Response object
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        proxied_url = self.get_proxied_url(url)
        modified_headers = self.modify_headers(headers)
        kwargs['headers'] = modified_headers
        kwargs['timeout'] = kwargs.get('timeout', self.config.timeout)

        try:
            if fastf1.Cache._requests_session_cached and not fastf1.Cache._tmp_disabled:
                session = fastf1.Cache._requests_session_cached
            else:
                session = self.session

            response = getattr(session, method)(proxied_url, **kwargs)
            response.raise_for_status()

            self.log_response(response, url)
            return response

        except requests.exceptions.RequestException as e:
            if self.config.debug:
                self.logger.error(f"Request failed: {str(e)}")
            raise

    def patch_fastf1(self) -> None:
        """Patch FastF1's request methods to use CORS proxy."""
        def wrapped_get(cls, url: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
            return self.make_request('get', url, headers, **kwargs)

        def wrapped_post(cls, url: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
            return self.make_request('post', url, headers, **kwargs)

        fastf1.Cache.requests_get = classmethod(wrapped_get)
        fastf1.Cache.requests_post = classmethod(wrapped_post)

def enable_cors_proxy(
    domains: List[str],
    proxy_url: Optional[str] = None,
    debug: bool = False,
    retry_count: int = 3,
    timeout: int = 30
) -> CORSProxyPatcher:
    """
    Enable CORS proxy support for FastF1.
    
    Args:
        domains (list): List of domains to route through the proxy
        proxy_url (str, optional): Base URL of the CORS proxy service
        debug (bool): Enable debug logging
        retry_count (int): Number of retry attempts for failed requests
        timeout (int): Request timeout in seconds
        
    Returns:
        CORSProxyPatcher: Configured proxy patcher instance
    """
    config = ProxyConfig(
        proxy_url=proxy_url or "https://api.allorigins.win/raw?url=",
        domains=domains,
        debug=debug,
        retry_count=retry_count,
        timeout=timeout
    )

    patcher = CORSProxyPatcher(config)
    patcher.patch_fastf1()

    return patcher

# enable_cors_proxy(
#    domains=["api.formula1.com", "livetiming.formula1.com"],
#    debug=True,
#    proxy_url="https://corsproxy.io/",
# )
