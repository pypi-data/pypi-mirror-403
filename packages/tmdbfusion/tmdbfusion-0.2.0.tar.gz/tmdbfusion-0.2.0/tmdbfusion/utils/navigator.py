# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Relationship Navigator.

Traverse the TMDB graph (movies → actors → other movies) with chainable
helpers using lazy evaluation.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from dataclasses import field


if typing.TYPE_CHECKING:
    from tmdbfusion.core.sync_client import TMDBClient
    from tmdbfusion.models.common import CastMember
    from tmdbfusion.models.common import CrewMember

T = typing.TypeVar("T")


@dataclass
class PersonRef:
    """Reference to a person in the graph.

    Attributes
    ----------
    id : int
        Person ID.
    name : str
        Person name.
    job : str | None
        Job title (for crew).

    """

    id: int
    name: str
    job: str | None = None


@dataclass
class MediaRef:
    """Reference to a movie or TV show.

    Attributes
    ----------
    id : int
        Media ID.
    title : str
        Title or name.
    media_type : str
        Either "movie" or "tv".
    year : int | None
        Release/air year.

    """

    id: int
    title: str
    media_type: str
    year: int | None = None


class PersonSet:
    """Set of people with set operations.

    Parameters
    ----------
    people : list[PersonRef]
        Initial list of people.

    """

    def __init__(self, people: list[PersonRef]) -> None:
        self._people = people

    def __iter__(self) -> typing.Iterator[PersonRef]:
        """Iterate over people.

        Yields
        ------
        PersonRef
            Each person.

        """
        yield from self._people

    def __len__(self) -> int:
        """Get count.

        Returns
        -------
        int
            Number of people.

        """
        return len(self._people)

    def intersect(self, other: PersonSet) -> PersonSet:
        """Find people in both sets.

        Parameters
        ----------
        other : PersonSet
            Other set to intersect with.

        Returns
        -------
        PersonSet
            People appearing in both.

        """
        other_ids = {p.id for p in other}
        return PersonSet([p for p in self._people if p.id in other_ids])

    def union(self, other: PersonSet) -> PersonSet:
        """Combine both sets.

        Parameters
        ----------
        other : PersonSet
            Other set to combine.

        Returns
        -------
        PersonSet
            All unique people.

        """
        seen: set[int] = set()
        result: list[PersonRef] = []
        for p in [*self._people, *list(other)]:
            if p.id not in seen:
                seen.add(p.id)
                result.append(p)
        return PersonSet(result)

    def difference(self, other: PersonSet) -> PersonSet:
        """Find people in self but not other.

        Parameters
        ----------
        other : PersonSet
            Set to subtract.

        Returns
        -------
        PersonSet
            People only in self.

        """
        other_ids = {p.id for p in other}
        return PersonSet([p for p in self._people if p.id not in other_ids])

    def to_list(self) -> list[PersonRef]:
        """Convert to list.

        Returns
        -------
        list[PersonRef]
            List of people.

        """
        return list(self._people)


class MediaSet:
    """Set of media items with set operations.

    Parameters
    ----------
    media : list[MediaRef]
        Initial list of media.

    """

    def __init__(self, media: list[MediaRef]) -> None:
        self._media = media

    def __iter__(self) -> typing.Iterator[MediaRef]:
        """Iterate over media.

        Yields
        ------
        MediaRef
            Each media item.

        """
        yield from self._media

    def __len__(self) -> int:
        """Get count.

        Returns
        -------
        int
            Number of media items.

        """
        return len(self._media)

    def sort_by(self, key: str, *, reverse: bool = True) -> MediaSet:
        """Sort media by attribute.

        Parameters
        ----------
        key : str
            Attribute to sort by ("year", "title").
        reverse : bool
            Descending order if True.

        Returns
        -------
        MediaSet
            Sorted set.

        """
        sorted_media = sorted(
            self._media,
            key=lambda m: getattr(m, key, 0) or 0,
            reverse=reverse,
        )
        return MediaSet(sorted_media)

    def chronological(self) -> MediaSet:
        """Sort by year ascending.

        Returns
        -------
        MediaSet
            Chronologically sorted.

        """
        return self.sort_by("year", reverse=False)

    def movies_only(self) -> MediaSet:
        """Filter to movies only.

        Returns
        -------
        MediaSet
            Only movies.

        """
        return MediaSet([m for m in self._media if m.media_type == "movie"])

    def tv_only(self) -> MediaSet:
        """Filter to TV only.

        Returns
        -------
        MediaSet
            Only TV shows.

        """
        return MediaSet([m for m in self._media if m.media_type == "tv"])

    def to_list(self) -> list[MediaRef]:
        """Convert to list.

        Returns
        -------
        list[MediaRef]
            List of media.

        """
        return list(self._media)


