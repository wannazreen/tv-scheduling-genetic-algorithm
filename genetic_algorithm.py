
import csv
import random

# Genetic Algorithm parameters
GEN = 100
POP = 50
CO_R = 0.8
MUT_R = 0.2
EL_S = 2

# TV broadcasting time slots (06:00 - 23:00)
TIME_SLOTS = list(range(6, 24))

# Read program ratings from CSV
def read_csv_to_dict(file_path):
    program_ratings = {}

    with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        header = next(reader)

        if len(header) != 19:
            raise ValueError("CSV must contain 1 program column and 18 rating columns.")

        for row in reader:
            if len(row) != len(header):
                raise ValueError("Invalid number of columns in CSV.")

            program = row[0]
            ratings = [float(value) for value in row[1:]]

            if program in program_ratings:
                raise ValueError(f"Duplicate program: {program}")

            if any(value < 0 or value > 1 for value in ratings):
                raise ValueError("Ratings must be between 0 and 1.")

            program_ratings[program] = ratings

    if not program_ratings:
        raise ValueError("No programs found in CSV.")

    return program_ratings

# Create a random TV schedule
def create_schedule(programs, rng):

    if len(programs) > len(TIME_SLOTS):
        raise ValueError("Too many programs for available time slots.")

    # Include each program at least once
    schedule = programs.copy()

    # Fill remaining time slots with random programs
    remaining_slots = len(TIME_SLOTS) - len(schedule)

    schedule.extend(
        rng.choices(programs, k=remaining_slots)
    )

    # Shuffle the schedule
    rng.shuffle(schedule)

    return schedule

# Calculate schedule fitness
def fitness_function(schedule, ratings):

    if len(schedule) != len(TIME_SLOTS):
        raise ValueError("Invalid schedule length.")

    total_rating = 0

    for index, program in enumerate(schedule):
        total_rating += ratings[program][index]

    return total_rating

# Tournament selection
def selection(population, ratings, rng):

    # Randomly select three schedules
    candidates = rng.sample(population, 3)

    # Choose the schedule with highest fitness
    best_parent = max(
        candidates,
        key=lambda schedule: fitness_function(schedule, ratings)
    )

    return best_parent.copy()

# Repair schedules with missing programs
def repair_schedule(schedule, programs, rng):

    missing_programs = [
        program for program in programs
        if program not in schedule
    ]

    for program in missing_programs:

        repeated_positions = [
            index for index, value in enumerate(schedule)
            if schedule.count(value) > 1
        ]

        if not repeated_positions:
            raise ValueError("Unable to repair schedule.")

        position = rng.choice(repeated_positions)

        schedule[position] = program

    return schedule

# One-point crossover
def crossover(parent1, parent2, programs, rng):

    crossover_point = rng.randint(1, len(parent1) - 1)

    child1 = (
        parent1[:crossover_point]
        + parent2[crossover_point:]
    )

    child2 = (
        parent2[:crossover_point]
        + parent1[crossover_point:]
    )

    # Repair the children if necessary
    child1 = repair_schedule(child1, programs, rng)
    child2 = repair_schedule(child2, programs, rng)

    return child1, child2

# Mutation
def mutate(schedule, programs, rng):

    mutated_schedule = schedule.copy()

    # Find positions containing repeated programs
    repeated_positions = [
        index for index, program in enumerate(mutated_schedule)
        if mutated_schedule.count(program) > 1
    ]

    if repeated_positions:

        mutation_point = rng.choice(repeated_positions)

        current_program = mutated_schedule[mutation_point]

        available_programs = [
            program for program in programs
            if program != current_program
        ]

        # Replace the selected program
        mutated_schedule[mutation_point] = rng.choice(
            available_programs
        )

    return mutated_schedule

# Main Genetic Algorithm
def genetic_algorithm(
    file_path,
    generations=GEN,
    population_size=POP,
    crossover_rate=CO_R,
    mutation_rate=MUT_R,
    elitism_size=EL_S,
    seed=None
):

    # Validate crossover rate
    if not 0 <= crossover_rate <= 0.95:
        raise ValueError("Crossover rate must be between 0 and 0.95.")

    # Lecturer default OR custom mutation range
    valid_mutation = (
        abs(mutation_rate - 0.2) < 1e-9
        or 0.01 <= mutation_rate <= 0.05
    )

    if not valid_mutation:
        raise ValueError(
            "Mutation rate must be 0.2 (default) "
            "or between 0.01 and 0.05 (custom)."
        )

    if generations < 1:
        raise ValueError("Generations must be at least 1.")

    if population_size < 3:
        raise ValueError("Population must contain at least 3 schedules.")

    if not 1 <= elitism_size < population_size:
        raise ValueError("Invalid elitism size.")

    # Random generator
    rng = random.Random(seed)

    # Load ratings
    ratings = read_csv_to_dict(file_path)
    programs = list(ratings.keys())

    # Step 1: Initialize population
    population = [
        create_schedule(programs, rng)
        for _ in range(population_size)
    ]

    # Record initial best fitness
    fitness_history = [
        max(fitness_function(s, ratings) for s in population)
    ]

    # Step 2: Run generations
    for generation in range(generations):

        # Sort by fitness
        population.sort(
            key=lambda s: fitness_function(s, ratings),
            reverse=True
        )

        # Step 3: Elitism
        new_population = [
            schedule.copy()
            for schedule in population[:elitism_size]
        ]

        # Step 4: Generate offspring
        while len(new_population) < population_size:

            # Selection
            parent1 = selection(population, ratings, rng)
            parent2 = selection(population, ratings, rng)

            # Crossover
            if rng.random() < crossover_rate:
                child1, child2 = crossover(
                    parent1, parent2, programs, rng
                )
            else:
                child1 = parent1.copy()
                child2 = parent2.copy()

            # Mutation
            if rng.random() < mutation_rate:
                child1 = mutate(child1, programs, rng)

            if rng.random() < mutation_rate:
                child2 = mutate(child2, programs, rng)

            # Add offspring
            new_population.append(child1)

            if len(new_population) < population_size:
                new_population.append(child2)

        # Update population
        population = new_population

        # Record best fitness
        best_fitness = max(
            fitness_function(s, ratings)
            for s in population
        )

        fitness_history.append(best_fitness)

    # Step 5: Return best schedule
    best_schedule = max(
        population,
        key=lambda s: fitness_function(s, ratings)
    )

    return best_schedule, fitness_history, ratings
