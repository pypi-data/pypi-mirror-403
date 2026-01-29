# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV aggregate credits and extra responses."""

import typing

import msgspec


class AggregateCastRole(msgspec.Struct, frozen=True):
    """Aggregate cast role."""

    credit_id: str
    character: str
    episode_count: int = 0


class AggregateCastMember(msgspec.Struct, frozen=True):
    """Aggregate cast member."""

    id: int
    name: str
    adult: bool = False
    gender: int = 0
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None
    roles: list[AggregateCastRole] = []
    total_episode_count: int = 0
    order: int = 0


class AggregateCrewJob(msgspec.Struct, frozen=True):
    """Aggregate crew job."""

    credit_id: str
    job: str
    episode_count: int = 0


class AggregateCrewMember(msgspec.Struct, frozen=True):
    """Aggregate crew member."""

    id: int
    name: str
    adult: bool = False
    gender: int = 0
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None
    department: str = ""
    jobs: list[AggregateCrewJob] = []
    total_episode_count: int = 0


class AggregateCreditsResponse(msgspec.Struct, frozen=True):
    """Aggregate credits response."""

    id: int
    cast: list[AggregateCastMember] = []
    crew: list[AggregateCrewMember] = []


class EpisodeGroup(msgspec.Struct, frozen=True):
    """Episode group."""

    id: str
    name: str
    description: str = ""
    episode_count: int = 0
    group_count: int = 0
    type: int = 0
    network: typing.Any = None


class EpisodeGroupsResponse(msgspec.Struct, frozen=True):
    """Episode groups response."""

    id: int
    results: list[EpisodeGroup] = []


class ScreenedTheatricallyResult(msgspec.Struct, frozen=True):
    """Screened theatrically result."""

    id: int
    episode_number: int
    season_number: int


class ScreenedTheatricallyResponse(msgspec.Struct, frozen=True):
    """Screened theatrically response."""

    id: int
    results: list[ScreenedTheatricallyResult] = []


class ListDetails(msgspec.Struct, frozen=True):
    """List details."""

    id: int
    name: str
    description: str = ""
    created_by: str = ""
    favorite_count: int = 0
    item_count: int = 0
    iso_639_1: str = ""
    poster_path: str | None = None
    items: list[typing.Any] = []


class ListItemStatus(msgspec.Struct, frozen=True):
    """List item status."""

    id: int
    item_present: bool = False
