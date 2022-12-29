# notion2markdown

Python export for notion pages to markdown, staying as close as possible to the Notion markdown export.

To install the package, run:

```bash
pip install notion2markdown
```

## Usage

From the command line, run:

```bash
notion2markdown --token <token> --page_id <page_id> --output <output_file>
```

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

## Why make this

### Fix random asterisks

Let's say we have the following piece of text.

**Here is a sentence that was bolded *then* typed.**

Turns out this is a pain to export to markdown correctly, from Notion's block data structure.

**Notion randomly adds a 💩 ton of asterisks.** Besides the fact that the export is not available via the API, the official UI-only Notion export generates asterisk messes. This occurs *anytime* you edit a bolded or italicized piece of text. You can try this: In Notion, bold a line, *then* type out that line. When you export, you'll get something like the following; notice the prefix of 20 asterisks:

```
************************Here is a sentence that was bolded ****then**** typed.**
```

**`notion2md` generates unparse-able markdown.** `notion2md` partially solves the above problem. There are no spurious leading asterisks, but it treats every piece of text with different annotations, separately. This means it breaks the above sentence in 3 pieces, rendering bold text, then a bold-italic text, then a bold text. This leads to the following, which is correct but uninterpretable by markdown parsers:

```
**Here is a sentence that was bolded *****then***** typed.**
```

Passing either of the above markdown into markdown conversion utilities will result in spurious asterisks throughout your text. By contrast, `notion2markdown` will render the following:

```
**Here is a sentence that was bolded *then* typed.**```
```

It's worth noting that `notion2md` and the Notion markdown export both otherwise generate valid markdown. This annoying edge case bothered me enough to write this library.

### Include metadata

Notion's markdown export includes the title along with any properties associated with the page. `notion2markdown` does the same By contrast, `notion2md` excludes the metadata and page properties, just exporting the page content.

### Export entire database

`notion2markdown` can export an entire database. `notion2md` is designed to export individual pages but it could in theory be expanded to export an entire database. Especially for exporting a database, metadata and page titles are important.