# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Data acquisition and export.

Dataset building, image downloading, export utilities, and daily syncs.
"""

from tmdbfusion.data.dataset import Dataset
from tmdbfusion.data.dataset import DatasetBuilder
from tmdbfusion.data.download import AsyncImageDownloader
from tmdbfusion.data.download import BulkDownloadResult
from tmdbfusion.data.download import DownloadResult
from tmdbfusion.data.download import ImageDownloader
from tmdbfusion.data.export import ExportConfig
from tmdbfusion.data.export import Exporter
from tmdbfusion.data.export import export_to_csv
from tmdbfusion.data.export import export_to_json
from tmdbfusion.data.sync import DailyExportSync


__all__ = [
    # Download
    "AsyncImageDownloader",
    "BulkDownloadResult",
    # Sync
    "DailyExportSync",
    # Dataset
    "Dataset",
    "DatasetBuilder",
    "DownloadResult",
    "ExportConfig",
    "Exporter",
    "ImageDownloader",
    # Export
    "export_to_csv",
    "export_to_json",
]
