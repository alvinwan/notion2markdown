# notion2markdown

Python export for notion pages to markdown, staying as close as possible to the Notion markdown export.

## Install

To install the package, run:

```bash
pip install notion2markdown
```

## Usage: CLI

As the official [notion-sdk-py](https://github.com/ramnes/notion-sdk-py) library notes,

> Before getting started, [create an integration](https://www.notion.com/my-integrations) and find the token. [→ Learn more about authorization.](https://developers.notion.com/docs/authorization)

From the command line, run the following to export a notion page:

```bash
notion2markdown https://notion.so/XXXX
```

Note that URL can be for a database or a single page. By default markdown will be exported to a directory named `./md`.

## Usage: Library

You can also write a script to export multiple pages. For example:

```python
from notion2markdown import NotionDownloader, JsonToMdConverter

...

notion = NotionDownloader(token, database_id)
notion.download("./json")

converter = JsonToMdConverter("./json")
converter.convert("./md")
```

The above demo is available at `example.py` and can be run with:

```bash
git clone XXX
python example.py
```

## Why use this library?

To start, Notion's official markdown export is available only via the UI. Even if they exposed it via an API, however, it still has issues.

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

- This library `notion2markdown` does the same, adding properties and the title in the same format that the official Notion export does. By contrast, `notion2md` excludes the metadata and page properties, just exporting the page content.
- Furthermore, `notion2markdown` can export an entire database, like Notion's official export. On the other hand, `notion2md` is designed to export individual pages. Naturally, it could be extended to export entire databases.
