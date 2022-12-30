# notion2markdown

Export notion pages to markdown in Python.

## Install

```bash
pip install notion2markdown
```

## CLI

> Before getting started, [create a notion integration](https://developers.notion.com/docs/create-a-notion-integration), and grab the token.

Put the following in your `~/.zshrc`, and start a new terminal session.

```bash
export NOTION_TOKEN=...
```

Then, export a notion page or database.

```bash
notion2markdown notion_url
```

> If you get the following error, `notion_client.errors.APIResponseError: Could not find block with ID`, follow the suggestion provided: ` Make sure the relevant pages and databases are shared with your integration.` [Click here for a tutorial](https://www.notion.so/help/add-and-manage-connections-with-the-api#add-connections-to-pages) on granting your integration access to your database or page.

By default markdown will be exported to a directory named `./md`. You can also use the `n2md` alias

```bash
n2md notion_url
```

## Library

You can also write a script to export, programmatically. See [`example.py`](https://github.com/alvinwan/notion2markdown/blob/main/example.py).

```python
from notion2markdown import NotionExporter
import os


exporter = NotionExporter(token=os.environ["NOTION_TOKEN"])
exporter.export_url(url='https://lvinwan.notion.site/lvinwan/Example-Notion-Page-f8deb4d042034c6c8d03b6de37a99498')
```

You may optionally download JSON, then convert to markdown separately. This may be helpful if you want to cache downloads, for example. You can use the exporter's downloader and converter separately, like this:

```python
exporter.downloader.download_url(url)  # Download json
exporter.converter.convert()  # Convert json to md
```

You may also export to any directory of your choosing.

```python
exporter.export_url(url, json_dir='./my_special_directory')
```

## Why use this library?

To start, Notion's official markdown export is (1) available only via the UI and (2) buggy.

### 1. Fix random asterisks

Let's say we have the following piece of text. Turns out this is a pain to export to markdown correctly, from Notion's block data structure.

> **Here is a sentence that was bolded *then* typed.**

**Notion randomly adds a ton of asterisks.** This occurs *anytime* you edit a bolded or italicized piece of text. To reproduce: In Notion, bold a line, *then* type out that line. When you export, you'll get something like the following with random leading or trailing asterisks.

```
************************Here is a sentence that was bolded ****then**** typed.**
```

**`notion2md` generates unparse-able markdown.** `notion2md` partially solves the above problem. There are no spurious leading asterisks, but it treats every piece of text with different annotations, separately. This means it breaks the above sentence in 3 pieces, rendering bold text, then a bold-italic text, then a bold text. This leads to the following, which is *technically* correct but uninterpretable by markdown parsers:

```
**Here is a sentence that was bolded *****then***** typed.**
```

Passing either of the above markdown into markdown conversion utilities will result in spurious asterisks throughout your text. By contrast, `notion2markdown` will render the following, which renders correctly with any standard markdown engine:

```
**Here is a sentence that was bolded *then* typed.**
```

It's worth noting that `notion2md` and the Notion markdown export both otherwise generate valid markdown. This annoying edge case bothered me enough to write this library.

### 2. Export databases, with metadata

Notion's official markdown export includes the title along with any properties associated with the page.

This library `notion2markdown` does the same, adding properties and the title in the same format that the official Notion export does. By contrast, `notion2md` excludes the metadata and page properties, just exporting the page content.

Furthermore, `notion2markdown` can export an entire database, like Notion's official export. On the other hand, `notion2md` is designed to export individual pages. Naturally, it could be extended to export entire databases.

## Develop

```bash
git clone git@github.com:alvinwan/notion2markdown.git
pip install --editable .
```

Run tests

```bash
pytest notion2markdown --doctest-modules
```
