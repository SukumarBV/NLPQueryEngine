import os
from typing import List, Dict
from pathlib import Path
import uuid

# Import libraries for file processing
import pypdf
import docx

# Import for embeddings
from sentence_transformers import SentenceTransformer

class DocumentProcessor:
    """
    Processes uploaded documents by extracting text, chunking it intelligently,
    and generating embeddings for vector storage.
    """
    def __init__(self):
        # Load the pre-trained model once during initialization
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.vector_store = {} # Using a simple dict as a placeholder for a real vector DB

    def process_documents(self, file_paths: List[str], job_id: str) -> None:
        """
        Main function to process a batch of documents.
        This is designed to be run in a background task.
        """
        # In a real app, you'd update a database with the job status
        print(f"Starting document processing for job_id: {job_id}")
        
        for file_path in file_paths:
            try:
                content, doc_type = self._extract_text(file_path)
                chunks = self.dynamic_chunking(content, doc_type)
                
                # Generate embeddings in batches for efficiency
                embeddings = self.embedding_model.encode(chunks, batch_size=32)
                
                # Store with proper indexing for fast retrieval
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    self.vector_store[chunk_id] = {
                        "content": chunk,
                        "embedding": embeddings[i],
                        "source": os.path.basename(file_path)
                    }
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
        
        print(f"Job {job_id} complete. Indexed {len(self.vector_store)} chunks.")

    def _extract_text(self, file_path: str) -> (str, str):
        """Auto-detects file type and extracts raw text."""
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
        """
        Intelligent chunking based on document structure.
        This is a simplified example; more complex rules can be added.
        """
        # For reviews or contracts, splitting by paragraph is a good start
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # For resumes, you might look for keywords like "Experience", "Skills"
        # and try to keep those sections together.
        
        # We'll use a simple paragraph-based approach here.
        return paragraphs