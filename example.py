from notion2markdown import NotionExporter
import os


exporter = NotionExporter(token=os.environ["NOTION_TOKEN"])
path = exporter.export_url(url=os.environ["NOTION_URL"])
print(f" * Exported to {path}")