"""
Chess Post-Game Analyst Package
A professional chess game analysis tool
"""

__version__ = "1.0.0"
__author__ = "Lekhan"
__license__ = "MIT"

from .pgn_parser import PGNParser
from .analyzer import GameAnalyzer, AnalysisResult
from .classifier import MoveClassifier, MoveClassification
from .engine import StockfishEngine

__all__ = [
    "PGNParser",
    "GameAnalyzer",
    "AnalysisResult",
    "MoveClassifier",
    "MoveClassification",
    "StockfishEngine",
]
