# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for navigator module."""

from tmdbfusion.utils.navigator import MediaRef
from tmdbfusion.utils.navigator import MediaSet
from tmdbfusion.utils.navigator import PersonRef
from tmdbfusion.utils.navigator import PersonSet


class TestPersonSet:
    """Tests for PersonSet operations."""

    def test_len(self) -> None:
        """Test length."""
        people = [PersonRef(id=1, name="A"), PersonRef(id=2, name="B")]
        ps = PersonSet(people)
        assert len(ps) == 2

    def test_intersect(self) -> None:
        """Test intersection."""
        set1 = PersonSet([PersonRef(1, "A"), PersonRef(2, "B")])
        set2 = PersonSet([PersonRef(2, "B"), PersonRef(3, "C")])
        result = set1.intersect(set2)
        assert len(result) == 1
        assert result.to_list()[0].id == 2

    def test_union(self) -> None:
        """Test union."""
        set1 = PersonSet([PersonRef(1, "A")])
        set2 = PersonSet([PersonRef(2, "B")])
        result = set1.union(set2)
        assert len(result) == 2

    def test_difference(self) -> None:
        """Test difference."""
        set1 = PersonSet([PersonRef(1, "A"), PersonRef(2, "B")])
        set2 = PersonSet([PersonRef(2, "B")])
        result = set1.difference(set2)
        assert len(result) == 1
        assert result.to_list()[0].id == 1


class TestMediaSet:
    """Tests for MediaSet operations."""

    def test_sort_by_year(self) -> None:
        """Test sorting by year."""
        media = [
            MediaRef(1, "Old", "movie", 1990),
            MediaRef(2, "New", "movie", 2020),
        ]
        ms = MediaSet(media)
        sorted_ms = ms.sort_by("year", reverse=True)
        items = sorted_ms.to_list()
        assert items[0].year == 2020
        assert items[1].year == 1990

    def test_chronological(self) -> None:
        """Test chronological sorting."""
        media = [
            MediaRef(1, "New", "movie", 2020),
            MediaRef(2, "Old", "movie", 1990),
        ]
        ms = MediaSet(media)
        chron = ms.chronological()
        assert chron.to_list()[0].year == 1990

    def test_movies_only(self) -> None:
        """Test filtering movies."""
        media = [
            MediaRef(1, "Movie", "movie", 2020),
            MediaRef(2, "Show", "tv", 2020),
        ]
        ms = MediaSet(media)
        movies = ms.movies_only()
        assert len(movies) == 1
        assert movies.to_list()[0].media_type == "movie"

    def test_tv_only(self) -> None:
        """Test filtering TV."""
        media = [
            MediaRef(1, "Movie", "movie", 2020),
            MediaRef(2, "Show", "tv", 2020),
        ]
        ms = MediaSet(media)
        tv = ms.tv_only()
        assert len(tv) == 1
        assert tv.to_list()[0].media_type == "tv"
