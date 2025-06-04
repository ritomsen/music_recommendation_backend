from typing import List, Callable, Optional
import random
from collections import Counter
from app.models.song import Pool_Song

class GeneticAlgorithm:
    def __init__(
        self,
        candidate_pool: List[Pool_Song],
        population_size: int = 100,
        mutation_rate: float = 0.1,
        generations: int = 50,
        fitness_function: Callable[[Pool_Song], float] = None
    ):
        self.candidate_pool = candidate_pool
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.fitness_function = fitness_function
        self.current_population: List[Pool_Song] = []
        self.fitness_scores: List[float] = []

    def initialize_population(self) -> None:
        """Initialize the population by randomly sampling from candidate pool"""
        self.current_population = random.sample(self.candidate_pool, self.population_size)
        self._evaluate_population()

    def _evaluate_population(self) -> None:
        """Evaluate fitness of all songs in current population"""
        self.fitness_scores = [self.fitness_function(song) for song in self.current_population]

    def _select_survivors(self) -> List[Pool_Song]:
        """Select top 50% of songs based on fitness"""
        # Pair songs with their fitness scores
        song_fitness_pairs = list(zip(self.current_population, self.fitness_scores))
        # Sort by fitness (descending)
        sorted_pairs = sorted(song_fitness_pairs, key=lambda x: x[1], reverse=True)
        # Take top 50%
        survivors = [song for song, _ in sorted_pairs[:len(sorted_pairs)//2]]
        return survivors

    def _mutate_song(self, song: Pool_Song) -> Pool_Song:
        """Mutate a song with probability mutation_rate"""
        if random.random() < self.mutation_rate:
            # 50% chance of similar artist mutation, 50% chance of random mutation
            if random.random() < 0.5:
                # Find songs from same artist
                similar_songs = [s for s in self.candidate_pool if s.artist == song.artist]
                if similar_songs:
                    return random.choice(similar_songs)
            # Random mutation
            return random.choice(self.candidate_pool)
        return song

    def _create_next_generation(self, survivors: List[Pool_Song]) -> None:
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
        self._evaluate_population()

    def run(self) -> Pool_Song:
        """Run the genetic algorithm and return the best song"""
        self.initialize_population()
        
        for _ in range(self.generations):
            survivors = self._select_survivors()
            self._create_next_generation(survivors)
        
        # Find most frequent song in final population
        song_counts = Counter(self.current_population)
        return song_counts.most_common(1)[0][0]

    def get_best_song(self) -> Optional[Pool_Song]:
        """Get the song with highest fitness in current population"""
        if not self.current_population:
            return None
        best_idx = self.fitness_scores.index(max(self.fitness_scores))
        return self.current_population[best_idx]
