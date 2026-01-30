"""Region-aware EdAPI client factory."""

import edapi.edapi as edapi_module
from edapi import EdAPI


def create_client(region: str) -> EdAPI:
    """Create EdAPI client configured for the given region.

    Patches the edapi module constants before instantiation to support
    different Ed regions (us, eu, au, etc.).

    Args:
        region: Region code from URL (e.g., "us", "eu", "au").

    Returns:
        Configured EdAPI instance.
    """
    # US uses no subdomain, other regions use their code as subdomain
    subdomain = "" if region == "us" else f"{region}."

    # Patch module constants before instantiation
    edapi_module.API_BASE_URL = f"https://{subdomain}edstem.org/api/"
    edapi_module.STATIC_FILE_BASE_URL = (
        f"https://static.{subdomain}edusercontent.com/files/"
    )

    return EdAPI()
