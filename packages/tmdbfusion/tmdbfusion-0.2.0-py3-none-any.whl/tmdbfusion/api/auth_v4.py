# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""V4 Authentication API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class V4RequestToken(typing.TypedDict):
    """V4 request token response."""

    success: bool
    status_code: int
    status_message: str
    request_token: str


class V4AccessToken(typing.TypedDict):
    """V4 access token response."""

    success: bool
    status_code: int
    status_message: str
    access_token: str
    account_id: str


class V4LogoutResponse(typing.TypedDict):
    """V4 logout response."""

    success: bool
    status_code: int
    status_message: str


class AuthV4API(BaseAPI):
    """
    Synchronous V4 Authentication API.

    Parameters
    ----------
    client : TMDBClient
        The TMDB client instance.
    """

    def __init__(self, client: TMDBClient) -> None:
        """
        Initialize the API.

        Parameters
        ----------
        client : TMDBClient
            The TMDB client instance.
        """
        super().__init__(client)

    def create_request_token(
        self,
        *,
        redirect_to: str | None = None,
    ) -> V4RequestToken:
        """
        Create a V4 request token.

        Parameters
        ----------
        redirect_to : str | None, optional
            The redirect URL after authorization.

        Returns
        -------
        V4RequestToken
            The V4RequestToken response.
        """
        body: dict[str, typing.Any] = {}
        if redirect_to:
            body["redirect_to"] = redirect_to
        return self._client._post(  # type: ignore[return-value]
            "/auth/request_token",
            dict[str, typing.Any],
            body=body,
            version=4,
        )

    def create_access_token(self, *, request_token: str) -> V4AccessToken:
        """
        Create a V4 access token from request token.

        Parameters
        ----------
        request_token : str
            The request token from authentication.

        Returns
        -------
        V4AccessToken
            The V4AccessToken response.
        """
        return self._client._post(  # type: ignore[return-value]
            "/auth/access_token",
            dict[str, typing.Any],
            body={"request_token": request_token},
            version=4,
        )

    def logout(self, *, access_token: str) -> V4LogoutResponse:
        """
        Delete an access token (logout).

        Parameters
        ----------
        access_token : str
            The access token.

        Returns
        -------
        V4LogoutResponse
            The V4LogoutResponse response.
        """
        return self._client._delete(  # type: ignore[return-value]
            "/auth/access_token",
            dict[str, typing.Any],
            body={"access_token": access_token},
            version=4,
        )


class AsyncAuthV4API(AsyncBaseAPI):
    """
    Asynchronous V4 Authentication API.

    Parameters
    ----------
    client : AsyncTMDBClient
        The TMDB client instance.
    """

    def __init__(self, client: AsyncTMDBClient) -> None:
        """
        Initialize the API.

        Parameters
        ----------
        client : TMDBClient
            The TMDB client instance.
        """
        super().__init__(client)

    async def create_request_token(
        self,
        *,
        redirect_to: str | None = None,
    ) -> V4RequestToken:
        """
        Create a V4 request token.

        Parameters
        ----------
        redirect_to : str | None, optional
            The redirect URL after authorization.

        Returns
        -------
        V4RequestToken
            The V4RequestToken response.
        """
        body: dict[str, typing.Any] = {}
        if redirect_to:
            body["redirect_to"] = redirect_to
        return await self._client._post(  # type: ignore[return-value]
            "/auth/request_token",
            dict[str, typing.Any],
            body=body,
            version=4,
        )

    async def create_access_token(
        self,
        *,
        request_token: str,
    ) -> V4AccessToken:
        """
        Create a V4 access token from request token.

        Parameters
        ----------
        request_token : str
            The request token from authentication.

        Returns
        -------
        V4AccessToken
            The V4AccessToken response.
        """
        return await self._client._post(  # type: ignore[return-value]
            "/auth/access_token",
            dict[str, typing.Any],
            body={"request_token": request_token},
            version=4,
        )

    async def logout(self, *, access_token: str) -> V4LogoutResponse:
        """
        Delete an access token (logout).

        Parameters
        ----------
        access_token : str
            The access token.

        Returns
        -------
        V4LogoutResponse
            The V4LogoutResponse response.
        """
        return await self._client._delete(  # type: ignore[return-value]
            "/auth/access_token",
            dict[str, typing.Any],
            body={"access_token": access_token},
            version=4,
        )
