# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
TMDB Models.

All data models for TMDB API responses.
"""

from tmdbfusion.models.common import Genre
from tmdbfusion.models.common import Image
from tmdbfusion.models.common import Keyword
from tmdbfusion.models.common import ProductionCompany
from tmdbfusion.models.common import ProductionCountry
from tmdbfusion.models.common import SpokenLanguage
from tmdbfusion.models.common import Video
from tmdbfusion.models.movie import Movie
from tmdbfusion.models.movie import MovieDetails
from tmdbfusion.models.person import CastMember
from tmdbfusion.models.person import CrewMember
from tmdbfusion.models.person import Person
from tmdbfusion.models.person import PersonDetails
from tmdbfusion.models.search import MovieSearchResult
from tmdbfusion.models.search import MultiSearchResult
from tmdbfusion.models.search import PersonSearchResult
from tmdbfusion.models.search import TVSearchResult
from tmdbfusion.models.tv import TVEpisode
from tmdbfusion.models.tv import TVSeason
from tmdbfusion.models.tv import TVSeries
from tmdbfusion.models.tv import TVSeriesDetails


__all__ = [
    "CastMember",
    "CrewMember",
    # Common
    "Genre",
    "Image",
    "Keyword",
    # Movie
    "Movie",
    "MovieDetails",
    # Search
    "MovieSearchResult",
    "MultiSearchResult",
    # Person
    "Person",
    "PersonDetails",
    "PersonSearchResult",
    "ProductionCompany",
    "ProductionCountry",
    "SpokenLanguage",
    "TVEpisode",
    "TVSearchResult",
    "TVSeason",
    # TV
    "TVSeries",
    "TVSeriesDetails",
    "Video",
]
