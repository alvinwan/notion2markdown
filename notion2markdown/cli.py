
from notion2markdown import NotionExporter
from argparse import ArgumentParser
from notion2markdown.utils import logger
import os


DEFAULT_FILTER = {
        "property": "Status",
        "status": {
            "equals": "Done",
        },
    }

def main():
    parser = ArgumentParser('notion2markdown', description='Export Notion pages and databases to markdown.')
    parser.add_argument('url', type=str, help='URL of the Notion page or database to export. Must be public or explicitly shared with the token.')
    parser.add_argument('--token', type=str, help='Must be set here or in environment variable NOTION_TOKEN')
    parser.add_argument('--extension', type=str, help='The file extension to output', default="md")
    parser.add_argument('--strip-meta-chars', type=str, help='Strip characters from frontmatter')
    parser.add_argument('--no-filter', help='Filter for notion export', action="store_true")
    args = parser.parse_args()

    token = args.token or os.environ.get("NOTION_TOKEN")
    assert token is not None, "Must set token using --token flag or in environment variable NOTION_TOKEN"

    strip_meta_chars = args.strip_meta_chars
    extension = args.extension
    no_filter = args.no_filter

    if no_filter:
        filter = None
    else:
        filter = DEFAULT_FILTER

    exporter = NotionExporter(token=token, strip_meta_chars=strip_meta_chars, extension=extension, filter=filter)
    path = exporter.export_url(url=args.url)
    logger.info(f"Exported to {path} directory")