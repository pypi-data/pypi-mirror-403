import numpy as np
import os
import csv
import json

def initialize_population(bounds, population_size, num_variables):
    """Initialize population with random values within bounds."""
    return np.random.uniform(low=bounds[:, 0], high=bounds[:, 1], size=(population_size, num_variables))

def clip_position(position, bounds):
    """Clip the position to make sure it stays within bounds."""
    return np.clip(position, bounds[:, 0], bounds[:, 1])

def run_optimization(algorithm, bounds, num_iterations, population_size, num_variables, objective_function, constraints=None, track_history=True):
    """Run the selected algorithm and handle logging, saving results, etc.
    
    Parameters:
    -----------
    algorithm : function
        The optimization algorithm to run
    bounds : numpy.ndarray
        Bounds for each variable, shape (num_variables, 2)
    num_iterations : int
        Number of iterations to run the algorithm
    population_size : int
        Size of the population
    num_variables : int
        Number of variables in the optimization problem
    objective_function : function
        Objective function to minimize
    constraints : list, optional
        List of constraint functions
    track_history : bool, optional
        Whether to track detailed convergence history (default: True)
        
    Returns:
    --------
    best_solution : numpy.ndarray
        Best solution found
    convergence_history : dict
        Detailed convergence history including best scores and solutions at each iteration
    """
    
    # Initialize population and variables
    population = initialize_population(bounds, population_size, num_variables)
    
    # Prepare directory for saving results
    if not os.path.exists('results'):
        os.makedirs('results')

    # Run the algorithm with history tracking
    result = algorithm(bounds, num_iterations, population_size, num_variables, objective_function, constraints, track_history)
    
    # Unpack the result based on what was returned
    if track_history:
        if isinstance(result, tuple) and len(result) == 3:
            best_solution, best_scores, convergence_history = result
        else:
            best_solution, convergence_history = result
            best_scores = convergence_history.get('best_scores', [])
    else:
        if isinstance(result, tuple) and len(result) == 2:
            best_solution, best_scores = result
            convergence_history = {'best_scores': best_scores}
        else:
            best_solution = result
            best_scores = []
            convergence_history = {'best_scores': []}

    # Save results
    save_convergence_curve(best_scores)
    if track_history:
        save_convergence_history(convergence_history)

    return best_solution, convergence_history

def save_convergence_curve(best_scores):
    """Save the convergence curve as a CSV."""
    with open(f'results/convergence_curve.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Iteration', 'Best Score'])
        for i, score in enumerate(best_scores):
            writer.writerow([i, score])

def save_convergence_history(convergence_history):
    """Save the detailed convergence history as a JSON file."""
    # Convert numpy arrays to lists for JSON serialization
    serializable_history = {}
    for key, value in convergence_history.items():
        if key == 'best_solutions':
            serializable_history[key] = [solution.tolist() if isinstance(solution, np.ndarray) else solution for solution in value]
        else:
            serializable_history[key] = value
    
    with open(f'results/convergence_history.json', 'w') as file:
        json.dump(serializable_history, file, indent=2)
