from notion2markdown import NotionExporter
import os


exporter = NotionExporter(token=os.environ["NOTION_TOKEN"])
exporter.export_url(url=os.environ["NOTION_URL"])