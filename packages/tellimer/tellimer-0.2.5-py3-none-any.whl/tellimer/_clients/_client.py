import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from tellimer import __version__
from tellimer._clients._data import DataClient
from tellimer.errors import (
    AuthError,
    BadGatewayError,
    BadRequestError,
    ForbiddenError,
    GatewayTimeoutError,
    InternalServerError,
    MethodNotAllowedError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
)

# Errors that should trigger a retry
RETRYABLE_ERRORS = (
    ServiceUnavailableError,
    BadGatewayError,
    GatewayTimeoutError,
    RateLimitError,
    httpx.TimeoutException,
    httpx.ConnectError,
)


class Client:
    """
    A client for the Tellimer API. This client is used to interact with the Tellimer API.

    Args:
        api_key: The API key to use for the client.
        timeout: The timeout to use for the client. Defaults to 30 seconds.
        max_retries: Maximum number of retry attempts for transient errors. Defaults to 3.

    Example:
        # Recommended: Use as context manager to ensure proper cleanup
        with Client(api_key="your_api_key") as client:
            result = client.data.macro_data.get(countries=["ARG"])

        # Alternative: Manual cleanup
        client = Client(api_key="your_api_key")
        try:
            result = client.data.macro_data.get(countries=["ARG"])
        finally:
            client.close()
    """

    def __init__(self, api_key: str, timeout: float = 30, max_retries: int = 3):
        """
        Initialize the client.

        Args:
            api_key: The API key to use for the client. Must be a non-empty string.
            timeout: The timeout to use for the client. Defaults to 30 seconds.
            max_retries: Maximum number of retry attempts for transient errors. Defaults to 3.

        Raises:
            ValueError: If api_key is empty or not a string.
        """
        # Validate API key
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("api_key must be a non-empty string")

        # Store API key as private attribute to reduce accidental exposure
        self._api_key = api_key.strip()
        # self._base_url = "http://localhost:8000/"
        self._base_url = "https://sdk.tellimer.com/"
        self._timeout = timeout
        self._max_retries = max_retries

        # Create persistent HTTP client with connection pooling
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "User-Agent": f"tellimer-sdk/{__version__}",
            },
            timeout=timeout,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
            ),
        )

        self.data = DataClient(self._make_request)
        # self.articles = ArticlesClient(self._make_request)
        # self.news = NewsClient(self._make_request)

    def close(self) -> None:
        """
        Close the HTTP client and release resources.

        This should be called when you're done using the client to properly
        release connection resources. Alternatively, use the client as a
        context manager which handles cleanup automatically.
        """
        self._client.close()

    def __enter__(self) -> "Client":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and cleanup resources."""
        self.close()

    def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Internal method to make HTTP requests with automatic retry for transient errors.

        Retries are applied for:
        - 5xx server errors (502, 503, 504)
        - 429 rate limit errors
        - Connection errors and timeouts

        4xx client errors (except 429) are NOT retried as they indicate
        issues with the request that won't be resolved by retrying.
        """
        return self._make_request_with_retry(method, url, **kwargs)

    @retry(
        retry=retry_if_exception_type(RETRYABLE_ERRORS),
        stop=stop_after_attempt(3),  # Will be overridden by instance setting
        wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
        reraise=True,
    )
    def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """
        Execute the HTTP request with retry logic.
        """
        try:
            resp = getattr(self._client, method)(url, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code

            if status_code == 400:
                raise BadRequestError("Bad request") from e
            elif status_code == 401:
                raise AuthError("Invalid API key") from e
            elif status_code == 403:
                raise ForbiddenError("Forbidden") from e
            elif status_code == 404:
                raise NotFoundError("Resource not found") from e
            elif status_code == 405:
                raise MethodNotAllowedError("Method not allowed") from e
            elif status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            elif status_code == 500:
                raise InternalServerError("Internal server error") from e
            elif status_code == 502:
                raise BadGatewayError("Bad gateway") from e
            elif status_code == 503:
                raise ServiceUnavailableError("Service unavailable") from e
            elif status_code == 504:
                raise GatewayTimeoutError("Gateway timeout") from e
            else:
                # Don't expose raw server error messages to clients
                raise httpx.HTTPStatusError(
                    f"HTTP {status_code}: Unexpected error occurred",
                    request=e.request,
                    response=e.response,
                )
