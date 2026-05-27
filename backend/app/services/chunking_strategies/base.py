from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class Chunk:
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str) -> List[Chunk]:
        pass