# File: simple_cors_proxy/proxy.py
from urllib.parse import urlencode, quote
import requests

import io
import platform
from typing import Optional, Union

PLATFORM = platform.system().lower()
CORS_PROXIES = {
    "corsproxyio": {"url": "https://corsproxy.io/?url={}", "quote": True},
    "allorigins": {"url": "https://api.allorigins.win/raw?url={}", "quote": True},
    "none": {"url": "{}", "quote": False},
}


class CorsProxy:
    """CORS Proxy with optional caching support."""

    def __init__(self, use_cache: bool = False, **cache_kwargs):
        """
        Initialize the CORS proxy.
        
        Args:
            use_cache: Whether to enable request caching
            **cache_kwargs: Arguments passed to requests_cache.CachedSession
                          (e.g., cache_name, backend, expire_after)
        """
        if use_cache:
            import requests_cache
            # Set some sensible defaults if not provided
            if 'cache_name' not in cache_kwargs:
                cache_kwargs['cache_name'] = 'cors_proxy_cache'
            if 'expire_after' not in cache_kwargs:
                cache_kwargs['expire_after'] = 3600  # 1 hour default
            self.session = requests_cache.CachedSession(**cache_kwargs)
        else:
            self.session = requests
        if "proxy" in cache_kwargs:
            self.proxy = cache_kwargs["proxy"]
        else:
            self.proxy = "corsproxyio"


    def apply_cors_proxy(self, url, proxy="corsproxyio"):
        """
        Apply a CORS proxy to the given URL.

        Args:
            url (str): The original URL to proxy
            proxy (str): The proxy identifier to use from CORS_PROXIES

        Returns:
            str: The proxied URL
        """
        if proxy not in CORS_PROXIES:
            raise ValueError(
                f"Unknown proxy: {proxy}. Available proxies: {', '.join(CORS_PROXIES.keys())}"
            )

        proxy_config = CORS_PROXIES[proxy]

        if proxy_config["quote"]:
            url = proxy_config["url"].format(quote(url, safe=":/?=&"))
        else:
            url = proxy_config["url"].format(url)

        return url

    def xurl(
        self,
        url: str,
        params: Optional[dict] = None,
        force: bool = False,
        proxy: str = "",
    ) -> str:
        """Generate a proxied URL."""
        if PLATFORM == "emscripten" or force:
            if params:
                url = f"{url}?{urlencode(params)}"
            # url = f"https://corsproxy.io/{quote(url)}"
            if not proxy:
                proxy = self.proxy
            url = self.apply_cors_proxy(url, proxy=proxy)
        return url

    def furl(self, url: str, params: Optional[dict] = None, force: bool = False, proxy: str = "") -> io.BytesIO:
        """Return file like object after calling the proxied URL."""
        r = self.cors_proxy_get(url, params, force, proxy)
        # TO DO - something to consider?
        # https://simonwillison.net/2025/Jan/31/save-memory-with-bytesio/
        return io.BytesIO(r.content)

    def cors_proxy_get(self, url: str, params: Optional[dict] = None, force: bool = False, proxy: str = "corsproxyio") -> requests.Response:
        """
        CORS proxy for GET resources with requests-like response.
        
        Args:
            url: The URL to fetch
            params: Query parameters to include
            force: Force using the proxy even on non-emscripten platforms
            
        Returns:
            A requests response object.
        """
        proxy_url = self.xurl(url, params, force)
        return self.session.get(proxy_url)

    def robust_get_request(
        self, url: str, params: Optional[dict] = None, proxy: str = ""
    ) -> requests.Response:
        """
        Try to make a simple request else fall back to a proxy.
        """
        try:
            r = self.session.get(url, params=params)
        except:
            r = self.cors_proxy_get(url, params=params, proxy=proxy)
        return r


# Create default instance
_default_proxy = CorsProxy()

# Legacy function-based interface
xurl = _default_proxy.xurl
furl = _default_proxy.furl
cors_proxy_get = _default_proxy.cors_proxy_get
robust_get_request = _default_proxy.robust_get_request

# Convenience function to create a cached proxy
def create_cached_proxy(**cache_kwargs):
    """Create a new CorsProxy instance with caching enabled."""
    return CorsProxy(use_cache=True, **cache_kwargs)
