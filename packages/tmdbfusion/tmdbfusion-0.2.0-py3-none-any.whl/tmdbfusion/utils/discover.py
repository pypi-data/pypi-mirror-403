# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Utility classes."""

from __future__ import annotations

import typing


class DiscoverBuilder:
    """Builder for Discover API queries.

    Examples
    --------
    >>> builder = DiscoverBuilder()
    >>> params = builder.sort_by("popularity.desc").page(2).build()
    >>> client.discover.movie(**params)

    """

    def __init__(self) -> None:
        self._params: dict[str, typing.Any] = {}

    def build(self) -> dict[str, typing.Any]:
        """Build parameters dictionary.

        Returns
        -------
        dict[str, typing.Any]
            Parameters for Discover API.

        """
        return self._params.copy()

    def sort_by(self, value: str) -> typing.Self:
        """Set sort_by parameter.

        Parameters
        ----------
        value : str
            Sort order (e.g., "popularity.desc").

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["sort_by"] = value
        return self

    def page(self, value: int) -> typing.Self:
        """Set page parameter.

        Parameters
        ----------
        value : int
            Page number.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["page"] = value
        return self

    def year(self, value: int) -> typing.Self:
        """Set year parameter (movies only).

        Parameters
        ----------
        value : int
            Release year.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["year"] = value
        return self

    def with_genres(self, value: str | list[str]) -> typing.Self:
        """Set with_genres parameter.

        Parameters
        ----------
        value : str | list[str]
            Genre ID(s) or comma-separated string.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        if isinstance(value, list):
            self._params["with_genres"] = ",".join(value)
        else:
            self._params["with_genres"] = value
        return self

    def without_genres(self, value: str | list[str]) -> typing.Self:
        """Set without_genres parameter.

        Parameters
        ----------
        value : str | list[str]
            Genre ID(s) or comma-separated string.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        if isinstance(value, list):
            self._params["without_genres"] = ",".join(value)
        else:
            self._params["without_genres"] = value
        return self

    def with_keywords(self, value: str | list[str]) -> typing.Self:
        """Set with_keywords parameter.

        Parameters
        ----------
        value : str | list[str]
            Keyword ID(s) or comma-separated string.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        if isinstance(value, list):
            self._params["with_keywords"] = ",".join(value)
        else:
            self._params["with_keywords"] = value
        return self

    def first_air_date_year(self, value: int) -> typing.Self:
        """Set first_air_date_year parameter (TV only).

        Parameters
        ----------
        value : int
            First air date year.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["first_air_date_year"] = value
        return self

    def language(self, value: str) -> typing.Self:
        """Set language parameter.

        Parameters
        ----------
        value : str
            Language code (e.g., "en-US").

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["language"] = value
        return self

    def region(self, value: str) -> typing.Self:
        """Set region parameter.

        Parameters
        ----------
        value : str
            Region code (e.g., "US").

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["region"] = value
        return self

    def include_adult(self, *, value: bool = True) -> typing.Self:
        """Set include_adult parameter.

        Parameters
        ----------
        value : bool
            Whether to include adult content.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["include_adult"] = value
        return self

    def include_video(self, *, value: bool = True) -> typing.Self:
        """Set include_video parameter.

        Parameters
        ----------
        value : bool
            Whether to include video content.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["include_video"] = value
        return self

    def primary_release_year(self, value: int) -> typing.Self:
        """Set primary_release_year parameter.

        Parameters
        ----------
        value : int
            Primary release year.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["primary_release_year"] = value
        return self

    def primary_release_date_gte(self, value: str) -> typing.Self:
        """Set primary_release_date.gte parameter.

        Parameters
        ----------
        value : str
            Date string (YYYY-MM-DD).

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["primary_release_date.gte"] = value
        return self

    def primary_release_date_lte(self, value: str) -> typing.Self:
        """Set primary_release_date.lte parameter.

        Parameters
        ----------
        value : str
            Date string (YYYY-MM-DD).

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["primary_release_date.lte"] = value
        return self

    def vote_count_gte(self, value: int) -> typing.Self:
        """Set vote_count.gte parameter.

        Parameters
        ----------
        value : int
            Minimum vote count.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["vote_count.gte"] = value
        return self

    def vote_average_gte(self, value: float) -> typing.Self:
        """Set vote_average.gte parameter.

        Parameters
        ----------
        value : float
            Minimum vote average.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["vote_average.gte"] = value
        return self

    def with_runtime_gte(self, value: int) -> typing.Self:
        """Set with_runtime.gte parameter.

        Parameters
        ----------
        value : int
            Minimum runtime in minutes.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["with_runtime.gte"] = value
        return self

    def with_runtime_lte(self, value: int) -> typing.Self:
        """Set with_runtime.lte parameter.

        Parameters
        ----------
        value : int
            Maximum runtime in minutes.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["with_runtime.lte"] = value
        return self

    def with_companies(self, value: str | list[str]) -> typing.Self:
        """Set with_companies parameter.

        Parameters
        ----------
        value : str | list[str]
            Company ID(s) or comma-separated string.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        if isinstance(value, list):
            self._params["with_companies"] = ",".join(value)
        else:
            self._params["with_companies"] = value
        return self

    def with_watch_providers(self, value: str | list[str]) -> typing.Self:
        """Set with_watch_providers parameter.

        Parameters
        ----------
        value : str | list[str]
            Provider ID(s) or pipe-separated string.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        if isinstance(value, list):
            self._params["with_watch_providers"] = "|".join(value)
        else:
            self._params["with_watch_providers"] = value
        return self

    def watch_region(self, value: str) -> typing.Self:
        """Set watch_region parameter.

        Parameters
        ----------
        value : str
            Region code.

        Returns
        -------
        typing.Self
            Builder instance.

        """
        self._params["watch_region"] = value
        return self


class StdOutLogger:
    """Simple logger that prints to stdout."""

    def __call__(self, method: str, url: str, status_code: int) -> None:
        """Log request details.

        Parameters
        ----------
        method : str
            HTTP method.
        url : str
            Request URL.
        status_code : int
            Response status code.

        Returns
        -------
        None

        """
