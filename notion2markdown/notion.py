from datetime import datetime
from pathlib import Path
import json
from itertools import chain
from typing import List, Union
from .utils import logger

from notion_client import Client
from notion_client.helpers import iterate_paginated_api as paginate


class NotionDownloader:
    def __init__(self, token: str):
        self.transformer = LastEditedToDateTime()
        self.notion = NotionClient(token=token, transformer=self.transformer)
        self.io = NotionIO(self.transformer)

    def download_url(self, url: str, out_dir: Union[str, Path]='./json'):
        """Download the notion page or database."""
        out_dir = Path(out_dir)
        slug = url.split("/")[-1].split('?')[0]
        if '-' in slug:
            page_id = slug.split('-')[-1]
            self.download_page(page_id, out_dir / f"{page_id}.json")
        else:
            self.download_database(slug, out_dir)

    def download_page(self, page_id: str, out_path: Union[str, Path]='./json', fetch_metadata: bool=True):
        """Download the notion page."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        blocks = self.notion.get_blocks(page_id)
        self.io.save(blocks, out_path)

        if fetch_metadata:
            metadata = self.notion.get_metadata(page_id)
            self.io.save([metadata], out_path.parent / "database.json")

    def download_database(self, database_id: str, out_dir: Union[str, Path]='./json'):
        """Download the notion database and associated pages."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "database.json"
        prev = {pg["id"]: pg["last_edited_time"] for pg in self.io.load(path)}
        pages = self.notion.get_database(database_id)  # download database
        self.io.save(pages, path)

        for cur in pages:  # download individual pages in database IF updated
            if prev.get(cur["id"], datetime(1, 1, 1)) < cur["last_edited_time"]:
                self.download_page(cur["id"], out_dir / f"{cur['id']}.json", False)
                logger.info(f"Downloaded {cur['url']}")


class LastEditedToDateTime:
    def forward(self, blocks, key: str = "last_edited_time") -> List:
        return [
            {**block, key: datetime.fromisoformat(block[key][:-1])} for block in blocks
        ]

    def reverse(self, o) -> Union[None, str]:
        if isinstance(o, datetime):
            return o.isoformat() + "Z"


class NotionIO:
    def __init__(self, transformer):
        self.transformer = transformer

    def load(self, path: Union[str, Path]) -> List[dict]:
        """Load blocks from json file."""
        if Path(path).exists():
            with open(path) as f:
                return self.transformer.forward(json.load(f))
        return []

    def save(self, blocks: List[dict], path: str):
        """Dump blocks to json file."""
        with open(path, "w") as f:
            json.dump(blocks, f, default=self.transformer.reverse)


class NotionClient:
    DEFAULT_FILTER = {
        "property": "Status",
        "status": {
            "equals": "Done",
        },
    }

    def __init__(self, token: str, transformer):
        self.client = Client(auth=token)
        self.transformer = transformer

    def get_metadata(self, page_id: str) -> dict:
        """Get page metadata as json."""
        return self.transformer.forward([self.client.pages.retrieve(page_id=page_id)])[0]

    def get_blocks(self, block_id: int) -> List:
        """Get all page blocks as json. Recursively fetches descendants."""
        blocks = []
        for child in chain(
            *paginate(self.client.blocks.children.list, block_id=block_id)
        ):
            child["children"] = (
                list(self.get_blocks(child["id"])) if child["has_children"] else []
            )
            blocks.append(child)
        return list(self.transformer.forward(blocks))

    def get_database(self, database_id: str, filter=DEFAULT_FILTER) -> List:
        """Fetch pages in database as json."""
        results = paginate(
            self.client.databases.query,
            database_id=database_id,
            filter=filter,
        )
        return list(self.transformer.forward(chain(*results)))
