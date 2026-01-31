"""Authentication providers for Corporate Memory client.

This package contains various authentication provider implementations for connecting
to eccenca Corporate Memory instances. It supports multiple OAuth 2.0 flows and
authentication methods to accommodate different deployment scenarios.

Supported authentication methods:
- Client Credentials Flow: For machine-to-machine authentication
- Resource Owner Password Flow: For trusted applications with user credentials
- Prefetched Token: For scenarios where tokens are obtained externally

The AuthProvider abstract base class provides a common interface, and specific
implementations handle the details of each authentication method.
"""
