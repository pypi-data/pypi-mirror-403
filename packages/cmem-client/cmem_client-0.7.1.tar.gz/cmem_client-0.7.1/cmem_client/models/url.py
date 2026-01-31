"""HTTP URL validation and manipulation utilities.

This module provides the HttpUrl class, which extends httpx.URL with additional
validation and path manipulation capabilities. It ensures URLs are well-formed
and provides convenient methods for building API endpoints.

The HttpUrl class is used throughout the configuration system to construct
various Corporate Memory API endpoints from base URLs.
"""

from httpx import URL


class HttpUrl(URL):
    """A http(s) URL"""

    def __init__(self, url: str) -> None:
        if str(URL(url)) != url:
            raise ValueError(f"URL '{url}' not well formed. Use '{URL(url)!s}' instead.")
        super().__init__(url)

    def __truediv__(self, other: str) -> "HttpUrl":
        """Add or extend a Path in the url

        Examples:
            >>> HttpUrl("https://example.com/") / "/path/to/file.txt"
            HttpUrl('https://example.com/path/to/file.txt')
        """
        path = self.path
        if path.endswith("/") and other.startswith("/"):
            other = other[1:]
        if not path.endswith("/") and not other.startswith("/"):
            other = f"/{other}"
        return HttpUrl(f"{self!s}{other}")
