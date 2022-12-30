from notion2markdown import NotionExporter
import os


exporter = NotionExporter(token=os.environ["NOTION_TOKEN"])
exporter.export_url(url='https://lvinwan.notion.site/Example-Notion-Page-f8deb4d042034c6c8d03b6de37a99498')