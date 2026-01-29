"""
Test suite for PGN Parser module
"""

import pytest
import tempfile
from pathlib import Path
import chess.pgn

from chess_analyst.pgn_parser import PGNParser


class TestPGNParser:
    """Tests for PGN Parser"""

    @pytest.fixture
    def sample_pgn_content(self):
        """Sample PGN content for testing"""
        return '''[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O 1-0
'''

    @pytest.fixture
    def temp_pgn_file(self, sample_pgn_content):
        """Create a temporary PGN file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pgn', delete=False) as f:
            f.write(sample_pgn_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_init_with_valid_file(self, temp_pgn_file):
        """Test initialization with valid PGN file"""
        parser = PGNParser(temp_pgn_file)
        assert parser.pgn_path == Path(temp_pgn_file)

    def test_init_with_invalid_file(self):
        """Test initialization with non-existent file"""
        with pytest.raises(FileNotFoundError):
            PGNParser("nonexistent.pgn")

    def test_load_game(self, temp_pgn_file):
        """Test loading a game from PGN file"""
        parser = PGNParser(temp_pgn_file)
        game = parser.load_game(0)
        
        assert game is not None
        assert isinstance(game, chess.pgn.Game)

    def test_get_game_info(self, temp_pgn_file):
        """Test extracting game information"""
        parser = PGNParser(temp_pgn_file)
        game = parser.load_game(0)
        info = parser.get_game_info(game)
        
        assert info['event'] == "Test Game"
        assert info['white'] == "Player1"
        assert info['black'] == "Player2"
        assert info['result'] == "1-0"

    def test_validate_pgn_valid(self, temp_pgn_file):
        """Test PGN validation with valid file"""
        assert PGNParser.validate_pgn(temp_pgn_file) is True

    def test_validate_pgn_invalid(self):
        """Test PGN validation with invalid file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a PGN file")
            temp_path = f.name
        
        try:
            assert PGNParser.validate_pgn(temp_path) is False
        finally:
            Path(temp_path).unlink(missing_ok=True)
