# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
TMDB API Exceptions.

All exception classes for TMDB API errors.
"""


class TMDBError(Exception):
    """Base exception for all TMDB API errors.

    Parameters
    ----------
    status_code : int
        TMDB API status code.
    message : str
        Error message.
    http_status : int
        HTTP status code.

    See Also
    --------
    AuthenticationError : Authentication failed.
    AuthorizationError : Authorization failed.
    NotFoundError : Resource not found.
    RateLimitError : Rate limit exceeded.
    ServerError : Server error.

    Examples
    --------
    >>> try:
    ...     raise TMDBError(401, "Invalid API key", 401)
    ... except TMDBError as e:
    ...     print(e)
    [401] Invalid API key
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        http_status: int,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.http_status = http_status
        super().__init__(f"[{status_code}] {message}")


class AuthenticationError(TMDBError):
    """Authentication failed (401).

    See Also
    --------
    TMDBError : Base exception for all TMDB API errors.

    Examples
    --------
    >>> try:
    ...     raise AuthenticationError(7, "Invalid API key: You must be granted a valid key.", 401)
    ... except AuthenticationError as e:
    ...     print(e)
    [7] Invalid API key: You must be granted a valid key.

    """


class AuthorizationError(TMDBError):
    """Authorization failed (403).

    See Also
    --------
    TMDBError : Base exception for all TMDB API errors.

    Examples
    --------
    >>> try:
    ...     raise AuthorizationError(
    ...         33,
    ...         "Invalid request token: The request token is either expired or invalid.",
    ...         401,
    ...     )
    ... except AuthorizationError as e:
    ...     print(e)
    [33] Invalid request token: The request token is either expired or invalid.

    """


class NotFoundError(TMDBError):
    """Resource not found (404).

    See Also
    --------
    TMDBError : Base exception for all TMDB API errors.

    Examples
    --------
    >>> try:
    ...     raise NotFoundError(34, "The resource you requested could not be found.", 404)
    ... except NotFoundError as e:
    ...     print(e)
    [34] The resource you requested could not be found.

    """


class RateLimitError(TMDBError):
    """Rate limit exceeded (429).

    Parameters
    ----------
    status_code : int
        TMDB API status code.
    message : str
        Error message.
    http_status : int
        HTTP status code.
    retry_after : int | None
        Seconds to wait before retrying.

    See Also
    --------
    TMDBError : Base exception for all TMDB API errors.

    Examples
    --------
    >>> try:
    ...     raise RateLimitError(
    ...         25,
    ...         "Your request count (#) is over the allowed limit of (40).",
    ...         429,
    ...         retry_after=10,
    ...     )
    ... except RateLimitError as e:
    ...     print(e.retry_after)
    10

    """

    def __init__(
        self,
        status_code: int,
        message: str,
        http_status: int,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(status_code, message, http_status)
        self.retry_after = retry_after


class ServerError(TMDBError):
    """Server error (5xx).

    See Also
    --------
    TMDBError : Base exception for all TMDB API errors.

    Examples
    --------
    >>> try:
    ...     raise ServerError(500, "Internal Server Error", 500)
    ... except ServerError as e:
    ...     print(e)
    [500] Internal Server Error

    """
