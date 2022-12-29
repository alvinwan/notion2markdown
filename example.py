from notion2markdown import NotionDownloader, JsonToMdConverter
import os


token = os.environ["NOTION_TOKEN"]
database_id = os.environ["NOTION_DATABASE_ID"]

notion = NotionDownloader(token, database_id)
notion.download("./json")

converter = JsonToMdConverter("./json")
converter.convert("./md")