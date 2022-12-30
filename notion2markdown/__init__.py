from pathlib import Path
from typing import Union
from .notion import NotionDownloader
from .json2md import JsonToMdConverter


class NotionExporter:
    def __init__(self, token: str):
        self.downloader = NotionDownloader(token)
        self.converter = JsonToMdConverter()

    def export_url(self, url: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion page or database."""
        self.downloader.download_url(url, json_dir)
        return self.converter.convert(json_dir, md_dir)

    def export_database(self, database_id: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion database and associated pages."""
        self.downloader.download_database(database_id, json_dir)
        self.converter.convert(json_dir, md_dir)

    def export_page(self, page_id: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion page."""
        self.downloader.download_page(page_id, json_dir)
        self.converter.convert(json_dir, md_dir)