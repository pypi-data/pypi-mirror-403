# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Image Downloader.

Download TMDB images in bulk with validation and organization.
"""

from __future__ import annotations

import asyncio
import logging
import typing
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


if typing.TYPE_CHECKING:
    from tmdbfusion.core.async_client import AsyncTMDBClient
    from tmdbfusion.core.sync_client import TMDBClient

logger = logging.getLogger("tmdbfusion.download")


@dataclass
class DownloadResult:
    """Result from image download.

    Attributes
    ----------
    path : Path
        Path where image was saved.
    success : bool
        Whether download succeeded.
    error : str | None
        Error message if failed.

    """

    path: Path
    success: bool
    error: str | None = None


@dataclass
class BulkDownloadResult:
    """Result from bulk download operation.

    Attributes
    ----------
    successful : list[DownloadResult]
        Successfully downloaded files.
    failed : list[DownloadResult]
        Failed downloads.

    """

    successful: list[DownloadResult] = field(default_factory=list)
    failed: list[DownloadResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Get number of successful downloads.

        Returns
        -------
        int
            Success count.

        """
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Get number of failed downloads.

        Returns
        -------
        int
            Failure count.

        """
        return len(self.failed)


class ImageDownloader:
    """Download TMDB images with organization.

    Examples
    --------
    >>> downloader = ImageDownloader(client, output_dir="./posters")
    >>> downloader.poster(movie_id=550, size="w500")
    >>> downloader.bulk_posters([550, 551, 552])

    Parameters
    ----------
    client : TMDBClient
        TMDB client instance.
    output_dir : str | Path
        Directory to save images.

    """

    def __init__(
        self,
        client: TMDBClient,
        output_dir: str | Path = "./images",
    ) -> None:
        self._client = client
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def poster(
        self,
        movie_id: int,
        *,
        size: str = "w500",
        filename: str | None = None,
        skip_existing: bool = True,
    ) -> DownloadResult:
        """Download movie poster.

        Parameters
        ----------
        movie_id : int
            Movie ID.
        size : str
            Image size (e.g., "w185", "w500", "original").
        filename : str | None
            Custom filename (auto-generated if None).
        skip_existing : bool
            Skip if file already exists.

        Returns
        -------
        DownloadResult
            Download result.

        """
        details = self._client.movies.details(movie_id)
        poster_path = getattr(details, "poster_path", None)
        title = getattr(details, "title", f"movie_{movie_id}")

        if poster_path is None:
            out = self._output_dir / (filename or f"{movie_id}.jpg")
            return DownloadResult(
                path=out,
                success=False,
                error="No poster available",
            )

        if filename is None:
            safe_title = self._safe_filename(title)
            filename = f"{safe_title}_{movie_id}.jpg"

        return self._download_image(
            image_path=poster_path,
            size=size,
            filename=filename,
            skip_existing=skip_existing,
        )

    def backdrop(
        self,
        movie_id: int,
        *,
        size: str = "w1280",
        filename: str | None = None,
        skip_existing: bool = True,
    ) -> DownloadResult:
        """Download movie backdrop.

        Parameters
        ----------
        movie_id : int
            Movie ID.
        size : str
            Image size.
        filename : str | None
            Custom filename.
        skip_existing : bool
            Skip if exists.

        Returns
        -------
        DownloadResult
            Download result.

        """
        details = self._client.movies.details(movie_id)
        backdrop_path = getattr(details, "backdrop_path", None)
        title = getattr(details, "title", f"movie_{movie_id}")

        if backdrop_path is None:
            out = self._output_dir / (filename or f"{movie_id}_backdrop.jpg")
            return DownloadResult(
                path=out,
                success=False,
                error="No backdrop available",
            )

        if filename is None:
            safe_title = self._safe_filename(title)
            filename = f"{safe_title}_{movie_id}_backdrop.jpg"

        return self._download_image(
            image_path=backdrop_path,
            size=size,
            filename=filename,
            skip_existing=skip_existing,
        )

    def profile(
        self,
        person_id: int,
        *,
        size: str = "h632",
        filename: str | None = None,
        skip_existing: bool = True,
    ) -> DownloadResult:
        """Download person profile image.

        Parameters
        ----------
        person_id : int
            Person ID.
        size : str
            Image size.
        filename : str | None
            Custom filename.
        skip_existing : bool
            Skip if exists.

        Returns
        -------
        DownloadResult
            Download result.

        """
        details = self._client.people.details(person_id)
        profile_path = getattr(details, "profile_path", None)
        name = getattr(details, "name", f"person_{person_id}")

        if profile_path is None:
            out = self._output_dir / (filename or f"{person_id}.jpg")
            return DownloadResult(
                path=out,
                success=False,
                error="No profile image available",
            )

        if filename is None:
            safe_name = self._safe_filename(name)
            filename = f"{safe_name}_{person_id}.jpg"

        return self._download_image(
            image_path=profile_path,
            size=size,
            filename=filename,
            skip_existing=skip_existing,
        )

    def bulk_posters(
        self,
        movie_ids: list[int],
        *,
        size: str = "w500",
        naming: str = "id",
        skip_existing: bool = True,
    ) -> BulkDownloadResult:
        """Download posters for multiple movies.

        Parameters
        ----------
        movie_ids : list[int]
            List of movie IDs.
        size : str
            Image size.
        naming : str
            Naming style: "id" or "title".
        skip_existing : bool
            Skip existing files.

        Returns
        -------
        BulkDownloadResult
            Bulk download results.

        """
        result = BulkDownloadResult()

        for movie_id in movie_ids:
            try:
                if naming == "title":
                    download = self.poster(
                        movie_id,
                        size=size,
                        skip_existing=skip_existing,
                    )
                else:
                    download = self.poster(
                        movie_id,
                        size=size,
                        filename=f"{movie_id}.jpg",
                        skip_existing=skip_existing,
                    )

                if download.success:
                    result.successful.append(download)
                else:
                    result.failed.append(download)
            except Exception as e:  # noqa: BLE001
                out = self._output_dir / f"{movie_id}.jpg"
                result.failed.append(
                    DownloadResult(
                        path=out,
                        success=False,
                        error=str(e),
                    )
                )

        return result

    def _download_image(
        self,
        image_path: str,
        size: str,
        filename: str,
        skip_existing: bool,
    ) -> DownloadResult:
        """Download single image file.

        Parameters
        ----------
        image_path : str
            TMDB image path.
        size : str
            Image size.
        filename : str
            Output filename.
        skip_existing : bool
            Skip if exists.

        Returns
        -------
        DownloadResult
            Download result.

        """
        output_path = self._output_dir / filename

        if skip_existing and output_path.exists():
            return DownloadResult(
                path=output_path,
                success=True,
                error=None,
            )

        url = self._client.images.url(image_path, size)
        if url is None:
            return DownloadResult(
                path=output_path,
                success=False,
                error="Could not construct image URL",
            )

        try:
            # Use the underlying HTTP client
            response = self._client._http.client.get(url)
            response.raise_for_status()

            output_path.write_bytes(response.content)
            logger.info("Downloaded: %s", output_path)

            return DownloadResult(path=output_path, success=True)
        except Exception as e:  # noqa: BLE001
            return DownloadResult(
                path=output_path,
                success=False,
                error=str(e),
            )

    def _safe_filename(self, name: str) -> str:
        """Convert name to safe filename.

        Parameters
        ----------
        name : str
            Original name.

        Returns
        -------
        str
            Safe filename.

        """
        # Remove/replace unsafe characters
        safe = name.replace("/", "_").replace("\\", "_")
        safe = safe.replace(":", "_").replace("*", "_")
        safe = safe.replace("?", "").replace('"', "")
        safe = safe.replace("<", "").replace(">", "")
        safe = safe.replace("|", "_")
        return safe[:100]  # Limit length


class AsyncImageDownloader:
    """Async image downloader with concurrency control.

    Parameters
    ----------
    client : AsyncTMDBClient
        Async TMDB client.
    output_dir : str | Path
        Output directory.
    concurrency : int
        Maximum concurrent downloads.

    """

    def __init__(
        self,
        client: AsyncTMDBClient,
        output_dir: str | Path = "./images",
        concurrency: int = 5,
    ) -> None:
        self._client = client
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)

    async def bulk_posters(
        self,
        movie_ids: list[int],
        *,
        size: str = "w500",
        skip_existing: bool = True,
    ) -> BulkDownloadResult:
        """Download posters concurrently.

        Parameters
        ----------
        movie_ids : list[int]
            Movie IDs to download.
        size : str
            Image size.
        skip_existing : bool
            Skip existing files.

        Returns
        -------
        BulkDownloadResult
            Bulk download results.

        """
        tasks = [self._download_poster(mid, size, skip_existing) for mid in movie_ids]
        results = await asyncio.gather(*tasks)

        bulk_result = BulkDownloadResult()
        for download in results:
            if download.success:
                bulk_result.successful.append(download)
            else:
                bulk_result.failed.append(download)

        return bulk_result

    async def _download_poster(
        self,
        movie_id: int,
        size: str,
        skip_existing: bool,
    ) -> DownloadResult:
        """Download single poster with semaphore.

        Parameters
        ----------
        movie_id : int
            Movie ID.
        size : str
            Image size.
        skip_existing : bool
            Skip if exists.

        Returns
        -------
        DownloadResult
            Download result.

        """
        async with self._semaphore:
            output_path = self._output_dir / f"{movie_id}.jpg"

            if skip_existing and output_path.exists():
                return DownloadResult(path=output_path, success=True)

            try:
                details = await self._client.movies.details(movie_id)
                poster_path = getattr(details, "poster_path", None)

                if poster_path is None:
                    return DownloadResult(
                        path=output_path,
                        success=False,
                        error="No poster available",
                    )

                url = self._client.images.url(poster_path, size)
                if url is None:
                    return DownloadResult(
                        path=output_path,
                        success=False,
                        error="Could not build URL",
                    )

                response = await self._client._http.client.get(url)
                response.raise_for_status()
                output_path.write_bytes(response.content)

                return DownloadResult(path=output_path, success=True)
            except Exception as e:  # noqa: BLE001
                return DownloadResult(
                    path=output_path,
                    success=False,
                    error=str(e),
                )
