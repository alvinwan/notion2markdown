from collections import defaultdict
from datetime import datetime
import glob
import json
from pathlib import Path
from typing import List, Union
from .utils import normalize_id, get_whitespace

class Noop:
    pass


noop = Noop()


rules = []


def rule(func):
    rules.append(func)
    return func



class JsonToMdConverter:
    def __init__(self, strip_meta_chars=None, extension="md"):
        self.stripchars=strip_meta_chars
        self.extention=extension

    def get_key(self, value):
        if self.stripchars == None:
            return value

        return value.strip(self.stripchars)

    def get_post_metadata(self, post):
        converter = JsonToMd(config={"apply_list": {"delimiter": ","}})
        return {
            key: self.get_key(converter.json2md(value))
            for key, value in post["properties"].items()
            if converter.json2md(value)
        }

    def convert(self, json_dir: Union[str, Path], md_dir: Union[str, Path]):
        json_dir = Path(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)

        md_dir = Path(md_dir)
        md_dir.mkdir(parents=True, exist_ok=True)

        with open(json_dir / "database.json") as f:
            page_id_to_metadata = {
                page["id"]: self.get_post_metadata(page) for page in json.load(f)
            }

        paths = [
            path for path in glob.glob(str(json_dir / "*.json"))
            if Path(path).name != "database.json"
        ]
        for path in paths:
            with open(path) as f:
                blocks = json.load(f)
                page_id = Path(path).stem
                path = md_dir / f"{page_id}.{self.extention}"
                if page_id not in page_id_to_metadata:  # page has been deleted
                    continue
                metadata = page_id_to_metadata[page_id]
                markdown = JsonToMd(metadata).page2md(blocks)
                with open(path, "w", encoding='utf-8') as f:
                    f.write(markdown)

                if len(paths) == 1:
                    return path

        return md_dir


