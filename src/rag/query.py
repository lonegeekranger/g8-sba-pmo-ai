import sys

from dotenv import load_dotenv
from openai import OpenAI

import os

from src.rag.embed import embed_query
from src.rag.load import get_collection

load_dotenv()

K = 5

SYSTEM_PROMPT = """Eres PMO-AI, un asistente que responde consultas sobre proyectos TI de una PMO.
Responde SOLO con base en el contexto entregado. Si el contexto no alcanza, dilo explícitamente.
Cada afirmación relevante debe citar su origen entre paréntesis con el formato (Fuente: <fuente>, Sección: <seccion>).
Responde en español, de forma concisa y estructurada."""


def retrieve(query: str, k: int = K) -> list[dict]:
    collection = get_collection()
    result = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=k,
    )
    hits = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": doc, **meta, "distance": dist})
    return hits


def ask(query: str) -> dict:
    hits = retrieve(query)
    context = "\n\n---\n\n".join(
        f"(Fuente: {h['fuente']}, Sección: {h['seccion']})\n{h['text']}" for h in hits
    )
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta: {query}"},
        ],
        temperature=0.2,
    )
    answer = response.choices[0].message.content
    sources = [{"fuente": h["fuente"], "seccion": h["seccion"]} for h in hits]
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    query = sys.argv[1]
    result = ask(query)
    print(result["answer"])
    print("\n--- Fuentes recuperadas ---")
    for s in result["sources"]:
        print(f"- {s['fuente']} :: {s['seccion']}")
