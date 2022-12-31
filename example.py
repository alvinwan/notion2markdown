from notion2markdown import NotionExporter

# 1. You can create your own Notion integration token by following this tutorial. Just follow step 1:
# https://developers.notion.com/docs/create-a-notion-integration#step-1-create-an-integration
token = "secret_wPO2C5mhbFBHeRfFsoS8bxtDBARceyEFUavwMwGDfvi"  # for the demo, use this as-is if you're feeling lazy

# Normally, you'd store this in an environment variable, called NOTION_TOKEN
# import os
# token = os.environ["NOTION_TOKEN"]

# 2. Add your integration to a Notion page or database. Just follow step 2:
# https://developers.notion.com/docs/create-a-notion-integration#step-2-share-a-database-with-your-integration
url = "https://lvinwan.notion.site/Example-Notion-Page-f8deb4d042034c6c8d03b6de37a99498"  # again, just for the demo, use this as-is if you're feeling lazy

exporter = NotionExporter(token=token)
path = exporter.export_url(url=url)
print(f" * Exported to {path}")
