import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chunking_strategies.base import Chunk, BaseChunkingStrategy


class TestChunkDataclass:
    def test_chunk_creation(self):
        chunk = Chunk(index=0, text="Test content", start_pos=0, end_pos=12)
        
        assert chunk.index == 0
        assert chunk.text == "Test content"
        assert chunk.start_pos == 0
        assert chunk.end_pos == 12
        assert chunk.metadata is None

    def test_chunk_with_metadata(self):
        metadata = {"source": "test", "page_id": "123"}
        chunk = Chunk(index=1, text="Content", start_pos=0, end_pos=7, metadata=metadata)
        
        assert chunk.metadata == metadata


class TestBaseChunkingStrategy:
    def test_abstract_methods(self):
        class ConcreteStrategy(BaseChunkingStrategy):
            strategy_name = "concrete"
            
            async def chunk(self, text: str, config: dict):
                return []
        
        strategy = ConcreteStrategy()
        assert strategy.strategy_name == "concrete"
