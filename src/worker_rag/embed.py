import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig

load_dotenv()

MODEL = "text-embedding-004"
BATCH_SIZE = 100

_client = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.environ["GCP_PROJECT"],
            location=os.environ.get("EMBED_REGION", os.environ["GCP_REGION"]),
        )
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_client()
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.models.embed_content(
            model=MODEL,
            contents=batch,
            config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        vectors.extend([e.values for e in response.embeddings])
    return vectors


def embed_query(text: str) -> list[float]:
    client = get_client()
    response = client.models.embed_content(
        model=MODEL,
        contents=[text],
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return response.embeddings[0].values
