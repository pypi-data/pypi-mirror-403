"""
Text Chunker

Splits text into meaningful chunks for embedding.
"""

import re
from typing import List, Dict, Any


def chunk_text(
    file_path: str,
    text: str,
    max_chunk_size: int = 512
) -> List[Dict[str, Any]]:
    """
    Chunk text into sentences/paragraphs.
    
    Strategy:
    - Split on paragraph boundaries (double newlines)
    - Within paragraphs, split on sentence boundaries (. ! ?)
    - Combine short sentences to reach target size (200-512 chars)
    - Preserve metadata (file path, chunk ID)
    
    Args:
        file_path: Source file path
        text: Text content to chunk
        max_chunk_size: Maximum characters per chunk (default: 512)
        
    Returns:
        List of chunks with metadata (file, chunk_id, text)
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    chunk_id = 0
    
    # Split into paragraphs (double newlines or single newlines)
    paragraphs = re.split(r'\n\s*\n', text)
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # If paragraph is small enough, use it as a chunk
        if len(paragraph) <= max_chunk_size:
            chunks.append({
                'file': file_path,
                'chunk_id': chunk_id,
                'text': paragraph
            })
            chunk_id += 1
            continue
        
        # Split paragraph into sentences
        # Match sentence endings: . ! ? followed by space or end of string
        sentences = re.split(r'([.!?]+(?:\s+|$))', paragraph)
        
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            combined = (sentence + punctuation).strip()
            if combined:
                combined_sentences.append(combined)
        
        # If no sentences found, treat whole paragraph as one chunk
        if not combined_sentences:
            # Split by max_chunk_size if too long
            for i in range(0, len(paragraph), max_chunk_size):
                chunk_text = paragraph[i:i + max_chunk_size].strip()
                if chunk_text:
                    chunks.append({
                        'file': file_path,
                        'chunk_id': chunk_id,
                        'text': chunk_text
                    })
                    chunk_id += 1
            continue
        
        # Combine sentences into chunks
        current_chunk = []
        current_length = 0
        
        for sentence in combined_sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed max size
            if current_length + sentence_length > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        'file': file_path,
                        'chunk_id': chunk_id,
                        'text': chunk_text
                    })
                    chunk_id += 1
                
                # Start new chunk with current sentence
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space
        
        # Save remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    'file': file_path,
                    'chunk_id': chunk_id,
                    'text': chunk_text
                })
                chunk_id += 1
    
    return chunks
