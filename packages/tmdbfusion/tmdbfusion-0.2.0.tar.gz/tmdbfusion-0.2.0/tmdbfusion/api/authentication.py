# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Authentication API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import RequestToken
from tmdbfusion.models.responses import Session
from tmdbfusion.models.responses import StatusResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class AuthenticationAPI(BaseAPI):
    """
    Synchronous Authentication API.

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

    def create_guest_session(self) -> Session:
        """
        Create a guest session.

        Returns
        -------
        Session
            The Session response.
        """
        return self._client._get(
            "/authentication/guest_session/new",
            Session,
            include_language=False,
        )

    def create_request_token(self) -> RequestToken:
        """
        Create a request token.

        Returns
        -------
        RequestToken
            The RequestToken response.
        """
        return self._client._get(
            "/authentication/token/new",
            RequestToken,
            include_language=False,
        )

    def create_session(self, *, request_token: str) -> Session:
        """
        Create a session from a request token.

        Parameters
        ----------
        request_token : str
            The request token from authentication.

        Returns
        -------
        Session
            The Session response.
        """
        return self._client._post(
            "/authentication/session/new",
            Session,
            body={"request_token": request_token},
        )

    def create_session_with_login(
        self,
        *,
        username: str,
        password: str,
        request_token: str,
    ) -> RequestToken:
        """
        Validate token with login credentials.

        Parameters
        ----------
        username : str
            The TMDB username.
        password : str
            The TMDB password.
        request_token : str
            The request token from authentication.

        Returns
        -------
        RequestToken
            The RequestToken response.
        """
        return self._client._post(
            "/authentication/token/validate_with_login",
            RequestToken,
            body={
                "username": username,
                "password": password,
                "request_token": request_token,
            },
        )

    def create_session_from_v4(self, *, access_token: str) -> Session:
        """
        Create session from v4 access token.

        Parameters
        ----------
        access_token : str
            The access token.

        Returns
        -------
        Session
            The Session response.
        """
        return self._client._post(
            "/authentication/session/convert/4",
            Session,
            body={"access_token": access_token},
        )

    def delete_session(self, *, session_id: str) -> StatusResponse:
        """
        Delete a session.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._delete(
            "/authentication/session",
            StatusResponse,
            body={"session_id": session_id},
        )

    def validate_key(self) -> StatusResponse:
        """
        Validate API key.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._get(
            "/authentication",
            StatusResponse,
            include_language=False,
        )


class AsyncAuthenticationAPI(AsyncBaseAPI):
    """
    Asynchronous Authentication API.

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

    async def create_guest_session(self) -> Session:
        """
        Create a guest session.

        Returns
        -------
        Session
            The Session response.
        """
        return await self._client._get(
            "/authentication/guest_session/new",
            Session,
            include_language=False,
        )

    async def create_request_token(self) -> RequestToken:
        """
        Create a request token.

        Returns
        -------
        RequestToken
            The RequestToken response.
        """
        return await self._client._get(
            "/authentication/token/new",
            RequestToken,
            include_language=False,
        )

    async def create_session(self, *, request_token: str) -> Session:
        """
        Create a session from a request token.

        Parameters
        ----------
        request_token : str
            The request token from authentication.

        Returns
        -------
        Session
            The Session response.
        """
        return await self._client._post(
            "/authentication/session/new",
            Session,
            body={"request_token": request_token},
        )

    async def delete_session(self, *, session_id: str) -> StatusResponse:
        """
        Delete a session.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._delete(
            "/authentication/session",
            StatusResponse,
            body={"session_id": session_id},
        )
