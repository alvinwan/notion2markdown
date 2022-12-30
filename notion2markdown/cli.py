
from notion2markdown import NotionExporter
from argparse import ArgumentParser
from notion2markdown.utils import logger
import os


def main():
    parser = ArgumentParser('notion2markdown', description='Export Notion pages and databases to markdown.')
    parser.add_argument('url', type=str, help='URL of the Notion page or database to export. Must be public or explicitly shared with the token.')
    parser.add_argument('--token', type=str, help='Must be set here or in environment variable NOTION_TOKEN')
    args = parser.parse_args()

    token = args.token or os.environ.get("NOTION_TOKEN")
    assert token is not None, "Must set token using --token flag or in environment variable NOTION_TOKEN"

    exporter = NotionExporter(token=token)
    _, path = exporter.export_url(url=args.url)
    logger.info(f"Exported to {path}")