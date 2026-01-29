"""
Game Analyzer Module
Main analysis engine for chess games
"""

import chess
import chess.pgn
from typing import List, Optional
from dataclasses import dataclass
import logging

from .engine import StockfishEngine
from .classifier import MoveClassifier, ClassifiedMove, MoveClassification

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete analysis result for a chess game"""
    game_info: dict
    classified_moves: List[ClassifiedMove]
    white_accuracy: float
    black_accuracy: float
    total_moves: int
    white_stats: dict
    black_stats: dict
    critical_moments: List[dict]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "game_info": self.game_info,
            "moves": [move.to_dict() for move in self.classified_moves],
            "white_accuracy": round(self.white_accuracy, 2),
            "black_accuracy": round(self.black_accuracy, 2),
            "total_moves": self.total_moves,
            "white_stats": self.white_stats,
            "black_stats": self.black_stats,
            "critical_moments": self.critical_moments,
        }


class GameAnalyzer:
    """Analyzes chess games using Stockfish engine"""

    def __init__(
        self,
        engine_path: Optional[str] = None,
        depth: int = 15,
        threads: int = 1,
        opening_moves: int = 10,
    ):
        """
        Initialize game analyzer

        Args:
            engine_path: Path to Stockfish executable
            depth: Analysis depth
            threads: Number of CPU threads
            opening_moves: Number of opening moves to skip in accuracy calculation
        """
        self.engine = StockfishEngine(engine_path, depth, threads)
        self.classifier = MoveClassifier(opening_moves)
        self.opening_moves = opening_moves

    def analyze(self, game: chess.pgn.Game, game_info: dict) -> AnalysisResult:
        """
        Analyze a complete chess game

        Args:
            game: Chess game object
            game_info: Game metadata dictionary

        Returns:
            AnalysisResult object with complete analysis
        """
        logger.info(f"Starting analysis of game: {game_info.get('white')} vs {game_info.get('black')}")

        classified_moves = []
        board = game.board()
        move_number = 1

        # Start the engine
        with self.engine:
            for node in game.mainline():
                move = node.move
                is_white = board.turn == chess.WHITE

                # Get evaluation before move
                analysis_before = self.engine.analyze_position(board)
                eval_before = analysis_before["score"]
                best_move = analysis_before["best_move"]

                # Make the move
                board.push(move)

                # Get evaluation after move (flip perspective)
                analysis_after = self.engine.analyze_position(board)
                eval_after = -analysis_after["score"]  # Negate because turn switched

                # Check if move was forced
                board.pop()
                is_forced = len(list(board.legal_moves)) == 1
                board.push(move)

                # Classify the move
                classified_move = self.classifier.classify_move(
                    move=move,
                    move_number=move_number,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    best_move=best_move,
                    is_white=is_white,
                    is_forced=is_forced,
                )

                classified_moves.append(classified_move)
                move_number += 1

                logger.debug(f"Move {move_number-1}: {move.uci()} - {classified_move.classification.value}")

        # Calculate statistics
        white_stats = self._calculate_stats(classified_moves, is_white=True)
        black_stats = self._calculate_stats(classified_moves, is_white=False)

        # Calculate accuracy
        white_accuracy = self._calculate_accuracy(classified_moves, is_white=True)
        black_accuracy = self._calculate_accuracy(classified_moves, is_white=False)

        # Find critical moments
        critical_moments = self._find_critical_moments(classified_moves)

        logger.info(f"Analysis complete. White accuracy: {white_accuracy:.1f}%, Black accuracy: {black_accuracy:.1f}%")

        return AnalysisResult(
            game_info=game_info,
            classified_moves=classified_moves,
            white_accuracy=white_accuracy,
            black_accuracy=black_accuracy,
            total_moves=len(classified_moves),
            white_stats=white_stats,
            black_stats=black_stats,
            critical_moments=critical_moments,
        )

    def _calculate_stats(self, moves: List[ClassifiedMove], is_white: bool) -> dict:
        """Calculate move statistics for one player"""
        player_moves = [m for m in moves if m.is_white == is_white and m.move_number > self.opening_moves]

        if not player_moves:
            return {
                "brilliant": 0,
                "good": 0,
                "inaccuracies": 0,
                "mistakes": 0,
                "blunders": 0,
                "total": 0,
            }

        return {
            "brilliant": sum(1 for m in player_moves if m.classification == MoveClassification.BRILLIANT),
            "good": sum(1 for m in player_moves if m.classification == MoveClassification.GOOD),
            "inaccuracies": sum(1 for m in player_moves if m.classification == MoveClassification.INACCURACY),
            "mistakes": sum(1 for m in player_moves if m.classification == MoveClassification.MISTAKE),
            "blunders": sum(1 for m in player_moves if m.classification == MoveClassification.BLUNDER),
            "total": len(player_moves),
        }

    def _calculate_accuracy(self, moves: List[ClassifiedMove], is_white: bool) -> float:
        """
        Calculate player accuracy percentage

        Accuracy is based on how close played moves are to optimal moves
        """
        player_moves = [m for m in moves if m.is_white == is_white and m.move_number > self.opening_moves]

        if not player_moves:
            return 100.0

        total_error = 0
        for move in player_moves:
            # Error is how much evaluation dropped (capped at 500 centipawns)
            error = min(abs(min(move.eval_change, 0)), 500)
            total_error += error

        # Convert error to accuracy (lower error = higher accuracy)
        avg_error = total_error / len(player_moves)
        accuracy = 100 * (1 - avg_error / 500)

        return max(0.0, min(100.0, accuracy))

    def _find_critical_moments(self, moves: List[ClassifiedMove], limit: int = 5) -> List[dict]:
        """Find the most critical moments in the game"""
        critical = []

        for move in moves:
            if move.classification in [MoveClassification.BLUNDER, MoveClassification.BRILLIANT]:
                critical.append({
                    "move_number": move.move_number,
                    "move": move.move.uci(),
                    "classification": move.classification.value,
                    "eval_change": round(move.eval_change, 2),
                    "best_move": move.best_move.uci() if move.best_move else None,
                    "player": "White" if move.is_white else "Black",
                })

        # Sort by absolute evaluation change
        critical.sort(key=lambda x: abs(x["eval_change"]), reverse=True)

        return critical[:limit]