@dataclass
class MovieNavigator:
    """Navigator starting from a movie.

    Attributes
    ----------
    client : TMDBClient
        TMDB client.
    movie_id : int
        Movie ID.

    """

    client: TMDBClient
    movie_id: int
    _credits: object | None = field(default=None, repr=False)

    def _fetch_credits(self) -> None:
        """Fetch credits if not cached."""
        if self._credits is None:
            self._credits = self.client.movies.credits(self.movie_id)

    def cast(self) -> PersonSet:
        """Get cast members.

        Returns
        -------
        PersonSet
            Set of cast.

        """
        self._fetch_credits()
        credits = self._credits
        cast_list: list[CastMember] = getattr(credits, "cast", [])
        return PersonSet([PersonRef(id=c.id, name=c.name or "") for c in cast_list])

    def crew(self, *, job: str | None = None) -> PersonSet:
        """Get crew members, optionally filtered by job.

        Parameters
        ----------
        job : str | None
            Filter by job title (e.g., "Director").

        Returns
        -------
        PersonSet
            Set of crew.

        """
        self._fetch_credits()
        credits = self._credits
        crew_list: list[CrewMember] = getattr(credits, "crew", [])
        if job:
            crew_list = [c for c in crew_list if c.job == job]
        return PersonSet([PersonRef(id=c.id, name=c.name or "", job=c.job) for c in crew_list])

    def directors(self) -> PersonSet:
        """Get directors.

        Returns
        -------
        PersonSet
            Set of directors.

        """
        return self.crew(job="Director")


@dataclass
class PersonNavigator:
    """Navigator starting from a person.

    Attributes
    ----------
    client : TMDBClient
        TMDB client.
    person_id : int
        Person ID.

    """

    client: TMDBClient
    person_id: int

    def movie_credits(self) -> MediaSet:
        """Get movies the person worked on.

        Returns
        -------
        MediaSet
            Set of movies.

        """
        credits = self.client.people.movie_credits(self.person_id)
        cast_list = getattr(credits, "cast", [])
        crew_list = getattr(credits, "crew", [])
        all_movies: list[MediaRef] = []
        seen: set[int] = set()

        for m in [*cast_list, *crew_list]:
            if m.id not in seen:
                seen.add(m.id)
                year = None
                rd = getattr(m, "release_date", None)
                if rd:
                    year = int(rd[:4]) if len(rd) >= 4 else None
                title = getattr(m, "title", "") or ""
                all_movies.append(
                    MediaRef(
                        id=m.id,
                        title=title,
                        media_type="movie",
                        year=year,
                    )
                )

        return MediaSet(all_movies)

    def directed_movies(self) -> MediaSet:
        """Get movies directed by this person.

        Returns
        -------
        MediaSet
            Set of directed movies.

        """
        credits = self.client.people.movie_credits(self.person_id)
        crew_list = getattr(credits, "crew", [])
        movies: list[MediaRef] = []

        for m in crew_list:
            if getattr(m, "job", None) == "Director":
                year = None
                rd = getattr(m, "release_date", None)
                if rd:
                    year = int(rd[:4]) if len(rd) >= 4 else None
                title = getattr(m, "title", "") or ""
                movies.append(
                    MediaRef(
                        id=m.id,
                        title=title,
                        media_type="movie",
                        year=year,
                    )
                )

        return MediaSet(movies)


@dataclass
class CollectionNavigator:
    """Navigator starting from a collection.

    Attributes
    ----------
    client : TMDBClient
        TMDB client.
    collection_id : int
        Collection ID.

    """

    client: TMDBClient
    collection_id: int

    def movies(self) -> MediaSet:
        """Get movies in the collection.

        Returns
        -------
        MediaSet
            Set of movies in collection.

        """
        details = self.client.collections.details(self.collection_id)
        parts = getattr(details, "parts", [])
        movies: list[MediaRef] = []

        for m in parts:
            year = None
            rd = getattr(m, "release_date", None)
            if rd:
                year = int(rd[:4]) if len(rd) >= 4 else None
            title = getattr(m, "title", "") or ""
            movies.append(
                MediaRef(
                    id=m.id,
                    title=title,
                    media_type="movie",
                    year=year,
                )
            )

        return MediaSet(movies)


class Navigator:
    """Entry point for graph navigation.

    Examples
    --------
    >>> nav = Navigator(client)
    >>> common = nav.movie(550).cast().intersect(nav.movie(680).cast())
    >>> nolan = nav.person(525).directed_movies().chronological()

    Parameters
    ----------
    client : TMDBClient
        TMDB client instance.

    """

    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def movie(self, movie_id: int) -> MovieNavigator:
        """Start navigation from a movie.

        Parameters
        ----------
        movie_id : int
            Movie ID.

        Returns
        -------
        MovieNavigator
            Movie navigator.

        """
        return MovieNavigator(client=self._client, movie_id=movie_id)

    def person(self, person_id: int) -> PersonNavigator:
        """Start navigation from a person.

        Parameters
        ----------
        person_id : int
            Person ID.

        Returns
        -------
        PersonNavigator
            Person navigator.

        """
        return PersonNavigator(client=self._client, person_id=person_id)

    def collection(self, collection_id: int) -> CollectionNavigator:
        """Start navigation from a collection.

        Parameters
        ----------
        collection_id : int
            Collection ID.

        Returns
        -------
        CollectionNavigator
            Collection navigator.

        """
        return CollectionNavigator(
            client=self._client,
            collection_id=collection_id,
        )