class JsonToMd:
    def __init__(self, metadata: dict = None, config: dict = None):
        self.metadata = metadata or {}
        self.config = config or {}
        self.state = defaultdict(dict)

    @rule
    def apply_list(self, value, prv=None, nxt=None):
        delimiter = (self.config or {}).get("apply_list", {}).get("delimiter", {}) or ""
        if isinstance(value, list):
            if len(value) == 0:
                return ""
            pieces = [
                self.json2md(
                    value[i],
                    value[i - 1] if i - 1 >= 0 else None,
                    value[i + 1] if i + 1 < len(value) else None,
                )
                for i in range(len(value))
            ]
            return delimiter.join(filter(lambda s: s is not noop, pieces))
        return noop

    @rule
    def apply_href(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("href"):
            return f"[{value['plain_text']}]({value['href']})"  # TODO: href and annotations are not exclusive
        return noop

    @rule
    def apply_annotation(self, value, prv=None, nxt=None, annotation_to_mark={
        "strikethrough": "~~",
        "bold": "**",
        "italic": "*",
        "underline": "__",
        "code": "`",
    }):
        """
        >>> c = JsonToMd()
        >>> hello_bold = {"type": "text", "text": {"content": "hello", "link": None}, "annotations": {"bold": True, "italic": False, "strikethrough": False, "underline": False, "code": False, "color": "default"}}
        >>> c.json2md(hello_bold)
        '**hello**'
        >>> hello_bold_strike = {"type": "text", "text": {"content": "hello", "link": None}, "annotations": {"bold": True, "italic": False, "strikethrough": True, "underline": False, "code": False, "color": "default"}}
        >>> c.json2md(hello_bold_strike)
        '**~~hello~~**'
        >>> c.json2md([hello_bold, hello_bold_strike])
        '**hello~~hello~~**'
        >>> hello_strike = {"type": "text", "text": {"content": "hello", "link": None}, "annotations": {"bold": False, "italic": False, "strikethrough": True, "underline": False, "code": False, "color": "default"}}
        >>> c.json2md([hello_strike, hello_bold_strike])
        '~~hello**hello**~~'
        >>> c = JsonToMd()
        >>> heading = {"type":"text","text":{"content":"Payment Claim assessed by Head Contractor","link":None},"annotations":{"bold":True,"italic":False,"strikethrough":False,"underline":False,"code":False,"color":"blue"},"plain_text":"Payment Claim assessed by Head Contractor","href":None}
        >>> c.json2md(heading)
        '**Payment Claim assessed by Head Contractor**'
        >>> c = JsonToMd()
        >>> heading = {"type":"text","text":{"content":"Payment Claim assessed by Head Contractor","link":None},"annotations":{"bold":True,"italic":False,"strikethrough":False,"underline":False,"code":False,"color":"blue"},"plain_text":"Payment Claim assessed by Head Contractor","href":None}
        >>> blank = {"type":"text","text":{"content":"\\n","link":None},"annotations":{"bold":True,"italic":False,"strikethrough":False,"underline":False,"code":False,"color":"default"},"plain_text":"\\n","href":None}
        >>> c.json2md(heading, None, blank)
        '**Payment Claim assessed by Head Contractor**'
        >>> c = JsonToMd()
        >>> hello = {"type":"text","text":{"content":"Hello ","link":None},"annotations":{"bold":True,"italic":False,"strikethrough":False,"underline":False,"code":False,"color":"blue"},"plain_text":"Hello ","href":None}
        >>> world = {"type": "text", "text": {"content": "world"}}
        >>> c.json2md([hello, world])  # moves space to outside of the bold for valid markdown
        '**Hello** world'
        """
        if isinstance(value, dict) and "type" in value:
            state = self.state["apply_annotation"]
            if "annotations" not in state:
                state["annotations"] = []
            text = self.json2md(value[value["type"]])
            annotations = value.get("annotations", {})

            # open annotations first
            applied = []
            for annotation, mark in annotation_to_mark.items():
                if (
                    annotation not in self.state["apply_annotation"]["annotations"]
                    and annotations.get(annotation)
                ):
                    # NOTE: starting annotations in this loop work from the
                    # inside out. so we need to insert them at the beginning of
                    # the list
                    applied.insert(0, annotation)
                    if not (prv and prv.get("annotations", {}).get(annotation)):
                        lines = []
                        if text is noop or not hasattr(text, 'split'):
                            return noop
                        for line in text.split('\n'):
                            if line:
                                whitespace, stripped = get_whitespace(line)
                                lines.append(f'{whitespace}{mark}{stripped}')
                            else:
                                lines.append('')
                        text = '\n'.join(lines)

            # add the new annotations to the end* of the list of open annotations
            self.state["apply_annotation"]["annotations"].extend(applied)

            # close annotations in the order they were opened
            for annotation in self.state["apply_annotation"]["annotations"][::-1]:

                # Strange case where an empty bold new line stops from terminating block
                if nxt and (nxt.get("text", {}).get("content") == "\n" or nxt.get("text", {}).get("content") == " "):
                    nxt=None

                if not (nxt and nxt.get("annotations", {}).get(annotation)):
                    self.state["apply_annotation"]["annotations"].remove(annotation)
                    lines = []

                    if text is noop or not hasattr(text, 'split'):
                        return noop
                    for line in text.split('\n'):
                        if line:
                            whitespace, stripped = get_whitespace(line, leading=False)
                            lines.append(f'{stripped}{annotation_to_mark[annotation]}{whitespace}')
                        else:
                            lines.append('') # NOTE: markdown syntax does not apply to multiple lines
                    text = '\n'.join(lines)
            return text
        return noop

    @rule
    def apply_dates(self, value, prv=None, nxt=None):
        if isinstance(value, dict):
            if value.get("start") and not value.get("end"):
                date_str = self.json2md(value["start"])
                try:
                    if 'T' in date_str:
                        # For ISO format dates like '2025-03-10T11:00:00.000+05:00'
                        # Remove timezone part for parsing if present
                        date_part = date_str.split('T')[0]
                        return datetime.strptime(date_part, "%Y-%m-%d").strftime("%b %d, %Y")
                    else:
                        # Original format for simple dates
                        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")
                except ValueError:
                    # If we can't parse it, just return the original string
                    return date_str
        # TODO: catch any other dates?
        return noop

    @rule
    def block_heading(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "").startswith("heading"):
            for i in range(6):
                if value["type"] == f"heading_{i + 1}":
                    return f"{'#' * (i + 1)} {self.json2md(value['heading_' + str(i + 1)]['rich_text'])}\n"
        return noop

    @rule
    def block_paragraph(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "paragraph":
            return f"{self.json2md(value['paragraph']['rich_text'])}\n"
        return noop

    @rule
    def block_callout(self, value, prv=None, nxt=None):
        # Following this convention: https://docs.readme.com/rdmd/docs/callouts (callouts denoted by leading emoji)
        if isinstance(value, dict) and value.get("type", "") == "callout":
            return '\n'.join([f"> {line}" for line in f"{self.json2md(value['callout']['icon'])}\n\n{self.json2md(value['callout']['rich_text'])}\n{self.jsons2md(value['children'])}".splitlines()])
        return noop

    @rule
    def block_bookmark(self, value, prv=None, nxt=None):
        """
        >>> c = JsonToMd()
        >>> item = {"object":"block","id":"f750cdfd99ee43319c26b13784b75a38","parent":{"type":"block_id","block_id":"9f46d84c-e671-465f-ab2a-0e57700b44d9"},"created_time":"2023-08-21T05:26:00.000Z","last_edited_time":"2023-08-21T05:26:00Z","created_by":{"object":"user","id":"f6647474-4586-45da-bb70-352d6c81336f"},"last_edited_by":{"object":"user","id":"f6647474-4586-45da-bb70-352d6c81336f"},"has_children":False,"archived":False,"type":"bookmark","bookmark":{"caption":[],"url":"https://www.qbcc.qld.gov.au/running-business/trust-accounts/pbs-building-qld-pty-ltd"},"children":[]}
        >>> c.block_bookmark(item)
        '[External Link](https://www.qbcc.qld.gov.au/running-business/trust-accounts/pbs-building-qld-pty-ltd)'
        """
        # Following this convention: https://docs.readme.com/rdmd/docs/callouts (callouts denoted by leading emoji)
        if isinstance(value, dict) and value.get("type", "") == "bookmark":
            url = value.get("bookmark")["url"]
            return f"[External Link]({url})"
        return noop

    @rule
    def block_divider(self, value, prv=None, nxt=None):
        """
        >>> c = JsonToMd()
        >>> divider = {"object":"block","id":"6d971a9c59d045e9b1eb9ab6d1fc0cc5","parent":{"type":"page_id","page_id":"8d9f3b08-ed27-4600-b238-b8105fdb6c09"},"created_time":"2023-06-19T04:00:00.000Z","last_edited_time":"2023-06-19T04:00:00Z","created_by":{"object":"user","id":"f6647474-4586-45da-bb70-352d6c81336f"},"last_edited_by":{"object":"user","id":"f6647474-4586-45da-bb70-352d6c81336f"},"has_children":False,"archived":False,"type":"divider","divider":{},"children":[]}
        >>> c.block_divider(divider)
        '<div></div>'
        """
        if isinstance(value, dict) and value.get("type", "") == "divider":
            return "<div></div>"
        return noop

    @rule
    def block_item(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") in ("bulleted_list_item", "numbered_list_item"):
            indent = (self.config or {}).get("block_item", {}).get("indent", "    ")

            # Determine if it's a bulleted or numbered list
            if value["type"] == "bulleted_list_item":
                marker = "-"
                self.state.pop("active_numbered_list", None)  # Reset numbered list state
                self.state.pop("numbered_list_counter", None)
            else:  # numbered_list_item
                if "active_numbered_list" not in self.state:
                    self.state["active_numbered_list"] = True
                    self.state["numbered_list_counter"] = 1
                else:
                    self.state["numbered_list_counter"] += 1
                marker = f"{self.state['numbered_list_counter']}."

            # Generate the list item
            lines = [f"{marker} {self.json2md(value[value['type']]['rich_text'])}"]

            # Handle nested lists (if children exist)
            if value["has_children"]:
                sub = self.jsons2md(value["children"])
                lines.extend([f"{indent}{line}" for line in sub.splitlines()])
                lines.append("")  # Add spacing after nested list

            # If the next block is not a list, reset numbered list state
            if not (nxt and isinstance(nxt, dict) and nxt.get("type") in ("numbered_list_item", "bulleted_list_item")):
                self.state.pop("active_numbered_list", None)
                self.state.pop("numbered_list_counter", None)

            return "\n".join(lines)

        return noop


    @rule
    def apply_file(self, value, prv=None, nxt=None):
        """
        >>> c = JsonToMd()
        >>> icon = {"type":"external","external":{"url":"https://www.notion.so/icons/info-alternate_gray.svg"}}
        >>> c.apply_file(icon)
        '![icon](https://www.notion.so/icons/info-alternate_gray.svg)'
        """
        if isinstance(value, dict):
            if value.get("type", "") == "external" and value.get("external"):
                url = value.get("external")["url"]
                caption = "icon"
                return f"![{caption}]({url})"
        return noop

    @rule
    def block_quote(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "quote":
            out = f"> {self.json2md(value['quote']['rich_text'])}\n{self.jsons2md(value['children'])}"
            return '\n> '.join(out.splitlines())
        return noop

    @rule
    def block_to_do(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "to_do":
            return f"- [ ] {self.json2md(value['to_do']['rich_text'])}{self.jsons2md(value['children'])}"
        return noop

    @rule
    def block_code(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "code":
            return f"```{value['code']['language']}\n{self.json2md(value['code']['rich_text'])}\n```"
        return noop

    @rule
    def block_table(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "table":
            lines = []
            table = value["children"]
            header = table[0]["table_row"]["cells"]
            lines.append(
                "|" + "|".join([self.json2md(cell[0]) if cell else '' for cell in header]) + "|"
            )
            lines.append("|" + "|".join(["---" for _ in header]) + "|")
            for child in table[1:]:
                row = child["table_row"]["cells"]
                lines.append(
                    "|"
                    + "|".join([self.json2md(cell[0]) for cell in row])
                    + "|"
                )
            lines.append("")
            return "\n".join(lines)
        return noop

    @rule
    def block_image(self, value, prv=None, nxt=None):
        """
        Options:
        - caption_mode: alt, em, none
        """
        if isinstance(value, dict) and value.get("type", "") == "image":
            image = value['image']
            caption_mode = (self.config or {}).get("block_image", {}).get('caption_mode', 'em')
            caption = self.json2md(image['caption'])

            if 'file' in image:
                url = image['file']['url']
            elif 'external' in image:
                url = image['external']['url']
            else:
                url = None

            if caption_mode == 'alt':
                return f"![{caption}]({url})"
            elif caption_mode == 'em':
                return f"![]({url})\n<em>{caption}</em>"
            elif caption_mode == 'none':
                return f"![]({url})"
        return noop

    @rule
    def block_toggle(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "toggle":
            return f"<details>\n<summary>{self.json2md(value['toggle']['rich_text'])}</summary>\n{self.jsons2md(value['children'])}</details>"
        return noop

    @rule
    def block_math(self, value, prv=None, nxt=None):
        """
        After including this in your markdown or HTML, you can then render the math using [MathJax](https://github.com/mathjax/MathJax).
        """
        if isinstance(value, dict) and value.get("type", "") == "equation":
            expression = value['equation']['expression'].replace('\\', '\\\\').replace('_', '\\_')
            if value.get('object') == 'block':
                return f"$${expression}$$"
            return f"${expression}$"
        return noop

    @rule
    def unpack_type(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and "type" in value:
            return self.json2md(value[value["type"]])
        return noop

    @rule
    def apply_misc(self, value, prv=None, nxt=None):
        if isinstance(value, dict):
            for key in (
                "name",
                "content",
            ):  # TODO: split this out. misc shouldnt be needed?
                if key in value:
                    return self.json2md(value[key])
            if 'id' in value:
                return normalize_id(value['id'])
        return noop

    @rule
    def apply_text(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and "text" in value:
            return value["text"]["content"]
        return noop

    @rule
    def apply_string(self, value, prv=None, nxt=None):
        if isinstance(value, str):
            return value
        return noop

    @rule
    def apply_none(self, value, prv=None, nxt=None):
        if value is None:
            return ""
        return noop

    def json2md(self, value: Union[str, List, dict], prv=None, nxt=None) -> str:
        """
        Lower-level conversion from notion JSON to markdown. This is the core of
        the conversion logic.
        """
        for rule in rules:
            if (md := rule(self, value, prv, nxt)) is not noop:
                return md

        return noop

    def jsons2md(self, blocks: List) -> str:
        """
        Top-level conversion from notion JSON to markdown. In this top-level, we
        add line breaks in between block types.
        """
        result, cur = "", None
        for i in range(len(blocks)):
            cur = blocks[i]
            prv = blocks[i - 1] if i > 0 else None
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            if (md := self.json2md(cur, prv, nxt)) is not noop:
                result += "\n" + md
            else:
                raise NotImplementedError(f"Unsupported block type: {cur['type']}")

            if cur["type"] != (nxt and nxt["type"]):
                result += "\n"

            if cur["type"] == "callout" and (nxt and nxt["type"] == "callout"):
                result += '\n<div></div>\n'  # weird property of blockquote parsing: https://stackoverflow.com/a/13066620/4855984
        return result

    def page2md(self, blocks: List[dict]) -> str:
        """Converts a notion page to markdown."""
        markdown = "---\n"
        for key, value in self.metadata.items():
            if value:
                markdown += f"{key}: {value}\n"
        markdown += f"---\n\n"
        if title := self.metadata.get('Name') or self.metadata.get('title'):
            markdown += f"# {title}\n\n"
        markdown += self.jsons2md(blocks)
        return markdown
