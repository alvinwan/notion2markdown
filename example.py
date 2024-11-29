from notion2markdown.json2md import JsonToMd
import pandas as pd


c = JsonToMd()
df = pd.read_json("/home/ubuntu/notion2markdown/sample_data.jsonl", lines=True)

blocks = df['_airbyte_data'].tolist()[:10]
print(c.page2md(blocks, parse_children=True))
