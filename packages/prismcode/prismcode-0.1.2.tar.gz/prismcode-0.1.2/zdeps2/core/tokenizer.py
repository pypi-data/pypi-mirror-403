from pathlib import Path
from typing import Union
import tiktoken

_encoding = None


def _get_encoding():
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding("cl100k_base")
    return _encoding


def count_tokens(text: str) -> int:
    if not isinstance(text, str) or not text:
        return 0
    try:
        return len(_get_encoding().encode(text))
    except Exception:
        return len(text.split())


def count_lines(filepath: Union[str, Path]) -> int:
    try:
        with open(filepath, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def read_file_content(filepath: Union[str, Path]) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"
