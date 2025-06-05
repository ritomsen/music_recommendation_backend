from typing import List, Callable, Optional, Dict, Tuple
import random
import asyncio
from collections import Counter
from app.models.song import Pool_Song
from app.services.service_instances import openai_service

class GeneticAlgorithm:
    def __init__(
        self,
        candidate_pool: List[Pool_Song],
        population_size: int = 30,
        mutation_rate: float = 0.1,
        generations: int = 10,
        weather_data: dict = None,
        user_context: dict = None,
        image_analysis: dict = None
    ):
        self.candidate_pool = candidate_pool
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.current_population: List[Pool_Song] = []
        self.fitness_scores: Dict[Pool_Song, float] = {}  # Changed to dict for explicit mapping
        self.weather_data = weather_data
        self.user_context = user_context
        self.image_analysis = image_analysis
        self.fitness_cache: Dict[str, float] = {}  # Cache for fitness scores using song ID as key

    def print_population(self):
        for index, song in enumerate(self.current_population):
            print(f"#{index}: {song.title} by {song.artist}, Fitness score: {self.fitness_scores.get(song, 'N/A')}")
            
    async def fitness_function(self, song: Pool_Song) -> Tuple[Pool_Song, float]:
        """Fitness function for a song with caching"""
        # Check if we have a cached score for this song
        song_id = song.title + " " + song.artist
        if song_id in self.fitness_cache:
            print(f"Cache hit for song {song.title} by {song.artist}")
            return (song, self.fitness_cache[song_id])
        
        # If not in cache, compute the score
        print(f"Cache miss for song {song.title} by {song.artist}")
        fitness_score = await openai_service.generate_fitness_scores(song, self.weather_data, self.user_context, self.image_analysis)
        print(f"Fitness score for song {song.title} by {song.artist}: {fitness_score}")
        # Store in cache
        self.fitness_cache[song_id] = fitness_score
        return (song, fitness_score)

    async def initialize_population(self) -> None:
        """Initialize the population by randomly sampling from candidate pool"""
        self.current_population = random.sample(self.candidate_pool, self.population_size)
        print("Initial population:")
        self.print_population()
        print("--------------------------------")
        
    async def _evaluate_population(self) -> None:
        """Evaluate fitness of all songs in current population concurrently"""
        # Create tasks for all fitness evaluations
        tasks = [self.fitness_function(song) for song in self.current_population]
        # Run all tasks concurrently and gather results
        results = await asyncio.gather(*tasks)
        # Update fitness scores dictionary
        self.fitness_scores = {song: score for song, score in results}
    async def _select_survivors(self) -> List[Pool_Song]:
        """Select top 50% of songs based on fitness"""
        # Sort songs by their fitness scores
        sorted_songs = sorted(
            self.current_population,
            key=lambda song: self.fitness_scores.get(song, float('-inf')),
            reverse=True
        )
        # Take top 50%
        return sorted_songs[:len(sorted_songs)//2]

    def _mutate_song(self, song: Pool_Song) -> Pool_Song:
        """Mutate a song with probability mutation_rate"""
        if random.random() < self.mutation_rate:
            # # 50% chance of similar artist mutation, 50% chance of random mutation
            # if random.random() < 0.5:
            #     # Find songs from same artist
            #     similar_songs = [s for s in self.candidate_pool if s.artist == song.artist]
            #     if similar_songs:
            #         return random.choice(similar_songs)
            # Random mutation
            return random.choice(self.candidate_pool)
        return song

    async def _create_next_generation(self, survivors: List[Pool_Song]) -> None:
        """Create next generation from survivors"""
        next_generation = []
        for survivor in survivors:
            # Create two children for each survivor
            child1 = self._mutate_song(survivor)
            child2 = self._mutate_song(survivor)
            next_generation.extend([child1, child2])
        
        # If we have too many songs, randomly remove some
        if len(next_generation) > self.population_size:
            next_generation = random.sample(next_generation, self.population_size)
        
        self.current_population = next_generation

    async def run(self) -> Pool_Song:
        """Run the genetic algorithm and return the best song"""
        await self.initialize_population()
        for _ in range(self.generations):
            await self._evaluate_population()
            print(f"Generation {_} evaluated")
            self.print_population()
            print("--------------------------------")
            survivors = await self._select_survivors()
            await self._create_next_generation(survivors)
        
        print("Final population:")
        self.print_population()
        print("--------------------------------")
        print(f"Fitness cache size: {len(self.fitness_cache)}")
        # Find most frequent song in final population
        song_counts = Counter(self.current_population)
        song = song_counts.most_common(1)
        if song[0][1] > 1:
            return song[0][0]
        else:
            print("No clear winner, Getting best fitness song")
            await self._evaluate_population()
            return self.get_best_song()

    async def get_best_song(self) -> Optional[Pool_Song]:
        """Get the song with highest fitness in current population"""
        if not self.current_population:
            return None
        return max(self.current_population, key=lambda song: self.fitness_scores.get(song, float('-inf')))
