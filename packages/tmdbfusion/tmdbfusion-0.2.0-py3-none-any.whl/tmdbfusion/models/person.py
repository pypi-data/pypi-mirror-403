# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Person and credits models."""

import msgspec


class Person(msgspec.Struct, frozen=True):
    """Person summary (from lists/search)."""

    id: int
    name: str
    adult: bool = False
    gender: int = 0
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None


class PersonDetails(msgspec.Struct, frozen=True):
    """Full person details."""

    id: int
    name: str
    adult: bool = False
    also_known_as: list[str] = []
    biography: str = ""
    birthday: str | None = None
    deathday: str | None = None
    gender: int = 0
    homepage: str | None = None
    imdb_id: str | None = None
    known_for_department: str = ""
    place_of_birth: str | None = None
    popularity: float = 0.0
    profile_path: str | None = None


class CastMember(msgspec.Struct, frozen=True):
    """Cast member in credits."""

    id: int
    name: str
    adult: bool = False
    cast_id: int = 0
    character: str = ""
    credit_id: str = ""
    gender: int = 0
    known_for_department: str = ""
    order: int = 0
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None


class CrewMember(msgspec.Struct, frozen=True):
    """Crew member in credits."""

    id: int
    name: str
    adult: bool = False
    credit_id: str = ""
    department: str = ""
    gender: int = 0
    job: str = ""
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None


class Credits(msgspec.Struct, frozen=True):
    """Credits response."""

    id: int
    cast: list[CastMember] = []
    crew: list[CrewMember] = []
