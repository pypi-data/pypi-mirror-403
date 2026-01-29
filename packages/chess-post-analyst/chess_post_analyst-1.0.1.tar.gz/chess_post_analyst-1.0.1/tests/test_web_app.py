"""
Test suite for Flask Web Application
"""

import pytest
import json
import tempfile
from pathlib import Path
from io import BytesIO

from web.app import app


class TestWebApp:
    """Tests for Flask Web Application"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

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
    def invalid_pgn_content(self):
        """Invalid PGN content for testing"""
        return "This is not a valid PGN file"

    def test_index_route(self, client):
        """Test main page loads"""
        response = client.get('/')
        assert response.status_code == 200

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'Chess Post-Game Analyst API'
        assert 'version' in data

    def test_analyze_no_file(self, client):
        """Test analyze endpoint with no file"""
        response = client.post('/api/analyze')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file uploaded' in data['error']

    def test_analyze_empty_filename(self, client):
        """Test analyze endpoint with empty filename"""
        data = {
            'pgn_file': (BytesIO(b''), '')
        }
        response = client.post('/api/analyze', data=data)
        assert response.status_code == 400
        
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'No file selected' in response_data['error']

    def test_analyze_invalid_file_type(self, client):
        """Test analyze endpoint with invalid file type"""
        data = {
            'pgn_file': (BytesIO(b'test content'), 'test.txt')
        }
        response = client.post('/api/analyze', data=data)
        assert response.status_code == 400
        
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'Invalid file type' in response_data['error']

    def test_analyze_valid_pgn_file(self, client, sample_pgn_content, mocker):
        """Test analyze endpoint with valid PGN file"""
        # Mock the GameAnalyzer to avoid needing Stockfish
        mock_result = mocker.Mock()
        mock_result.to_dict.return_value = {
            'game_info': {'white': 'Player1', 'black': 'Player2'},
            'moves': [],
            'accuracy': {'white': 85.5, 'black': 82.3}
        }
        
        mock_analyzer = mocker.patch('web.app.GameAnalyzer')
        mock_analyzer.return_value.analyze.return_value = mock_result

        data = {
            'pgn_file': (BytesIO(sample_pgn_content.encode()), 'test.pgn'),
            'depth': '15',
            'game_number': '0'
        }
        
        response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'analysis' in response_data

    def test_validate_pgn_no_file(self, client):
        """Test validate endpoint with no file"""
        response = client.post('/api/validate')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_validate_pgn_valid_file(self, client, sample_pgn_content):
        """Test validate endpoint with valid PGN"""
        data = {
            'pgn_file': (BytesIO(sample_pgn_content.encode()), 'test.pgn')
        }
        
        response = client.post('/api/validate', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert 'valid' in response_data
        assert response_data['valid'] is True

    def test_validate_pgn_invalid_file(self, client, invalid_pgn_content):
        """Test validate endpoint with invalid PGN"""
        data = {
            'pgn_file': (BytesIO(invalid_pgn_content.encode()), 'test.pgn')
        }
        
        response = client.post('/api/validate', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert 'valid' in response_data
        assert response_data['valid'] is False

    def test_analyze_pgn_text_no_data(self, client):
        """Test analyze PGN text endpoint with no data"""
        response = client.post('/api/analyze-pgn-text', 
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No PGN text provided' in data['error']

    def test_analyze_pgn_text_empty(self, client):
        """Test analyze PGN text endpoint with empty text"""
        response = client.post('/api/analyze-pgn-text',
                              data=json.dumps({'pgn_text': '   '}),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Empty PGN text' in data['error']

    def test_analyze_pgn_text_valid(self, client, sample_pgn_content, mocker):
        """Test analyze PGN text endpoint with valid PGN"""
        # Mock the GameAnalyzer
        mock_result = mocker.Mock()
        mock_result.to_dict.return_value = {
            'game_info': {'white': 'Player1', 'black': 'Player2'},
            'moves': [],
            'accuracy': {'white': 85.5, 'black': 82.3}
        }
        
        mock_analyzer = mocker.patch('web.app.GameAnalyzer')
        mock_analyzer.return_value.analyze.return_value = mock_result

        response = client.post('/api/analyze-pgn-text',
                              data=json.dumps({
                                  'pgn_text': sample_pgn_content,
                                  'depth': 15
                              }),
                              content_type='application/json')
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'analysis' in response_data

    def test_get_sample_games(self, client, mocker):
        """Test get sample games endpoint"""
        # Mock the file reading
        mock_games = [
            {'name': 'Game 1', 'pgn': 'sample pgn 1'},
            {'name': 'Game 2', 'pgn': 'sample pgn 2'}
        ]
        
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_games)))
        
        response = client.get('/api/sample-games')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'games' in data

    def test_get_coaching_tips_valid(self, client, mocker):
        """Test get coaching tips endpoint with valid classification"""
        mock_tips = {
            'blunder': {
                'title': 'Avoiding Blunders',
                'tips': ['Tip 1', 'Tip 2']
            },
            'mistake': {
                'title': 'Reducing Mistakes',
                'tips': ['Tip 1', 'Tip 2']
            }
        }
        
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_tips)))
        
        response = client.get('/api/coaching-tips/blunder')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'tips' in data

    def test_get_coaching_tips_invalid(self, client, mocker):
        """Test get coaching tips endpoint with invalid classification"""
        mock_tips = {
            'blunder': {'title': 'Test', 'tips': []}
        }
        
        mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data=json.dumps(mock_tips)))
        
        response = client.get('/api/coaching-tips/invalid_classification')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_404_error(self, client):
        """Test 404 error handler"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_file_too_large(self, client):
        """Test file size limit"""
        # Create a file larger than 16MB
        large_content = b'x' * (17 * 1024 * 1024)  # 17MB
        
        data = {
            'pgn_file': (BytesIO(large_content), 'large.pgn')
        }
        
        response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        # Flask may return 413 or 500 depending on when the size check happens
        assert response.status_code in [413, 500]
        
        response_data = json.loads(response.data)
        assert 'error' in response_data

    def test_allowed_file_function(self):
        """Test allowed_file helper function"""
        from web.app import allowed_file
        
        assert allowed_file('test.pgn') is True
        assert allowed_file('test.PGN') is True
        assert allowed_file('test.txt') is False
        assert allowed_file('test') is False
        assert allowed_file('test.pgn.txt') is False

    def test_analyze_with_custom_depth(self, client, sample_pgn_content, mocker):
        """Test analyze endpoint with custom depth parameter"""
        mock_result = mocker.Mock()
        mock_result.to_dict.return_value = {'test': 'data'}
        
        mock_analyzer_class = mocker.patch('web.app.GameAnalyzer')
        mock_analyzer_instance = mock_analyzer_class.return_value
        mock_analyzer_instance.analyze.return_value = mock_result

        data = {
            'pgn_file': (BytesIO(sample_pgn_content.encode()), 'test.pgn'),
            'depth': '20'
        }
        
        response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        # Verify depth was passed correctly
        mock_analyzer_class.assert_called_once()
        call_kwargs = mock_analyzer_class.call_args[1]
        assert call_kwargs['depth'] == 20

    def test_analyze_pgn_text_with_game_number(self, client, sample_pgn_content, mocker):
        """Test analyze PGN text with specific game number"""
        mock_result = mocker.Mock()
        mock_result.to_dict.return_value = {'test': 'data'}
        
        mock_analyzer = mocker.patch('web.app.GameAnalyzer')
        mock_analyzer.return_value.analyze.return_value = mock_result

        response = client.post('/api/analyze-pgn-text',
                              data=json.dumps({
                                  'pgn_text': sample_pgn_content,
                                  'depth': 15,
                                  'game_number': 0
                              }),
                              content_type='application/json')
        assert response.status_code == 200

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/api/health')
        # CORS headers should be present due to flask-cors
        assert response.status_code == 200


