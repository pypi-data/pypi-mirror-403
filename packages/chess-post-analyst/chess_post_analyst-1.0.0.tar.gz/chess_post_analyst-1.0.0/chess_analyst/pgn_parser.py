"""
PGN Parser Module
Handles parsing and loading of PGN (Portable Game Notation) files
"""

import chess.pgn
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PGNParser:
    """Parser for PGN chess game files"""

    def __init__(self, pgn_path: str):
        """
        Initialize PGN Parser

        Args:
            pgn_path: Path to PGN file
        """
        self.pgn_path = Path(pgn_path)
        if not self.pgn_path.exists():
            raise FileNotFoundError(f"PGN file not found: {pgn_path}")

    def load_game(self, game_number: int = 0) -> Optional[chess.pgn.Game]:
        """
        Load a specific game from the PGN file

        Args:
            game_number: Index of game to load (0-based)

        Returns:
            Chess game object or None if not found
        """
        try:
            with open(self.pgn_path, 'r', encoding='utf-8') as pgn_file:
                for i in range(game_number + 1):
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        if i == 0:
                            raise ValueError("No games found in PGN file")
                        else:
                            raise ValueError(f"Game {game_number} not found in PGN file")
                
                logger.info(f"Loaded game {game_number} from {self.pgn_path}")
                return game

        except Exception as e:
            logger.error(f"Error loading game: {e}")
            raise

    def load_all_games(self) -> List[chess.pgn.Game]:
        """
        Load all games from the PGN file

        Returns:
            List of chess game objects
        """
        games = []
        try:
            with open(self.pgn_path, 'r', encoding='utf-8') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    games.append(game)

            logger.info(f"Loaded {len(games)} games from {self.pgn_path}")
            return games

        except Exception as e:
            logger.error(f"Error loading games: {e}")
            raise

    def get_game_info(self, game: chess.pgn.Game) -> dict:
        """
        Extract metadata from a chess game

        Args:
            game: Chess game object

        Returns:
            Dictionary with game information
        """
        headers = game.headers
        return {
            "event": headers.get("Event", "Unknown"),
            "site": headers.get("Site", "Unknown"),
            "date": headers.get("Date", "Unknown"),
            "round": headers.get("Round", "Unknown"),
            "white": headers.get("White", "Unknown"),
            "black": headers.get("Black", "Unknown"),
            "result": headers.get("Result", "*"),
            "white_elo": headers.get("WhiteElo", "Unknown"),
            "black_elo": headers.get("BlackElo", "Unknown"),
            "time_control": headers.get("TimeControl", "Unknown"),
            "eco": headers.get("ECO", "Unknown"),
            "opening": headers.get("Opening", "Unknown"),
        }

    @staticmethod
    def validate_pgn(pgn_path: str) -> bool:
        """
        Validate if a file is a valid PGN file

        Args:
            pgn_path: Path to potential PGN file

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(pgn_path)
            if not path.exists():
                return False

            with open(path, 'r', encoding='utf-8') as pgn_file:
                game = chess.pgn.read_game(pgn_file)
                return game is not None

        except Exception:
            return False
