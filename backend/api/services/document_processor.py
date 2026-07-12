import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import uuid

import numpy as np
import pypdf
import docx
from google import genai
from google.genai import types

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("GEMINI_EMBEDDING_DIM", "768"))
MAX_CHUNK_CHARS = 1200
EMBED_BATCH_SIZE = 100  # Gemini API batch limit per request


class DocumentProcessor:
    """
    Handles document ingestion: extraction, chunking, and embedding.
    Embeddings are generated via the Gemini API instead of a local
    sentence-transformers model so the service stays lightweight enough
    to run on small (e.g. 512MB) hosts.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        # chunk_id -> {"content": str, "embedding": np.ndarray, "source": str}
        self.vector_store: Dict[str, dict] = {}

    def process_documents(self, file_paths: List[str], job_id: str, job_statuses: Dict):
        print(f"Starting document processing for job_id: {job_id}")

        if not self.client:
            job_statuses[job_id] = "Failed: GEMINI_API_KEY is not configured on the server."
            self._cleanup(file_paths)
            return

        total_chunks = 0
        try:
            for file_path in file_paths:
                content, doc_type = self._extract_text(file_path)
                chunks = self.dynamic_chunking(content, doc_type)
                if not chunks:
                    continue

                embeddings = self._embed_texts(chunks, task_type="RETRIEVAL_DOCUMENT")
                for chunk, embedding in zip(chunks, embeddings):
                    chunk_id = str(uuid.uuid4())
                    self.vector_store[chunk_id] = {
                        "content": chunk,
                        "embedding": embedding,
                        "source": os.path.basename(file_path),
                    }
                total_chunks += len(chunks)

            job_statuses[job_id] = "Complete"
            print(f"Job {job_id} complete. Indexed {total_chunks} chunks.")
        except Exception as e:
            job_statuses[job_id] = f"Failed: {e}"
            print(f"Job {job_id} failed: {e}")
        finally:
            self._cleanup(file_paths)

    def _cleanup(self, file_paths: List[str]):
        if not file_paths:
            return
        upload_dir = os.path.dirname(file_paths[0])
        try:
            shutil.rmtree(upload_dir, ignore_errors=True)
        except OSError:
            pass

    def _embed_texts(self, texts: List[str], task_type: str) -> List[np.ndarray]:
        results: List[np.ndarray] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[i : i + EMBED_BATCH_SIZE]
            response = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type, output_dimensionality=EMBEDDING_DIM
                ),
            )
            results.extend(np.array(e.values, dtype=np.float32) for e in response.embeddings)
        return results

    def embed_query(self, query: str) -> np.ndarray:
        return self._embed_texts([query], task_type="RETRIEVAL_QUERY")[0]

    def _extract_text(self, file_path: str) -> Tuple[str, str]:
        file_extension = Path(file_path).suffix.lower()
        if file_extension == ".pdf":
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, "pdf"
        elif file_extension == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs)
            return text, "docx"
        elif file_extension == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            return text, "txt"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def dynamic_chunking(self, content: str, doc_type: str) -> List[str]:
        """
        Groups paragraphs into chunks up to MAX_CHUNK_CHARS so embedding
        requests stay small while preserving paragraph boundaries.
        """
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks: List[str] = []
        buffer = ""
        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= MAX_CHUNK_CHARS:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = paragraph
        if buffer:
            chunks.append(buffer)
        return chunks