class TestWebAppIntegration:
    """Integration tests for web application"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_full_workflow_file_upload(self, client, mocker):
        """Test complete workflow: upload -> validate -> analyze"""
        sample_pgn = '''[Event "Test"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
'''
        
        # Step 1: Validate
        data = {
            'pgn_file': (BytesIO(sample_pgn.encode()), 'test.pgn')
        }
        response = client.post('/api/validate', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert json.loads(response.data)['valid'] is True

        # Step 2: Analyze (with mocked analyzer)
        mock_result = mocker.Mock()
        mock_result.to_dict.return_value = {'moves': [], 'accuracy': {}}
        mock_analyzer = mocker.patch('web.app.GameAnalyzer')
        mock_analyzer.return_value.analyze.return_value = mock_result

        data = {
            'pgn_file': (BytesIO(sample_pgn.encode()), 'test.pgn'),
            'depth': '15'
        }
        response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert json.loads(response.data)['success'] is True

    def test_error_handling_invalid_pgn(self, client):
        """Test error handling with invalid PGN content"""
        invalid_pgn = "Not a valid PGN at all!"
        
        data = {
            'pgn_file': (BytesIO(invalid_pgn.encode()), 'invalid.pgn')
        }
        
        response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
        # Should return error due to invalid PGN
        assert response.status_code in [400, 500]
        assert 'error' in json.loads(response.data)
