from pathlib import Path
from typing import Union
from .notion import NotionDownloader
from .json2md import JsonToMdConverter


class NotionExporter:
    def __init__(self, token: str):
        self.notion = NotionDownloader(token)
        self.converter = JsonToMdConverter()

    def export_url(self, url: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion page or database."""
        self.notion.download_url(url, json_dir)
        self.converter.convert(json_dir, md_dir)

    def export_database(self, database_id: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion database and associated pages."""
        self.notion.download_database(database_id, json_dir)
        self.converter.convert(json_dir, md_dir)

    def export_page(self, page_id: str, json_dir: Union[str, Path]='./json', md_dir: Union[str, Path]='./md'):
        """Export the notion page."""
        self.notion.download_page(page_id, json_dir)
        self.converter.convert(json_dir, md_dir)