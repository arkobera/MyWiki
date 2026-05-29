from __future__ import annotations

from pathlib import Path

from backend.knowledge_graph import parse_index_markdown


def test_parse_index_markdown_accepts_path_input(tmp_path: Path) -> None:
    index_path = tmp_path / "index.md"
    index_path.write_text(
        """# Document Index

## Alpha

Summary:
Attention paper summary.

Keywords:
- Transformer
- Attention

Category:
Artificial Intelligence

File:
raw/alpha.pdf

Embedding ID:
embed-alpha
""",
        encoding="utf-8",
    )

    entries = parse_index_markdown(index_path)

    assert len(entries) == 1
    assert entries[0].document_name == "Alpha"
    assert entries[0].file_path == "raw/alpha.pdf"
    assert entries[0].embedding_id == "embed-alpha"
