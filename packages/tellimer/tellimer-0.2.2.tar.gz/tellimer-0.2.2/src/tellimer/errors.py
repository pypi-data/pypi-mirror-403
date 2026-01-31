class AuthError(Exception):
    """Raised when the API key is invalid."""

    pass


class BadRequestError(Exception):
    """Raised when the request is invalid."""

    pass


class ForbiddenError(Exception):
    """Raised when the request is forbidden."""

    pass


class NotFoundError(Exception):
    """Raised when the resource is not found."""

    pass


class MethodNotAllowedError(Exception):
    """Raised when the method is not allowed."""

    pass


class RateLimitError(Exception):
    """Raised when the rate limit is exceeded."""

    pass


class InternalServerError(Exception):
    """Raised when the server encounters an internal error."""

    pass


class BadGatewayError(Exception):
    """Raised when the server encounters a bad gateway."""

    pass


class ServiceUnavailableError(Exception):
    """Raised when the server is unavailable."""

    pass


class GatewayTimeoutError(Exception):
    """Raised when the server encounters a gateway timeout."""

    pass
