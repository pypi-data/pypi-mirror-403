"""
Stockfish Engine Module
Wrapper for Stockfish chess engine integration
"""

import chess
import chess.engine
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class StockfishEngine:
    """Wrapper for Stockfish chess engine"""

    def __init__(self, engine_path: Optional[str] = None, depth: int = 15, threads: int = 1):
        """
        Initialize Stockfish engine

        Args:
            engine_path: Path to Stockfish executable (auto-detect if None)
            depth: Analysis depth (higher = stronger but slower)
            threads: Number of CPU threads to use
        """
        self.engine_path = engine_path or self._find_stockfish()
        self.depth = depth
        self.threads = threads
        self.engine: Optional[chess.engine.SimpleEngine] = None

    def _find_stockfish(self) -> str:
        """
        Attempt to auto-detect Stockfish installation

        Returns:
            Path to Stockfish executable
        """
        # Common Stockfish locations
        common_paths = [
            "stockfish",  # In PATH
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "C:\\Program Files\\Stockfish\\stockfish.exe",
            "C:\\stockfish\\stockfish.exe",
        ]

        for path in common_paths:
            if Path(path).exists() or path == "stockfish":
                logger.info(f"Found Stockfish at: {path}")
                return path

        raise FileNotFoundError(
            "Stockfish not found. Please install Stockfish and provide the path. "
            "Download from: https://stockfishchess.org/download/"
        )

    def start(self):
        """Start the chess engine"""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self.engine.configure({"Threads": self.threads})
            logger.info(f"Stockfish engine started (depth={self.depth}, threads={self.threads})")
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            raise

    def stop(self):
        """Stop the chess engine"""
        if self.engine:
            self.engine.quit()
            logger.info("Stockfish engine stopped")

    def analyze_position(self, board: chess.Board) -> Dict:
        """
        Analyze a chess position

        Args:
            board: Chess board position

        Returns:
            Dictionary with analysis results
        """
        if not self.engine:
            raise RuntimeError("Engine not started. Call start() first.")

        try:
            info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
            
            score = info.get("score")
            pov_score = score.white() if score else None

            return {
                "score": pov_score.score(mate_score=10000) if pov_score else 0,
                "mate": pov_score.mate() if pov_score else None,
                "best_move": info.get("pv", [None])[0] if "pv" in info else None,
                "depth": info.get("depth", 0),
                "pv": info.get("pv", []),
            }
        except Exception as e:
            logger.error(f"Error analyzing position: {e}")
            return {
                "score": 0,
                "mate": None,
                "best_move": None,
                "depth": 0,
                "pv": [],
            }

    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get the best move for a position

        Args:
            board: Chess board position

        Returns:
            Best move or None
        """
        if not self.engine:
            raise RuntimeError("Engine not started. Call start() first.")

        try:
            result = self.engine.play(board, chess.engine.Limit(depth=self.depth))
            return result.move
        except Exception as e:
            logger.error(f"Error getting best move: {e}")
            return None

    def evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """
        Evaluate the quality of a specific move

        Args:
            board: Chess board before the move
            move: Move to evaluate

        Returns:
            Evaluation difference (negative means move loses advantage)
        """
        # Analyze position before move
        before_analysis = self.analyze_position(board)
        before_score = before_analysis["score"]

        # Make the move
        board_copy = board.copy()
        board_copy.push(move)

        # Analyze position after move
        after_analysis = self.analyze_position(board_copy)
        after_score = after_analysis["score"]

        # Calculate score change from moving player's perspective
        if board.turn == chess.WHITE:
            return after_score - before_score
        else:
            return before_score - after_score

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
