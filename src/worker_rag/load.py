import os
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from src.worker_rag.chunk import chunk_markdown
from src.worker_rag.embed import embed_texts

load_dotenv()

COLLECTION = "pmo_docs"


def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=os.environ["CHROMA_PATH"])
    return client.get_or_create_collection(COLLECTION)


def load_directory(data_dir: str) -> None:
    collection = get_collection()
    files = sorted(Path(data_dir).glob("*.md"))
    if not files:
        print(f"No hay archivos .md en {data_dir}")
        return
    for path in files:
        fuente = path.name
        chunks = chunk_markdown(path.read_text(), fuente)
        ids = [f"{fuente}::{i}" for i in range(len(chunks))]
        embeddings = embed_texts([c.text for c in chunks])
        collection.upsert(
            ids=ids,
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )
        print(f"{fuente}: {len(chunks)} chunks cargados")


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/"
    load_directory(data_dir)
    print(f"Total en colección: {get_collection().count()} chunks")
