"""JWT token validation for Auth0 integration."""

import os
from typing import Optional


def get_jwt_config():
    """Get JWT configuration from environment variables.

    Returns:
        dict with jwks_uri, issuer, audience
    """
    auth0_domain = os.getenv("AUTH0_DOMAIN", "")
    auth0_audience = os.getenv("AUTH0_AUDIENCE", "")

    if not auth0_domain:
        raise ValueError("AUTH0_DOMAIN environment variable not set")
    if not auth0_audience:
        raise ValueError("AUTH0_AUDIENCE environment variable not set")

    return {
        "jwks_uri": f"https://{auth0_domain}/.well-known/jwks.json",
        "issuer": f"https://{auth0_domain}/",
        "audience": auth0_audience,
    }


def create_jwt_verifier():
    """Create JWTVerifier for Auth0 validation.

    Returns:
        JWTVerifier instance configured for Auth0
    """
    try:
        from fastmcp.server.auth.providers.jwt import JWTVerifier
    except ImportError:
        raise ImportError("fastmcp not installed. Install with: pip install fastmcp")

    config = get_jwt_config()

    return JWTVerifier(
        jwks_uri=config["jwks_uri"],
        issuer=config["issuer"],
        audience=config["audience"],
    )


__all__ = ["get_jwt_config", "create_jwt_verifier"]
