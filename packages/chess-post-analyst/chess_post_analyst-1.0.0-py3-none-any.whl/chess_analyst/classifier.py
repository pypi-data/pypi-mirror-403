"""
Move Classifier Module
Classifies chess moves as brilliant, good, inaccuracy, mistake, or blunder
"""

from enum import Enum
from dataclasses import dataclass
import chess


class MoveClassification(Enum):
    """Classification categories for chess moves"""
    BRILLIANT = "brilliant"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    BOOK = "book"  # Opening book move


@dataclass
class ClassifiedMove:
    """Data class for a classified chess move"""
    move: chess.Move
    move_number: int
    classification: MoveClassification
    evaluation_before: float
    evaluation_after: float
    eval_change: float
    best_move: chess.Move
    is_white: bool

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "move": self.move.uci(),
            "move_number": self.move_number,
            "classification": self.classification.value,
            "evaluation_before": self.evaluation_before,
            "evaluation_after": self.evaluation_after,
            "eval_change": self.eval_change,
            "best_move": self.best_move.uci() if self.best_move else None,
            "player": "white" if self.is_white else "black",
        }


class MoveClassifier:
    """Classifies chess moves based on evaluation changes"""

    # Thresholds for move classification (in centipawns)
    BLUNDER_THRESHOLD = -200  # Lost 2+ pawns of advantage
    MISTAKE_THRESHOLD = -100  # Lost 1+ pawn of advantage
    INACCURACY_THRESHOLD = -50  # Lost 0.5+ pawn of advantage
    BRILLIANT_THRESHOLD = 100  # Unexpected strong move that gains significant advantage

    def __init__(self, opening_moves: int = 10):
        """
        Initialize move classifier

        Args:
            opening_moves: Number of opening moves to treat as "book" moves
        """
        self.opening_moves = opening_moves

    def classify_move(
        self,
        move: chess.Move,
        move_number: int,
        eval_before: float,
        eval_after: float,
        best_move: chess.Move,
        is_white: bool,
        is_forced: bool = False,
    ) -> ClassifiedMove:
        """
        Classify a single chess move

        Args:
            move: The move that was played
            move_number: Move number in the game
            eval_before: Evaluation before the move (from player's perspective)
            eval_after: Evaluation after the move (from player's perspective)
            best_move: The best move in the position
            is_white: Whether white made the move
            is_forced: Whether the move was forced (only legal move)

        Returns:
            ClassifiedMove object
        """
        # Calculate evaluation change (negative means position got worse)
        eval_change = eval_after - eval_before

        # Classify the move
        if move_number <= self.opening_moves:
            classification = MoveClassification.BOOK
        elif is_forced:
            classification = MoveClassification.GOOD
        elif eval_change <= self.BLUNDER_THRESHOLD:
            classification = MoveClassification.BLUNDER
        elif eval_change <= self.MISTAKE_THRESHOLD:
            classification = MoveClassification.MISTAKE
        elif eval_change <= self.INACCURACY_THRESHOLD:
            classification = MoveClassification.INACCURACY
        elif move == best_move and eval_change >= self.BRILLIANT_THRESHOLD:
            classification = MoveClassification.BRILLIANT
        else:
            classification = MoveClassification.GOOD

        return ClassifiedMove(
            move=move,
            move_number=move_number,
            classification=classification,
            evaluation_before=eval_before,
            evaluation_after=eval_after,
            eval_change=eval_change,
            best_move=best_move,
            is_white=is_white,
        )

    @staticmethod
    def get_symbol(classification: MoveClassification) -> str:
        """
        Get symbolic representation of classification

        Args:
            classification: Move classification

        Returns:
            Symbol string
        """
        symbols = {
            MoveClassification.BRILLIANT: "✨",
            MoveClassification.GOOD: "✅",
            MoveClassification.INACCURACY: "⚠️",
            MoveClassification.MISTAKE: "❌",
            MoveClassification.BLUNDER: "💥",
            MoveClassification.BOOK: "📖",
        }
        return symbols.get(classification, "")

    @staticmethod
    def get_description(classification: MoveClassification) -> str:
        """
        Get text description of classification

        Args:
            classification: Move classification

        Returns:
            Description string
        """
        descriptions = {
            MoveClassification.BRILLIANT: "Brilliant move!",
            MoveClassification.GOOD: "Good move",
            MoveClassification.INACCURACY: "Inaccuracy",
            MoveClassification.MISTAKE: "Mistake",
            MoveClassification.BLUNDER: "Blunder!",
            MoveClassification.BOOK: "Book move",
        }
        return descriptions.get(classification, "Unknown")
