from dataclasses import dataclass, field
from datetime import date

MAX_CHARS = 800
OVERLAP = 150


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    sections = []
    current_header = "intro"
    buffer = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if buffer:
                sections.append((current_header, "\n".join(buffer).strip()))
            current_header = line.lstrip("# ").strip()
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        sections.append((current_header, "\n".join(buffer).strip()))
    return [(h, t) for h, t in sections if t]


def _split_with_overlap(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHARS, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - OVERLAP
    return chunks


def chunk_markdown(markdown: str, fuente: str) -> list[Chunk]:
    chunks = []
    for seccion, texto in _split_sections(markdown):
        for piece in _split_with_overlap(texto):
            chunks.append(Chunk(
                text=f"[{seccion}]\n{piece}",
                metadata={
                    "fuente": fuente,
                    "seccion": seccion,
                    "fecha_carga": date.today().isoformat(),
                },
            ))
    return chunks
