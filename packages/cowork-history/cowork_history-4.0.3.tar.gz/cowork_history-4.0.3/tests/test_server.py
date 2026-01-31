"""Basic tests for cowork-history server."""

import os
import sys

# Set test environment before imports
os.environ["OLLAMA_URL"] = "http://localhost:11434"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text"

import pytest


class TestImports:
    """Test that all modules can be imported."""

    def test_import_server(self):
        """Test that the server module can be imported."""
        from src import cowork_history_server

        assert cowork_history_server.mcp is not None

    def test_import_main(self):
        """Test that main function exists."""
        from src.cowork_history_server import main

        assert callable(main)


class TestPathReconstructor:
    """Test the PathReconstructor class."""

    def test_reconstruct_home_path(self):
        """Test reconstructing a path starting with home directory."""
        from src.cowork_history_server import PathReconstructor

        reconstructor = PathReconstructor()
        # This will vary by system, just test it doesn't crash
        result = reconstructor.reconstruct("-Users-test-project")
        # Result may be None if path doesn't exist, that's OK
        assert result is None or isinstance(result, str)

    def test_cache_works(self):
        """Test that path caching works."""
        from src.cowork_history_server import PathReconstructor

        reconstructor = PathReconstructor()
        # First call
        result1 = reconstructor.reconstruct("-nonexistent-path")
        # Second call should use cache
        result2 = reconstructor.reconstruct("-nonexistent-path")
        assert result1 == result2


class TestFTSQuery:
    """Test FTS query preparation."""

    def test_single_word(self):
        """Test single word query."""
        from src.cowork_history_server import prepare_fts_query

        result = prepare_fts_query("test")
        assert "test*" in result

    def test_multiple_words(self):
        """Test multiple word query."""
        from src.cowork_history_server import prepare_fts_query

        result = prepare_fts_query("test query")
        assert "test*" in result
        assert "query*" in result

    def test_exact_phrase_passthrough(self):
        """Test that queries with operators pass through."""
        from src.cowork_history_server import prepare_fts_query

        result = prepare_fts_query("test AND query")
        assert result == "test AND query"

    def test_quoted_passthrough(self):
        """Test that quoted queries pass through."""
        from src.cowork_history_server import prepare_fts_query

        result = prepare_fts_query('"exact phrase"')
        assert result == '"exact phrase"'


class TestEmbeddings:
    """Test embedding utilities."""

    def test_embedding_roundtrip(self):
        """Test embedding to/from bytes conversion."""
        from src.cowork_history_server import bytes_to_embedding, embedding_to_bytes

        original = [0.1, 0.2, 0.3, 0.4, 0.5]
        as_bytes = embedding_to_bytes(original)
        restored = bytes_to_embedding(as_bytes)

        assert restored is not None
        assert len(restored) == len(original)
        for a, b in zip(original, restored):
            assert abs(a - b) < 0.0001

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from src.cowork_history_server import cosine_similarity

        # Same vector should have similarity 1.0
        v = [1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 0.0001

        # Orthogonal vectors should have similarity 0.0
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        assert abs(cosine_similarity(v1, v2)) < 0.0001

        # Opposite vectors should have similarity -1.0
        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v1, v2) - (-1.0)) < 0.0001


class TestSystemCheck:
    """Test system requirement checking."""

    def test_system_check_returns_dict(self):
        """Test that system check returns expected structure."""
        from src.cowork_history_server import _check_system_requirements

        result = _check_system_requirements()

        assert isinstance(result, dict)
        assert "platform" in result
        assert "is_macos" in result
        assert "ram_gb" in result
        assert "issues" in result
        assert "recommendations" in result


class TestResponseFormat:
    """Test response formatting."""

    def test_format_empty_results(self):
        """Test formatting empty results."""
        from src.cowork_history_server import ResponseFormat, format_results

        result = format_results([], ResponseFormat.MARKDOWN, "Test")
        assert "no test found" in result.lower()

    def test_format_json(self):
        """Test JSON formatting."""
        import json

        from src.cowork_history_server import ResponseFormat, format_results

        results = [{"session_id": "test123", "topic": "Test topic"}]
        result = format_results(results, ResponseFormat.JSON, "Test")

        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert "results" in parsed
