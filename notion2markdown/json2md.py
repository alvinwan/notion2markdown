from collections import defaultdict
from datetime import datetime
import glob
import json
from pathlib import Path
from typing import List, Union


class Noop:
    pass


noop = Noop()


rules = []


def rule(func):
    rules.append(func)
    return func


class JsonToMdConverter:
    def get_post_metadata(self, post):
        converter = JsonToMd(config={"apply_list": {"delimiter": ","}})
        return {
            key: converter.json2md(value)
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
                page["id"].replace('-', ''): self.get_post_metadata(page) for page in json.load(f)
            }

        for path in glob.iglob(str(json_dir / "*.json")):
            if Path(path).name == "database.json":
                continue
            with open(path) as f:
                blocks = json.load(f)
                page_id = Path(path).stem.replace('-', '')
                slug = page_id.replace('-', '')
                path = md_dir / f"{slug}.md"
                if page_id not in page_id_to_metadata:  # page has been deleted
                    continue
                metadata = page_id_to_metadata[page_id]
                markdown = JsonToMd(metadata).page2md(blocks)
                with open(path, "w") as f:
                    f.write(markdown)

        return page_id_to_metadata, md_dir


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
            return delimiter.join(
                [
                    self.json2md(
                        value[i],
                        value[i - 1] if i - 1 >= 0 else None,
                        value[i + 1] if i + 1 < len(value) else None,
                    )
                    for i in range(len(value))
                ]
            )
        return noop

    @rule
    def apply_href(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("href"):
            return f"[{value['plain_text']}]({value['href']})"  # TODO: href and annotations are not exclusive
        return noop

    @rule
    def apply_annotation(self, value, prv=None, nxt=None):
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
        """
        if isinstance(value, dict) and "type" in value:
            state = self.state["apply_annotation"]
            if "annotations" not in state:
                state["annotations"] = []
            text = self.json2md(value[value["type"]])
            annotations = value.get("annotations", {})

            # open annotations first
            annotation_to_mark = {
                "strikethrough": "~~",
                "bold": "**",
                "italic": "*",
                "underline": "__",
                "code": "`",
            }
            applied = []
            for annotation, mark in annotation_to_mark.items():
                if annotation not in self.state["apply_annotation"]["annotations"]:
                    if annotations.get(annotation):
                        # starting annotations in this loop work from the inside out. so we need to insert them at the beginning of the list
                        applied.insert(0, annotation)
                        if not (prv and prv.get("annotations", {}).get(annotation)):
                            text = f"{mark}{text}"
            # add the new annotations to the end* of the list of open annotations
            self.state["apply_annotation"]["annotations"].extend(applied)

            # close annotations in the order they were opened
            for annotation in self.state["apply_annotation"]["annotations"][::-1]:
                if not (nxt and nxt.get("annotations", {}).get(annotation)):
                    self.state["apply_annotation"]["annotations"].remove(annotation)
                    text = f"{text}{annotation_to_mark[annotation]}"
            return text
        return noop

    @rule
    def apply_dates(self, value, prv=None, nxt=None):
        if isinstance(value, dict):
            if value.get("start") and not value.get("end"):
                return datetime.strptime(
                    self.json2md(value["start"]), "%Y-%m-%d"
                ).strftime("%b%e,%Y")
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
        if isinstance(value, dict) and value.get("type", "") == "callout":
            return f"<aside>\n{self.json2md(value['callout']['icon'])} {self.json2md(value['callout']['rich_text'])}\n{self.jsons2md(value['children'])}</aside>"
        return noop

    @rule
    def block_item(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") in (
            "bulleted_list_item",
            "numbered_list_item",
        ):
            indent = (
                (self.config or {}).get("block_item", {}).get("indent", "    ")
            )  # TODO: make getting config less ugly
            marker = {"bulleted_list_item": "-", "numbered_list_item": "1."}[
                value["type"]
            ]

            lines = []
            lines.append(f"{marker} {self.json2md(value[value['type']]['rich_text'])}")
            if value["has_children"]:
                sub = self.jsons2md(value["children"])
                lines.extend([f"{indent}{line}" for line in sub.splitlines()])
                lines.append("")
            return "\n".join(lines)
        return noop

    @rule
    def block_quote(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "quote":
            return f"> {self.json2md(value['quote']['rich_text'])}\n{self.jsons2md(value['children'])}"
        return noop

    @rule
    def block_to_do(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "to_do":
            return f"- [ ] {self.json2md(value['to_do']['rich_text'])}{self.jsons2md(value['children'])}"
        return noop

    @rule
    def block_code(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "code":
            return f"```\n{self.json2md(value['code']['rich_text'])}\n```"
        return noop

    @rule
    def block_table(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "table":
            lines = []
            table = value["children"]
            header = table[0]["table_row"]["cells"]
            lines.append(
                "|" + "|".join([self.json2md(cell[0]["text"]) for cell in header]) + "|"
            )
            lines.append("|" + "|".join(["---" for _ in header]) + "|")
            for child in table[1:]:
                row = child["table_row"]["cells"]
                lines.append(
                    "|"
                    + "|".join([self.json2md(cell[0]["text"]) for cell in row])
                    + "|"
                )
            lines.append("")
            return "\n".join(lines)
        return noop

    @rule
    def block_toggle(self, value, prv=None, nxt=None):
        if isinstance(value, dict) and value.get("type", "") == "toggle":
            return f"<details>\n<summary>{self.json2md(value['toggle']['rich_text'])}</summary>\n{self.jsons2md(value['children'])}</details>"
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
                "id",
            ):  # TODO: split this out. misc shouldnt be needed?
                if key in value:
                    return self.json2md(value[key])
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
            if cur["type"] != (nxt and nxt["type"]):
                result += "\n"
            if (md := self.json2md(cur, prv, nxt)) is not noop:
                result += "\n" + md
            else:
                raise NotImplementedError(f"Unsupported block type: {cur['type']}")
        return result

    def page2md(self, blocks: List[dict]) -> str:
        """Converts a notion page to markdown."""
        markdown = f"# {self.metadata['Name']}\n\n"
        for key, value in self.metadata.items():
            if value:
                markdown += f"{key}: {value}\n"
        markdown += self.jsons2md(blocks)
        return markdown
