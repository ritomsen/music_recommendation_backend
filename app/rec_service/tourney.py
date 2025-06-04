import json
import random
import asyncio
import concurrent.futures
import math
from typing import List, Dict, Callable, Any, Tuple
from app.models.song import Pool_Song
from app.services.open_ai_service import OpenAIService


#TODO CHECK CODE because I think there are small optimizations that can be made

class Tourney:
    def __init__(self, pool: List[Pool_Song], openai_service: OpenAIService, prompt_template: str, num_tournaments: int = 3):
        self.pool = pool
        self.song_scores: Dict[Pool_Song, List[float]] = {song: [] for song in pool}
        self.final_rankings: Dict[Pool_Song, float] = {}
        self.openai_service = openai_service
        self.prompt_template = prompt_template
        self.num_tournaments = num_tournaments
        print(f"Initialized tournament with {len(pool)} songs")
        
    async def _blackbox_compare(self, song1: Pool_Song, song2: Pool_Song) -> Pool_Song:
        """
        Use AI service to compare two songs and return the winner
        """
        print(f"Comparing songs: {song1.title} vs {song2.title}")
        result = await self.openai_service.get_recommendation(song1, song2, self.prompt_template)
        winner = song1 if result == 0 else song2
        print(f"Winner: {winner.title}")
        return winner
    
    async def _run_single_tourney(self, songs: List[Pool_Song], tourney_id: int) -> Dict[Pool_Song, int]:
        """Run a single tournament and return the placement of each song"""
        if not songs:
            print(f"Tournament {tourney_id}: Empty song list provided")
            return {}
            
        print(f"Starting tournament {tourney_id} with {len(songs)} songs")
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
                    print(f"Tournament {tourney_id} Round {round_num}: {remaining_songs[i].title} gets a bye")
            
            print(f"Tournament {tourney_id} Round {round_num}: {len(matchups)} matchups")
            
            # Run matchups concurrently using asyncio
            tasks = [self._blackbox_compare(s1, s2) for s1, s2 in matchups]
            winners = await asyncio.gather(*tasks)
            
            for (s1, s2), winner in zip(matchups, winners):
                next_round_songs.append(winner)
                loser = s2 if winner == s1 else s1
                eliminated_this_round.append(loser)
                print(f"Tournament {tourney_id} Round {round_num}: {winner.title} defeats {loser.title}")
            
            # Assign rounds reached to songs eliminated this round
            for song in eliminated_this_round:
                results[song] = round_num
            
            remaining_songs = next_round_songs
            eliminated_this_round = []
            round_num += 1
        
        # The last remaining song is the winner - it reached one round further
        if remaining_songs:
            results[remaining_songs[0]] = round_num + 1
            print(f"Tournament {tourney_id} completed. Winner: {remaining_songs[0].title}")
            
        return results
    
    def _calculate_score(self, rounds_reached: int, total_rounds: int) -> float:
        """
        Calculate a score based on how many rounds a song survived
        Higher scores for songs that reached later rounds
        """
        return (1.5 ** rounds_reached) / total_rounds
    
    async def run_tourney(self, num_recommendations: int = 5) -> List[Tuple[Pool_Song, float]]:
        """Run tournaments in parallel and calculate the average score for each song"""
        if not self.pool:
            print("Empty pool provided for tournament")
            return []
            
        tournament_tasks = []
        total_rounds = math.ceil(math.log2(len(self.pool)))
        number_of_tournaments = self.num_tournaments
        print(f"Starting {number_of_tournaments} tournaments with {len(self.pool)} songs")
        
        # Launch number_of_tournaments parallel tournaments with randomized song lists
        for i in range(number_of_tournaments):
            # Randomize the song list for this tournament
            randomized_songs = self.pool.copy()
            random.shuffle(randomized_songs)
            print(f"Tournament {i} starting with seed song: {randomized_songs[0].title} by {randomized_songs[0].artist}")
            # Submit the tournament task
            task = asyncio.create_task(self._run_single_tourney(randomized_songs, i))
            tournament_tasks.append(task)
        
        # Wait for all tournaments to complete
        tournament_results = await asyncio.gather(*tournament_tasks)
        print("All tournaments completed, processing results")
        
        # Process results from all tournaments
        for results in tournament_results:
            # Convert rounds reached to scores and store them
            for song, rounds_reached in results.items():
                score = self._calculate_score(rounds_reached, total_rounds)
                self.song_scores[song].append(score)
        
        # Calculate average scores for each song
        for song, scores in self.song_scores.items():
            if scores:  # Ensure the song participated in at least one tournament
                self.final_rankings[song] = sum(scores) / len(scores)
            else:
                self.final_rankings[song] = 0
        
        output = self.get_top_recommendations(num_recommendations)
        print(f"Tournament complete. Top {num_recommendations} recommendations generated")
        
        return output
    
    def get_top_recommendations(self, n: int = 5) -> List[Tuple[Pool_Song, float]]:
        """
        Get the top n songs with temperature-based softmax probabilities.
        Returns a list of tuples (song, probability)
        """
        if not self.final_rankings:
            print("Attempted to get recommendations before running tournament")
            raise RuntimeError("Must run tournament first")
            
        # Get the top n songs
        top_songs = sorted(
            self.final_rankings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        print(f"Top song ALL SONGS: {top_songs}")
        top_songs = top_songs[:n]
        
        if not top_songs:
            print("No songs found in final rankings")
            return []
        
        print("Top songs by score: " + ", ".join([f"{song.title} ({score:.2f})" for song, score in top_songs]))
        
        # Apply softmax to convert scores to probabilities
        songs, scores = zip(*top_songs)
        
        # Temperature parameter (higher = more uniform distribution)
        temperature = 5.0
        
        # Apply softmax function with temperature and numerical stability
        max_score = max(scores)
        exp_scores = [math.exp((score - max_score) / temperature) for score in scores]
        sum_exp_scores = sum(exp_scores)
        softmax_probs = [100 * (exp_score / sum_exp_scores) for exp_score in exp_scores]
        
        # Log final probabilities
        for song, prob in zip(songs, softmax_probs):
            print(f"Final probability for {song.title}: {prob:.2f}%")
        
        # Return songs with their probabilities
        return list(zip(songs, softmax_probs))
