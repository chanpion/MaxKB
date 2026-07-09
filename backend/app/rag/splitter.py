# coding=utf-8
"""Text splitter ported from MaxKB's common/utils/split_model.py.

Pure, dependency-free port of the legacy ``SplitModel`` so the new FastAPI
service can turn a parsed document (markdown/plain text) into the same
``{title, content}`` paragraph structure the Django ``knowledge`` app produced.
No Django / jieba imports — keeps the RAG pipeline async-friendly (call from a
thread pool if needed).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Pattern tables (identical to legacy default_split_pattern in split_model.py)
# ---------------------------------------------------------------------------
_MD_PATTERN: List[re.Pattern[str]] = [
    re.compile(r"(?<=^)# .*|(?<=\n)# .*"),
    re.compile(r"(?<=\n)(?<!#)## (?!#).*|(?<=^)(?<!#)## (?!#).*"),
    re.compile(r"(?<=\n)(?<!#)### (?!#).*|(?<=^)(?<!#)### (?!#).*"),
    re.compile(r"(?<=\n)(?<!#)#### (?!#).*|(?<=^)(?<!#)#### (?!#).*"),
    re.compile(r"(?<=\n)(?<!#)##### (?!#).*|(?<=^)(?<!#)##### (?!#).*"),
    re.compile(r"(?<=\n)(?<!#)###### (?!#).*|(?<=^)(?<!#)###### (?!#).*"),
]
_DEFAULT_PATTERN: List[re.Pattern[str]] = [
    re.compile(r"(?<!\n)\n\n+"),
]

_TITLE_SPECIAL_CHARS = ["#", "\n", "\r", "\\s"]
_REPLACE_MAP = [
    (re.compile(r"\n+"), "\n"),
    (re.compile(r" +"), " "),
    (re.compile(r"#+"), ""),
    (re.compile(r"\t+"), ""),
]


# ---------------------------------------------------------------------------
# Low-level helpers (ported verbatim in behaviour)
# ---------------------------------------------------------------------------
def mask_code_blocks(text: str) -> str:
    """Mask code-block contents with spaces so inner '#' are not seen as titles."""
    result = list(text)
    for match in re.finditer(r"```[^\n]*\n.*?```", text, re.DOTALL):
        start, end = match.start(), match.end()
        inner_start = text.index("\n", start) + 1
        closing_fence_start = text.rindex("```", start, end)
        for i in range(inner_start, closing_fence_start):
            if result[i] != "\n":
                result[i] = " "
    return "".join(result)


def re_findall(pattern: Any, text: str) -> List[str]:
    if pattern is None:
        return []
    if isinstance(pattern, str) and (not pattern or not pattern.strip()):
        return []
    try:
        result = re.findall(pattern, text, flags=0)
    except re.error:
        return []
    flat: List[str] = []
    for row in result:
        items = list(row) if isinstance(row, tuple) else [row]
        flat.extend([r for r in items if r is not None and len(r) > 0])
    return flat


def _to_tree_obj(content: str, state: str = "title") -> Dict[str, Any]:
    return {"content": content, "state": state}


def _filter_special_symbol(content: Dict[str, Any]) -> Dict[str, Any]:
    content["content"] = content["content"]
    return content


def _remove_special_symbol(str_source: str) -> str:
    return str_source


def filter_special_char(content: str) -> str:
    out = content
    for key, value in _REPLACE_MAP:
        out = re.sub(key, value, out)
    return out


def parse_level(text: str, pattern: str) -> List[Dict[str, Any]]:
    masked_text = mask_code_blocks(text)
    level_content_list = [
        _to_tree_obj(r[0:255]) for r in re_findall(pattern, masked_text) if r is not None
    ]
    filtered = [
        item
        for item in level_content_list
        if item["content"].strip(" ") and item["content"].replace("#", "").strip(" ")
    ]
    return [_filter_special_symbol(item) for item in filtered]


def parse_title_level(text: str, content_level_pattern: List[str], index: int) -> List[Dict[str, Any]]:
    if index >= len(content_level_pattern):
        return []
    result = parse_level(text, content_level_pattern[index])
    if len(result) == 0 and len(content_level_pattern) > index:
        return parse_title_level(text, content_level_pattern, index + 1)
    return result


def get_level_block(text: str, level_content_list: List[Dict[str, Any]], index: int, cursor: int):
    start_content = level_content_list[index].get("content")
    next_content = (
        level_content_list[index + 1].get("content") if index + 1 < len(level_content_list) else None
    )
    start_index = text.index(start_content, cursor)
    end_index = text.index(next_content, start_index + 1) if next_content is not None else len(text)
    return text[start_index + len(start_content) : end_index], end_index


def smart_split_paragraph(content: str, limit: int) -> List[str]:
    result: List[str] = []
    temp_char, start = "", 0
    while (pos := content.find("\n", start)) != -1:
        split, start = content[start : pos + 1], pos + 1
        if len(temp_char + split) > limit:
            result.append(temp_char)
            temp_char = ""
        temp_char = temp_char + split
    temp_char = temp_char + content[start:]
    if len(temp_char) > 0:
        result.append(temp_char)
    pattern = r"[\S\s]{1," + str(limit) + "}"
    return [r for row in result for r in re.findall(pattern, row)]


def result_tree_to_paragraph(
    result_tree: List[Dict[str, Any]],
    result: List[Dict[str, Any]],
    parent_chain: List[str],
    with_filter: bool,
) -> List[Dict[str, Any]]:
    for item in result_tree:
        if item.get("state") == "block":
            result.append(
                {
                    "title": " ".join(parent_chain),
                    "content": filter_special_char(item.get("content")) if with_filter else item.get("content"),
                }
            )
        children = item.get("children")
        if children is not None and len(children) > 0:
            result_tree_to_paragraph(
                children,
                result,
                [*parent_chain, _remove_special_symbol(item.get("content", ""))],
                with_filter,
            )
    return result


class SplitModel:
    """Markdown / plain-text structure-aware splitter (ported)."""

    def __init__(self, content_level_pattern: List[Any], with_filter: bool = True, limit: int = 100000):
        self.content_level_pattern = content_level_pattern
        self.with_filter = with_filter
        if not isinstance(limit, int):
            limit = int(limit)
        if limit is None or limit > 100000:
            limit = 100000
        if limit < 50:
            limit = 50
        self.limit = limit

    def parse_to_tree(self, text: str, index: int = 0) -> List[Dict[str, Any]]:
        level_content_list = parse_title_level(text, self.content_level_pattern, index)
        if len(level_content_list) == 0:
            return [_to_tree_obj(row, "block") for row in smart_split_paragraph(text, limit=self.limit)]
        if index == 0 and text.lstrip().index(level_content_list[0]["content"].lstrip()) != 0:
            level_content_list.insert(0, _to_tree_obj(""))

        cursor = 0
        level_title_content_list = [item for item in level_content_list if item.get("state") == "title"]
        for i in range(len(level_title_content_list)):
            start_content = level_title_content_list[i].get("content")
            if cursor < text.index(start_content, cursor):
                for row in smart_split_paragraph(text[cursor : text.index(start_content, cursor)], limit=self.limit):
                    level_content_list.insert(0, _to_tree_obj(row, "block"))

            block, cursor = get_level_block(text, level_title_content_list, i, cursor)
            if len(block) == 0:
                continue
            children = self.parse_to_tree(text=block, index=index + 1)
            level_title_content_list[i]["children"] = children
            first_child_idx_in_block = block.lstrip().index(children[0]["content"].lstrip())
            if first_child_idx_in_block != 0:
                inner_children = self.parse_to_tree(block[:first_child_idx_in_block], index + 1)
                level_title_content_list[i]["children"].extend(inner_children)
        return level_content_list

    def parse(self, text: str) -> List[Dict[str, Any]]:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\0", "")
        result_tree = self.parse_to_tree(text, 0)
        result = result_tree_to_paragraph(result_tree, [], [], self.with_filter)
        title_list = list({row.get("title") for row in result})
        return [
            item
            for item in [self._post_reset_paragraph(row, title_list) for row in result]
            if "content" in item and len(item.get("content", "").strip()) > 0
        ]

    @staticmethod
    def _sub_title(paragraph: Dict[str, Any]) -> Dict[str, Any]:
        if "title" in paragraph:
            title = paragraph.get("title")
            if len(title) > 255:
                return {
                    **paragraph,
                    "title": title[0:255],
                    "content": title[255 : len(title)] + paragraph.get("content"),
                }
        return paragraph

    @staticmethod
    def _content_is_null(paragraph: Dict[str, Any], title_list: List[str]) -> Dict[str, Any]:
        if "title" in paragraph:
            title = paragraph.get("title")
            content = paragraph.get("content")
            if (content is None or len(content.strip()) == 0) and (title is not None and len(title) > 0):
                find = [t for t in title_list if t.__contains__(title) and t != title]
                if find:
                    return {"title": "", "content": ""}
                return {"title": "", "content": title}
        return paragraph

    @staticmethod
    def _filter_title_special_characters(paragraph: Dict[str, Any]) -> Dict[str, Any]:
        title = paragraph.get("title") if "title" in paragraph else ""
        for ch in _TITLE_SPECIAL_CHARS:
            title = title.replace(ch, "")
        return {**paragraph, "title": title}

    def _post_reset_paragraph(self, paragraph: Dict[str, Any], title_list: List[str]) -> Dict[str, Any]:
        result = self._content_is_null(paragraph, title_list)
        result = self._filter_title_special_characters(result)
        result = self._sub_title(result)
        return result


def get_split_model(filename: str, with_filter: bool = False, limit: int = 4096) -> SplitModel:
    """Return a SplitModel for the given filename extension (mirrors legacy)."""
    pattern = _MD_PATTERN if filename.lower().endswith(".md") else _DEFAULT_PATTERN
    return SplitModel(pattern, with_filter=with_filter, limit=limit)


def split_text(
    text: str,
    filename: str = "",
    with_filter: bool = False,
    limit: int = 4096,
) -> List[Dict[str, Any]]:
    """Split raw text into MaxKB-compatible paragraph dicts (title + content)."""
    return get_split_model(filename, with_filter=with_filter, limit=limit).parse(text)
