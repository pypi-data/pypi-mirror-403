from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_sections() -> tuple[tuple[str, str], ...]:
    res_dir = Path(__file__).parent.parent / "resources" / "translate"
    sections: list[tuple[str, str]] = []

    for md_file in sorted(res_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                text = text[end + 3:].lstrip("\n")

        h2_title = md_file.stem.replace("_", " ").title()
        h3_title: str | None = None
        current_content = ""

        for line in text.splitlines(keepends=True):
            if line.startswith("## "):
                _flush(sections, h2_title, h3_title, current_content)
                h2_title = line[3:].strip()
                h3_title = None
                current_content = ""
            elif line.startswith("### "):
                _flush(sections, h2_title, h3_title, current_content)
                h3_title = line[4:].strip()
                current_content = ""
            elif line.startswith("# ") and not line.startswith("## "):
                continue
            else:
                current_content += line

        _flush(sections, h2_title, h3_title, current_content)

    return tuple(sections)


def _flush(sections: list[tuple[str, str]], h2_title: str, h3_title: str | None, content: str) -> None:
    text = content.strip()
    if not text:
        return
    title = f"{h2_title} > {h3_title}" if h3_title else h2_title
    sections.append((title, text))


def lookup_translation(topic: str) -> str:
    sections = _load_sections()
    topic_lower = topic.lower()
    keywords = topic_lower.split()

    scored: list[tuple[float, str, str]] = []
    for title, content in sections:
        title_lower = title.lower()
        score: float = 3 if topic_lower in title_lower else 0
        score += sum(1 for kw in keywords if kw in title_lower)
        if score == 0:
            preview = content[:300].lower()
            score = sum(0.3 for kw in keywords if kw in preview)
        if score > 0:
            scored.append((score, title, content))

    if not scored:
        titles = sorted(set(t for t, _ in sections))
        return f"No match for '{topic}'. Available topics:\n" + "\n".join(f"- {t}" for t in titles)

    scored.sort(key=lambda x: -x[0])

    result_parts: list[str] = []
    total = 0
    for _, title, content in scored[:3]:
        chunk = f"## {title}\n\n{content}"
        if total + len(chunk) > 4000 and result_parts:
            break
        result_parts.append(chunk)
        total += len(chunk)

    return "\n\n---\n\n".join(result_parts)
