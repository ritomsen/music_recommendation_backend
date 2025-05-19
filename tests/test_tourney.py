import json
import os
import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.rec_service.tourney import Tourney
from app.models.song import Pool_Song

def load_test_pool():
    """Load the most recent candidate pool from test results"""
    test_results_dir = os.path.join(os.path.dirname(__file__), 'test_results')
    files = [f for f in os.listdir(test_results_dir) if f.startswith('candidate_pool_results_')]
    if not files:
        raise FileNotFoundError("No candidate pool results found")
    
    # Get the most recent file
    latest_file = sorted(files)[-1]
    with open(os.path.join(test_results_dir, latest_file), 'r') as f:
        data = json.load(f)
    
    # Convert JSON data to Pool_Song objects
    return [Pool_Song(**song) for song in data]

class TestTourney:
    @pytest.fixture
    def tourney(self):
        """Create a Tourney instance with test data"""
        pool = load_test_pool()
        return Tourney(pool)
    
    def test_initialization(self, tourney):
        """Test that Tourney initializes correctly"""
        assert tourney.pool is not None
        assert len(tourney.song_scores) == len(tourney.pool)
        assert len(tourney.final_rankings) == 0
    
    def test_calculate_score(self, tourney):
        """Test score calculation for different round placements"""
        total_rounds = 5
        
        # Test first round elimination
        score1 = tourney._calculate_score(1, total_rounds)
        assert score1 > 0
        
        # Test final round
        score2 = tourney._calculate_score(total_rounds, total_rounds)
        assert score2 > score1  # Later rounds should have higher scores
    
    def test_run_tourney(self, tourney):
        """Test that running a tournament produces valid results"""
        results = tourney.run_tourney()
        
        # Check that we get results
        assert len(results) > 0
        
        # Check that results are properly formatted
        for song, score in results:
            assert isinstance(song, Pool_Song)
            assert isinstance(score, float)
            assert 0 <= score <= 100  # Scores should be probabilities between 0 and 100
    
    def test_get_top_recommendations(self, tourney):
        """Test getting top recommendations"""
        n = 3
        results = tourney.get_top_recommendations(n)
        
        # Check number of results
        assert len(results) == n
        
        # Check that results are sorted by score
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
        
        # Check that probabilities sum to approximately 100
        total_prob = sum(score for _, score in results)
        assert abs(total_prob - 100) < 0.01  # Allow for small floating point errors
    
    def test_empty_pool(self):
        """Test behavior with empty pool"""
        tourney = Tourney([])
        # Empty pool should return empty results without raising an error
        results = tourney.run_tourney()
        assert len(results) == 0
        assert len(tourney.final_rankings) == 0
        assert len(tourney.song_scores) == 0
    
    def test_single_song_pool(self):
        """Test behavior with single song in pool"""
        pool = [Pool_Song(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            img_link="",
            genre="Test Genre",
            description="Test Description",
            spotify_link="",
            popularity_score=0,
            release_date="2024-01-01",
            lyrics="Test Lyrics",
            comes_from="test"
        )]
        tourney = Tourney(pool)
        results = tourney.run_tourney()
        assert len(results) == 1
        assert results[0][1] == 100.0  # Single song should have 100% probability

    def test_two_song_pool(self):
        """Test behavior with exactly two songs in pool"""
        pool = [
            Pool_Song(
                title="Test Song 1",
                artist="Test Artist 1",
                album="Test Album",
                img_link="",
                genre="Test Genre",
                description="Test Description",
                spotify_link="",
                popularity_score=0,
                release_date="2024-01-01",
                lyrics="Test Lyrics",
                comes_from="test"
            ),
            Pool_Song(
                title="Test Song 2",
                artist="Test Artist 2",
                album="Test Album",
                img_link="",
                genre="Test Genre",
                description="Test Description",
                spotify_link="",
                popularity_score=0,
                release_date="2024-01-01",
                lyrics="Test Lyrics",
                comes_from="test"
            )
        ]
        tourney = Tourney(pool)
        results = tourney.run_tourney()
        assert len(results) == 2
        # Check that probabilities sum to 100
        total_prob = sum(score for _, score in results)
        assert abs(total_prob - 100) < 0.01 