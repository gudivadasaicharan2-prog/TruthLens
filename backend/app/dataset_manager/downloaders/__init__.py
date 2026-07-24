"""
Dataset Downloaders
===================
Downloaders for various AI detection datasets.
"""

from .base_downloader import BaseDownloader
from .ffhq_downloader import FFHQDownloader
from .coco_downloader import COCODownloader
from .openimages_downloader import OpenImagesDownloader
from .genimage_downloader import GenImageDownloader
from .faceforensics_downloader import FaceForensicsDownloader
from .dfdc_downloader import DFDCDownloader

__all__ = [
    'BaseDownloader',
    'FFHQDownloader',
    'COCODownloader',
    'OpenImagesDownloader',
    'GenImageDownloader',
    'FaceForensicsDownloader',
    'DFDCDownloader'
]
