import re
from typing import List
from .base import Chunk, ChunkingStrategy

class HeadingChunkingStrategy(ChunkingStrategy):
    def __init__(self, levels: List[int] = None):
        self.levels = levels or [1, 2, 3]
    
    def chunk(self, text: str) -> List[Chunk]:
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        start_pos = 0
        
        for i, line in enumerate(lines):
            if any(line.startswith('#' * level) for level in self.levels):
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append(Chunk(
                        text=chunk_text.strip(),
                        start_pos=start_pos,
                        end_pos=start_pos + len(chunk_text),
                        chunk_index=len(chunks)
                    ))
                    start_pos += len(chunk_text) + 1
                    current_chunk = []
            current_chunk.append(line)
        
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text.strip(),
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text),
                chunk_index=len(chunks)
            ))
        
        return chunks

class ParagraphChunkingStrategy(ChunkingStrategy):
    def __init__(self, min_length: int = 50):
        self.min_length = min_length
    
    def chunk(self, text: str) -> List[Chunk]:
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        start_pos = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if len(paragraph) >= self.min_length:
                chunks.append(Chunk(
                    text=paragraph,
                    start_pos=start_pos,
                    end_pos=start_pos + len(paragraph),
                    chunk_index=i
                ))
            start_pos += len(paragraph) + 2
        
        return chunks

class LengthChunkingStrategy(ChunkingStrategy):
    def __init__(self, max_tokens: int = 500, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
    
    def chunk(self, text: str) -> List[Chunk]:
        chunks = []
        tokens = text.split()
        start_pos = 0
        
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = ' '.join(chunk_tokens)
            
            if i > 0 and self.overlap > 0:
                overlap_tokens = tokens[max(0, i - self.overlap):i]
                chunk_text = ' '.join(overlap_tokens) + ' ' + chunk_text
            
            chunks.append(Chunk(
                text=chunk_text,
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text),
                chunk_index=len(chunks)
            ))
            
            start_pos += len(chunk_text) + 1
            i += self.max_tokens - self.overlap
        
        return chunks