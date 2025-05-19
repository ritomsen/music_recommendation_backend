import random
import threading
import concurrent.futures
import math
from typing import List, Dict, Callable, Any, Tuple
from app.models.song import Pool_Song

#TODO CHECK CODE because I think there are small optimizations that can be made

class Tourney:
    def __init__(self, pool: List[Pool_Song]):
        self.pool = pool
        self.song_scores: Dict[Pool_Song, List[float]] = {song: [] for song in pool}
        self.final_rankings: Dict[Pool_Song, float] = {}
        
    def _blackbox_compare(self, song1: Pool_Song, song2: Pool_Song) -> Pool_Song:
        """
        Placeholder for the AI service function that will decide which song wins.
        Will be implemented later.
        """
        # This is just a placeholder - the actual implementation will be provided later
        return song1  # Default return for now
    
    def _run_single_tourney(self, songs: List[Pool_Song], tourney_id: int) -> Dict[Pool_Song, int]:
        """Run a single tournament and return the placement of each song"""
        if not songs:
            return {}
            
        results = {}
        remaining_songs = songs.copy()
        
        # Track the round number (used for scoring)
        round_num = 0
        eliminated_this_round = []
        
        while len(remaining_songs) > 1:
            round_num += 1
            next_round_songs = []
            matchups = []
            
            # Create matchups for this round
            for i in range(0, len(remaining_songs), 2):
                if i + 1 < len(remaining_songs):
                    matchups.append((remaining_songs[i], remaining_songs[i+1]))
                else:
                    # If odd number of songs, one gets a bye to next round
                    next_round_songs.append(remaining_songs[i])
            
            # Run matchups in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                future_to_matchup = {
                    executor.submit(self._blackbox_compare, s1, s2): (s1, s2) 
                    for s1, s2 in matchups
                }
                
                for future in concurrent.futures.as_completed(future_to_matchup):
                    s1, s2 = future_to_matchup[future]
                    try:
                        winner = future.result()
                        next_round_songs.append(winner)
                        loser = s2 if winner == s1 else s1
                        eliminated_this_round.append(loser)
                    except Exception as e:
                        print(f"Error in matchup {s1.id} vs {s2.id}: {e}")
            
            # Assign rounds reached to songs eliminated this round
            for song in eliminated_this_round:
                results[song] = round_num
            
            remaining_songs = next_round_songs
            eliminated_this_round = []
            round_num += 1
        
        # The last remaining song is the winner - it reached one round further
        if remaining_songs:
            results[remaining_songs[0]] = round_num + 1
            
        return results
    
    def _calculate_score(self, rounds_reached: int, total_rounds: int) -> float:
        """
        Calculate a score based on how many rounds a song survived
        Higher scores for songs that reached later rounds
        """
        # Use a smaller base for exponential growth and scale by total rounds
        return (1.5 ** rounds_reached) / total_rounds
    
    def run_tourney(self) -> List[Tuple[Pool_Song, float]]:
        """Run 8 tournaments in parallel and calculate the average score for each song"""
        if not self.pool:
            return []
            
        tournament_futures = []
        total_rounds = math.ceil(math.log2(len(self.pool)))

        # Launch 8 parallel tournaments with randomized song lists
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for i in range(8):
                # Randomize the song list for this tournament
                randomized_songs = self.pool.copy()
                random.shuffle(randomized_songs)
                print("Start of tournament", i, randomized_songs[0].title, randomized_songs[0].artist)
                # Submit the tournament task
                future = executor.submit(self._run_single_tourney, randomized_songs, i)
                tournament_futures.append(future)
            
            # Collect results from all tournaments
            for future in concurrent.futures.as_completed(tournament_futures):
                try:
                    tournament_results = future.result()
                    
                    # Convert rounds reached to scores and store them
                    for song, rounds_reached in tournament_results.items():
                        score = self._calculate_score(rounds_reached, total_rounds)
                        self.song_scores[song].append(score)
                except Exception as e:
                    print(f"Error in tournament: {e}")
        
        # Calculate average scores for each song
        for song, scores in self.song_scores.items():
            if scores:  # Ensure the song participated in at least one tournament
                self.final_rankings[song] = sum(scores) / len(scores)
            else:
                self.final_rankings[song] = 0
        
        n=5
        output = self.get_top_recommendations(n)

        
        return output
    
    def get_top_recommendations(self, n: int = 5) -> List[Tuple[Pool_Song, float]]:
        """
        Get the top n songs with temperature-based softmax probabilities.
        Returns a list of tuples (song, probability)
        """
        if not self.final_rankings:
            self.run_tourney()
            
        # Get the top n songs
        top_songs = sorted(
            self.final_rankings.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
        
        if not top_songs:
            return []
        
        print("Top songs", top_songs)
        
        # Apply softmax to convert scores to probabilities
        songs, scores = zip(*top_songs)
        
        # Temperature parameter (higher = more uniform distribution)
        temperature = 2.0
        
        # Apply softmax function with temperature and numerical stability
        max_score = max(scores)
        exp_scores = [math.exp((score - max_score) / temperature) for score in scores]
        sum_exp_scores = sum(exp_scores)
        softmax_probs = [100 * (exp_score / sum_exp_scores) for exp_score in exp_scores]
        
        # Return songs with their probabilities
        return list(zip(songs, softmax_probs))
