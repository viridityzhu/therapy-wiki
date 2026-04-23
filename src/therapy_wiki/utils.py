"""Generic helpers."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"


def extract_date_from_name(path: Path) -> Optional[str]:
    patterns = [
        r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)",
        r"(20\d{2})\.([01]\d)\.([0-3]\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, path.stem)
        if match:
            return "{}-{}-{}".format(*match.groups())
    return None


def iso_date_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).date().isoformat()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def short_ts(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def flatten_text_lines(chunks: Iterable[str]) -> str:
    return "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def safe_title(text: str, fallback: str) -> str:
    normalized = text.strip().splitlines()[0].strip() if text.strip() else ""
    return normalized[:80] if normalized else fallback


def top_keywords(text: str, limit: int = 8) -> List[str]:
    stopwords = {
        "然后",
        "就是",
        "那个",
        "这个",
        "我们",
        "你们",
        "他们",
        "自己",
        "觉得",
        "一个",
        "因为",
        "所以",
        "但是",
        "还是",
        "如果",
        "已经",
        "有点",
    }
    candidates = re.findall(r"[\u4e00-\u9fff]{2,6}", text)
    scores: Dict[str, int] = {}
    for candidate in candidates:
        if candidate in stopwords:
            continue
        scores[candidate] = scores.get(candidate, 0) + 1
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:limit]]

