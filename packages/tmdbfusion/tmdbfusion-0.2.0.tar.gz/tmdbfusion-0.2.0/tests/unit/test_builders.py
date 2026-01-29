"""Unit tests for the DiscoverBuilder."""

from tmdbfusion.utils.discover import DiscoverBuilder


def test_builder_defaults():
    builder = DiscoverBuilder()
    params = builder.build()
    assert params == {}


def test_builder_chaining():
    builder = DiscoverBuilder()
    params = builder.page(2).sort_by("popularity.desc").year(1999).build()

    assert params["page"] == 2
    assert params["sort_by"] == "popularity.desc"
    assert params["year"] == 1999


def test_list_handling():
    builder = DiscoverBuilder()
    params = (
        builder.with_genres(["28", "12"])
        .with_watch_providers(["8", "9"])
        .without_genres(["1", "2"])
        .with_keywords(["kw1", "kw2"])
        .with_companies(["c1", "c2"])
        .build()
    )

    assert params["with_genres"] == "28,12"
    assert params["with_watch_providers"] == "8|9"
    assert params["without_genres"] == "1,2"
    assert params["with_keywords"] == "kw1,kw2"
    assert params["with_companies"] == "c1,c2"


def test_single_value_lists():
    builder = DiscoverBuilder()
    params = (
        builder.with_genres("28")
        .without_genres("1")
        .with_keywords("kw1")
        .with_companies("c1")
        .with_watch_providers("8")
        .build()
    )
    assert params["with_genres"] == "28"
    assert params["without_genres"] == "1"
    assert params["with_keywords"] == "kw1"
    assert params["with_companies"] == "c1"
    assert params["with_watch_providers"] == "8"


def test_all_other_methods():
    builder = DiscoverBuilder()
    params = (
        builder.first_air_date_year(2020)
        .language("fr-FR")
        .region("FR")
        .include_adult(value=True)
        .include_video(value=False)
        .primary_release_year(2021)
        .primary_release_date_gte("2021-01-01")
        .primary_release_date_lte("2021-12-31")
        .vote_count_gte(100)
        .vote_average_gte(7.5)
        .with_runtime_gte(90)
        .with_runtime_lte(180)
        .watch_region("US")
        .build()
    )

    assert params["first_air_date_year"] == 2020
    assert params["language"] == "fr-FR"
    assert params["region"] == "FR"
    assert params["include_adult"] is True
    assert params["include_video"] is False
    assert params["primary_release_year"] == 2021
    assert params["primary_release_date.gte"] == "2021-01-01"
    assert params["primary_release_date.lte"] == "2021-12-31"
    assert params["vote_count.gte"] == 100
    assert params["vote_average.gte"] == 7.5
    assert params["with_runtime.gte"] == 90
    assert params["with_runtime.lte"] == 180
    assert params["watch_region"] == "US"
