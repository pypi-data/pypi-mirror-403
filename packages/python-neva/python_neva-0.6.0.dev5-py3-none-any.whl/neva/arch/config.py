"""Helper TypedDict for application configuration."""

from typing import NotRequired, TypedDict

from neva.arch import ServiceProvider


class AppConfig(TypedDict):
    """Main application config.

    Attributes:
        title: The application title.
        debug: Whether the application is in debug mode.
        version: The application version.
        openapi_url: The URL for the OpenAPI specification.
        docs_url: The URL for the Swagger UI documentation.
        redoc_url: The URL for the ReDoc documentation.
        providers: List of service providers to register.
    """

    title: NotRequired[str]
    debug: NotRequired[bool]
    version: NotRequired[str]
    openapi_url: NotRequired[str]
    docs_url: NotRequired[str]
    redoc_url: NotRequired[str]
    providers: NotRequired[list[ServiceProvider]]


class ProviderConfig(TypedDict):
    """Application service provider config.

    Attributes:
        providers: List of service providers to register.
    """

    providers: NotRequired[list[ServiceProvider]]
