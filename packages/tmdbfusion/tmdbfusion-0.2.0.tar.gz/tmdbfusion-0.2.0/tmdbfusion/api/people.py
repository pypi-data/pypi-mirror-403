# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""People API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.person import PersonDetails
from tmdbfusion.models.responses import ChangesResponse
from tmdbfusion.models.responses import ExternalIdsResponse
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import TranslationsResponse
from tmdbfusion.models.search import MoviePaginatedResponse
from tmdbfusion.models.search import PersonPaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class PeopleAPI(BaseAPI):
    """
    Synchronous People API.

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

    def details(
        self,
        person_id: int,
        *,
        append_to_response: str | None = None,
    ) -> PersonDetails:
        """
        Get person details.

        Parameters
        ----------
        person_id : int
            The person ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        PersonDetails
            The PersonDetails response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._client._get(
            f"/person/{person_id}",
            PersonDetails,
            params=params,
        )

    def popular(self, *, page: int = 1) -> PersonPaginatedResponse:
        """
        Get popular people.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return self._client._get(
            "/person/popular",
            PersonPaginatedResponse,
            params={"page": page},
        )

    def movie_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's movie credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/person/{person_id}/movie_credits",
            dict[str, typing.Any],
        )

    def tv_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's TV credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/person/{person_id}/tv_credits",
            dict[str, typing.Any],
        )

    def combined_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's combined credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/person/{person_id}/combined_credits",
            dict[str, typing.Any],
        )

    def external_ids(self, person_id: int) -> ExternalIdsResponse:
        """
        Get person's external IDs.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return self._client._get(
            f"/person/{person_id}/external_ids",
            ExternalIdsResponse,
        )

    def images(self, person_id: int) -> ImagesResponse:
        """
        Get person's images.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return self._client._get(
            f"/person/{person_id}/images",
            ImagesResponse,
        )

    def translations(self, person_id: int) -> TranslationsResponse:
        """
        Get person's translations.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/person/{person_id}/translations",
            TranslationsResponse,
        )

    def changes(
        self,
        person_id: int,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesResponse:
        """
        Get person's changes.

        Parameters
        ----------
        person_id : int
            The person ID.
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesResponse
            The changes.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._get(
            f"/person/{person_id}/changes",
            ChangesResponse,
            params=params,
        )

    def tagged_images(
        self,
        person_id: int,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get person's tagged images.

        Parameters
        ----------
        person_id : int
            The person ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/person/{person_id}/tagged_images",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def latest(self) -> PersonDetails:
        """
        Get latest person.

        Returns
        -------
        PersonDetails
            The PersonDetails response.
        """
        return self._client._get(
            "/person/latest",
            PersonDetails,
            include_language=False,
        )


class AsyncPeopleAPI(AsyncBaseAPI):
    """
    Asynchronous People API.

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

    async def details(
        self,
        person_id: int,
        *,
        append_to_response: str | None = None,
    ) -> PersonDetails:
        """
        Get person details.

        Parameters
        ----------
        person_id : int
            The person ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        PersonDetails
            The PersonDetails response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return await self._client._get(
            f"/person/{person_id}",
            PersonDetails,
            params=params,
        )

    async def popular(self, *, page: int = 1) -> PersonPaginatedResponse:
        """
        Get popular people.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return await self._client._get(
            "/person/popular",
            PersonPaginatedResponse,
            params={"page": page},
        )

    async def movie_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's movie credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/person/{person_id}/movie_credits",
            dict[str, typing.Any],
        )

    async def tv_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's TV credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/person/{person_id}/tv_credits",
            dict[str, typing.Any],
        )

    async def combined_credits(self, person_id: int) -> dict[str, typing.Any]:
        """
        Get person's combined credits.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/person/{person_id}/combined_credits",
            dict[str, typing.Any],
        )

    async def external_ids(self, person_id: int) -> ExternalIdsResponse:
        """
        Get person's external IDs.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return await self._client._get(
            f"/person/{person_id}/external_ids",
            ExternalIdsResponse,
        )

    async def images(self, person_id: int) -> ImagesResponse:
        """
        Get person's images.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/person/{person_id}/images",
            ImagesResponse,
        )

    async def translations(self, person_id: int) -> TranslationsResponse:
        """
        Get person's translations.

        Parameters
        ----------
        person_id : int
            The person ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return await self._client._get(
            f"/person/{person_id}/translations",
            TranslationsResponse,
        )

    async def changes(
        self,
        person_id: int,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesResponse:
        """
        Get person's changes.

        Parameters
        ----------
        person_id : int
            The person ID.
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesResponse
            The changes.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._client._get(
            f"/person/{person_id}/changes",
            ChangesResponse,
            params=params,
        )

    async def latest(self) -> PersonDetails:
        """
        Get latest person.

        Returns
        -------
        PersonDetails
            The PersonDetails response.
        """
        return await self._client._get(
            "/person/latest",
            PersonDetails,
            include_language=False,
        )
