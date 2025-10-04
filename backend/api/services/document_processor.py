# backend/api/services/document_processor.py (Corrected)
import os
from typing import List, Dict
from pathlib import Path
import uuid

import pypdf
import docx
from sentence_transformers import SentenceTransformer

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vector_store = {}

    def process_documents(self, file_paths: List[str], job_id: str, job_statuses: Dict):
        print(f"Starting document processing for job_id: {job_id}")
        
        try:
            for file_path in file_paths:
                content, doc_type = self._extract_text(file_path)
                chunks = self.dynamic_chunking(content, doc_type)
                embeddings = self.embedding_model.encode(chunks, batch_size=32)
                
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    self.vector_store[chunk_id] = {
                        "content": chunk,
                        "embedding": embeddings[i],
                        "source": os.path.basename(file_path)
                    }
            # Set status to Complete when done
            job_statuses[job_id] = "Complete"
            print(f"Job {job_id} complete. Indexed {len(chunks)} chunks.")
        except Exception as e:
            job_statuses[job_id] = f"Failed: {e}"
            print(f"Job {job_id} failed: {e}")

    # ... (the rest of the file, _extract_text and dynamic_chunking, remains the same)
    def _extract_text(self, file_path: str) -> (str, str):
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.pdf':
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                text = "".join(page.extract_text() for page in reader.pages)
            return text, 'pdf'
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs)
            return text, 'docx'
        elif file_extension == '.txt':
            with open(file_path, 'r') as f:
                text = f.read()
            return text, 'txt'
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def dynamic_chunking(self, content: str, doc_type: str) -> List[str]:
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        return paragraphs