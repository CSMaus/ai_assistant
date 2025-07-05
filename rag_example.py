"""
RAG (Retrieval-Augmented Generation) example implementation for the AI assistant.
This module demonstrates a basic RAG system that can be integrated with the existing assistant.
"""

import os
import re
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity
import openai
import langdetect

# Constants
EMBEDDINGS_DIR = "embeddings"
DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_TOKENS_PER_CHUNK = 500

# Ensure directories exist
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

class Document:
    """Class representing a document with metadata"""
    def __init__(self, 
                 content: str, 
                 metadata: Dict[str, Any],
                 doc_id: str = None):
        self.content = content
        self.metadata = metadata
        self.doc_id = doc_id or metadata.get('source', 'unknown')
        
    def __str__(self):
        return f"Document(id={self.doc_id}, metadata={self.metadata})"

class DocumentProcessor:
    """Processes documents into chunks suitable for embedding"""
    
    def __init__(self, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def process_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Document:
        """
        Process a file into a Document object
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata
            
        Returns:
            Document object
        """
        if metadata is None:
            metadata = {}
            
        # Extract file information
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try another encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
                
        # Detect language if not specified
        if 'language' not in metadata:
            try:
                metadata['language'] = langdetect.detect(content)
            except:
                metadata['language'] = 'en'  # Default to English
                
        # Add file metadata
        metadata.update({
            'source': file_path,
            'filename': filename,
            'extension': file_ext,
            'created_at': os.path.getctime(file_path),
            'modified_at': os.path.getmtime(file_path)
        })
        
        # Create document
        return Document(content, metadata, doc_id=os.path.splitext(filename)[0])
    
    def chunk_document(self, document: Document) -> List[Dict[str, Any]]:
        """
        Split document into chunks with metadata
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        content = document.content
        
        # Simple chunking by paragraphs first
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Count tokens in this paragraph
            para_tokens = len(self.tokenizer.encode(para))
            
            # If adding this paragraph would exceed our chunk size, save current chunk and start a new one
            if current_tokens + para_tokens > MAX_TOKENS_PER_CHUNK and current_chunk:
                # Save current chunk
                chunk_data = {
                    "content": current_chunk,
                    "metadata": {**document.metadata, "chunk_id": len(chunks)},
                    "doc_id": document.doc_id
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap (include the last paragraph from previous chunk)
                current_chunk = para
                current_tokens = para_tokens
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                current_tokens += para_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_data = {
                "content": current_chunk,
                "metadata": {**document.metadata, "chunk_id": len(chunks)},
                "doc_id": document.doc_id
            }
            chunks.append(chunk_data)
        
        return chunks

class VectorStore:
    """Stores and retrieves document embeddings"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.chunks = []
        self.embeddings = []
        
    def add_document(self, document: Document, processor: DocumentProcessor):
        """
        Add a document to the vector store
        
        Args:
            document: Document to add
            processor: DocumentProcessor to chunk the document
        """
        # Chunk the document
        chunks = processor.chunk_document(document)
        
        # Create embeddings for chunks
        self._create_embeddings(chunks)
        
    def _create_embeddings(self, chunks: List[Dict[str, Any]]):
        """
        Create embeddings for document chunks
        
        Args:
            chunks: List of document chunks
        """
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            for chunk in chunks:
                # Check if we already have this chunk
                existing_chunk = next((c for c in self.chunks if 
                                     c["doc_id"] == chunk["doc_id"] and 
                                     c["metadata"]["chunk_id"] == chunk["metadata"]["chunk_id"]), None)
                
                if existing_chunk:
                    continue
                
                # Create embedding
                response = client.embeddings.create(
                    input=chunk["content"],
                    model="text-embedding-ada-002"
                )
                
                embedding = response.data[0].embedding
                
                # Store chunk and embedding
                self.chunks.append(chunk)
                self.embeddings.append(embedding)
                
            print(f"Created embeddings for {len(chunks)} chunks")
            
        except Exception as e:
            print(f"Error creating embeddings: {e}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for chunks similar to the query
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of chunks with similarity scores
        """
        if not self.chunks or not self.embeddings:
            print("No chunks or embeddings available.")
            return []
            
        try:
            # Create query embedding
            client = openai.OpenAI(api_key=self.api_key)
            query_response = client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = query_response.data[0].embedding
            
            # Calculate similarities
            similarities = []
            for i, embedding in enumerate(self.embeddings):
                similarity = cosine_similarity([query_embedding], [embedding])[0][0]
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top-k chunks
            results = []
            for i, similarity in similarities[:top_k]:
                chunk = self.chunks[i]
                results.append({
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "doc_id": chunk["doc_id"],
                    "similarity": float(similarity)
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def save(self, path: str = None):
        """
        Save vector store to disk
        
        Args:
            path: Directory to save to (default: EMBEDDINGS_DIR)
        """
        if path is None:
            path = EMBEDDINGS_DIR
            
        os.makedirs(path, exist_ok=True)
        
        try:
            with open(os.path.join(path, "vector_store.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": self.chunks,
                    "embeddings": self.embeddings
                }, f)
            print(f"Saved {len(self.chunks)} chunks with embeddings")
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def load(self, path: str = None):
        """
        Load vector store from disk
        
        Args:
            path: Directory to load from (default: EMBEDDINGS_DIR)
        """
        if path is None:
            path = EMBEDDINGS_DIR
            
        try:
            file_path = os.path.join(path, "vector_store.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.embeddings = data.get("embeddings", [])
                    print(f"Loaded {len(self.chunks)} chunks with embeddings")
            else:
                print("No vector store file found.")
        except Exception as e:
            print(f"Error loading vector store: {e}")

class RAGSystem:
    """Main RAG system that combines document processing, vector storage, and retrieval"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.processor = DocumentProcessor()
        self.vector_store = VectorStore(api_key=self.api_key)
        
        # Load existing vector store if available
        self.vector_store.load()
    
    def add_document_from_file(self, file_path: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a document from a file
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        try:
            # Process the document
            document = self.processor.process_file(file_path, metadata)
            
            # Add to vector store
            self.vector_store.add_document(document, self.processor)
            
            # Save vector store
            self.vector_store.save()
            
            return document.doc_id
        except Exception as e:
            print(f"Error adding document from file: {e}")
            return None
    
    def add_document_from_text(self, text: str, title: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a document from text
        
        Args:
            text: Document text
            title: Document title
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        try:
            if metadata is None:
                metadata = {}
            
            # Detect language if not specified
            if 'language' not in metadata:
                try:
                    metadata['language'] = langdetect.detect(text)
                except:
                    metadata['language'] = 'en'  # Default to English
            
            metadata.update({
                'source': 'text_input',
                'title': title
            })
            
            # Create document
            document = Document(text, metadata, doc_id=title)
            
            # Add to vector store
            self.vector_store.add_document(document, self.processor)
            
            # Save vector store
            self.vector_store.save()
            
            return document.doc_id
        except Exception as e:
            print(f"Error adding document from text: {e}")
            return None
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with similarity scores
        """
        return self.vector_store.search(query, top_k)
    
    def generate_augmented_prompt(self, query: str, system_prompt: str, top_k: int = 3) -> str:
        """
        Generate an augmented prompt with retrieved context
        
        Args:
            query: User query
            system_prompt: Original system prompt
            top_k: Number of chunks to retrieve
            
        Returns:
            Augmented system prompt
        """
        # Retrieve relevant chunks
        retrieved_chunks = self.retrieve(query, top_k)
        
        if not retrieved_chunks:
            return system_prompt
        
        # Format retrieved context
        context_text = "\n\n".join([
            f"--- Document: {chunk['doc_id']} ---\n{chunk['content']}"
            for chunk in retrieved_chunks
        ])
        
        # Augment system prompt
        augmented_prompt = f"""{system_prompt}

RETRIEVED CONTEXT:
{context_text}

Use the retrieved context to help answer the user's question when relevant. If the context doesn't contain relevant information, rely on your general knowledge. When using information from the context, indicate the source.
"""
        
        return augmented_prompt
    
    def answer_with_rag(self, query: str, system_prompt: str = None) -> str:
        """
        Generate an answer using RAG
        
        Args:
            query: User query
            system_prompt: Optional system prompt
            
        Returns:
            Generated answer
        """
        try:
            # Use default system prompt if none provided
            if system_prompt is None:
                system_prompt = """You are an AI assistant designed to help with PAUT (Phased Array Ultrasonic Testing) data analysis. 
Answer questions based on the retrieved context when available, and use your general knowledge when necessary."""
            
            # Generate augmented prompt
            augmented_prompt = self.generate_augmented_prompt(query, system_prompt)
            
            # Generate response
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": augmented_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"I encountered an error: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Initialize RAG system
    rag = RAGSystem()
    
    # Add a document
    doc_id = rag.add_document_from_text(
        """Phased Array Ultrasonic Testing (PAUT) is an advanced method of ultrasonic testing that uses multiple ultrasonic elements and electronic time delays to create beams that can be steered, scanned, swept, and focused electronically for fast inspection, full data storage, and multiple angle inspections.

PAUT offers several advantages over conventional ultrasonic testing:
1. Faster scanning of the test object
2. Inspection of complex geometries
3. Increased probability of detection of defects
4. Ability to save data for later analysis
5. Creation of C-scan images

Common defects detected by PAUT include:
- Cracks
- Lack of fusion
- Porosity
- Inclusions
- Wall thickness variations""",
        "paut_basics"
    )
    
    # Add another document
    doc_id2 = rag.add_document_from_text(
        """Signal-to-Noise Ratio (SNR) analysis in ultrasonic testing is a critical measurement that compares the level of the desired signal to the level of background noise. A higher SNR indicates a clearer signal and more reliable detection of defects.

SNR is calculated using the formula:
SNR = 20 * log10(Signal Amplitude / Noise Amplitude)

Factors affecting SNR in PAUT:
1. Transducer frequency
2. Material properties
3. Surface conditions
4. Electronic noise
5. Gain settings

To improve SNR:
- Use appropriate frequency transducers
- Apply proper coupling
- Optimize gain and filtering settings
- Use signal averaging techniques
- Select appropriate scan patterns""",
        "snr_analysis"
    )
    
    # Test retrieval
    results = rag.retrieve("How does phased array ultrasonic testing work?")
    print("\nRetrieval results:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f}):")
        print(f"Document: {result['doc_id']}")
        print(f"Content: {result['content'][:100]}...")
    
    # Test RAG answer generation
    answer = rag.answer_with_rag("What is SNR in ultrasonic testing and how can I improve it?")
    print("\nRAG Answer:")
    print(answer)
    
    # Test with a question that combines information from both documents
    answer2 = rag.answer_with_rag("How does PAUT help with defect detection and what role does SNR play?")
    print("\nRAG Answer (Combined Knowledge):")
    print(answer2)
