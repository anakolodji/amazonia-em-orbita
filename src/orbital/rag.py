from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CORPUS_DIR = Path(__file__).resolve().parents[2] / "docs" / "rag_corpus"


@dataclass(frozen=True)
class RAGSnippet:
    title: str
    source: str
    text: str
    score: int

    def as_prompt_block(self) -> str:
        return f"[{self.title} | {self.source}] {self.text}"


def retrieve_humanitarian_context(
    query: str,
    *,
    corpus_dir: str | Path = DEFAULT_CORPUS_DIR,
    top_k: int = 3,
) -> list[RAGSnippet]:
    query_tokens = _tokenize(query)
    snippets: list[RAGSnippet] = []

    for path in sorted(Path(corpus_dir).glob("*.md")):
        title, paragraphs = _read_markdown_chunks(path)
        for paragraph in paragraphs:
            paragraph_tokens = _tokenize(paragraph)
            score = len(query_tokens.intersection(paragraph_tokens))
            if score:
                snippets.append(
                    RAGSnippet(
                        title=title,
                        source=path.name,
                        text=paragraph,
                        score=score,
                    )
                )

    return sorted(snippets, key=lambda item: item.score, reverse=True)[:top_k]


def build_humanitarian_query(context: dict[str, float | str]) -> str:
    return (
        f"prioridade {context['priority']} comunidade {context['name']} "
        f"territorio {context['territory']} chuva {context['rainfall']} "
        f"isolamento {context['isolation']} casos sanitarios {context['sanitary_cases']} "
        f"area afetada {context['affected']} risco ambiental {context['environmental']}"
    )


def format_rag_snippets(snippets: list[RAGSnippet]) -> str:
    if not snippets:
        return "Nenhum trecho RAG local foi recuperado."
    return "\n".join(f"- {snippet.as_prompt_block()}" for snippet in snippets)


def _read_markdown_chunks(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    title = path.stem.replace("_", " ").title()
    if lines and lines[0].startswith("# "):
        title = lines[0].removeprefix("# ").strip()

    body = "\n".join(line for line in lines if not line.startswith("#"))
    paragraphs = [
        " ".join(paragraph.split())
        for paragraph in re.split(r"\n\s*\n", body)
        if paragraph.strip()
    ]
    return title, paragraphs


def _tokenize(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    tokens = set(re.findall(r"[a-z0-9]{3,}", ascii_text))
    return tokens.difference(
        {
            "com",
            "para",
            "por",
            "das",
            "dos",
            "uma",
            "que",
            "deve",
            "devem",
            "quando",
        }
    )
