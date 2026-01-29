"""
Test suite for Move Classifier module
"""

import pytest
import chess

from chess_analyst.classifier import MoveClassifier, MoveClassification, ClassifiedMove


class TestMoveClassifier:
    """Tests for Move Classifier"""

    @pytest.fixture
    def classifier(self):
        """Create a move classifier instance"""
        return MoveClassifier(opening_moves=10)

    def test_classify_blunder(self, classifier):
        """Test blunder classification"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("d2d4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=15,
            eval_before=100,
            eval_after=-150,  # Lost 250 centipawns
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        assert classified.classification == MoveClassification.BLUNDER

    def test_classify_mistake(self, classifier):
        """Test mistake classification"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("d2d4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=15,
            eval_before=100,
            eval_after=-50,  # Lost 150 centipawns
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        assert classified.classification == MoveClassification.MISTAKE

    def test_classify_inaccuracy(self, classifier):
        """Test inaccuracy classification"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("d2d4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=15,
            eval_before=100,
            eval_after=30,  # Lost 70 centipawns
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        assert classified.classification == MoveClassification.INACCURACY

    def test_classify_good_move(self, classifier):
        """Test good move classification"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("d2d4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=15,
            eval_before=100,
            eval_after=85,  # Lost only 15 centipawns
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        assert classified.classification == MoveClassification.GOOD

    def test_classify_book_move(self, classifier):
        """Test book move classification"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("e2e4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=5,  # Within opening moves
            eval_before=20,
            eval_after=25,
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        assert classified.classification == MoveClassification.BOOK

    def test_get_symbol(self):
        """Test getting symbol for classification"""
        assert MoveClassifier.get_symbol(MoveClassification.BRILLIANT) == "✨"
        assert MoveClassifier.get_symbol(MoveClassification.BLUNDER) == "💥"
        assert MoveClassifier.get_symbol(MoveClassification.GOOD) == "✅"

    def test_to_dict(self, classifier):
        """Test classified move to dict conversion"""
        move = chess.Move.from_uci("e2e4")
        best_move = chess.Move.from_uci("d2d4")
        
        classified = classifier.classify_move(
            move=move,
            move_number=15,
            eval_before=100,
            eval_after=85,
            best_move=best_move,
            is_white=True,
            is_forced=False
        )
        
        result_dict = classified.to_dict()
        
        assert result_dict['move'] == "e2e4"
        assert result_dict['move_number'] == 15
        assert result_dict['player'] == "white"
        assert 'classification' in result_dict
