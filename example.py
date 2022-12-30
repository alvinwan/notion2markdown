from notion2markdown import NotionExporter
import os


token = os.environ["NOTION_TOKEN"]
url = os.environ["NOTION_URL"]


exporter = NotionExporter(token=token)
exporter.export_url(url=url, json_dir="./json", md_dir="./md")