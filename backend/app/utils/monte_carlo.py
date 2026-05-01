import numpy as np

def monte_carlo_simulation(drivers: dict, volatility: float = 0.1, simulations: int = 1000):
    """
    Drivers can be multiple (revenue, expense, etc.)
    Returns mean/min/max per driver
    """
    results = {key: [] for key in drivers}

    for _ in range(simulations):
        for key, value in drivers.items():
            simulated_value = value * np.random.normal(1, volatility)
            results[key].append(simulated_value)

    summary = {}
    for key, vals in results.items():
        summary[key] = {
            "mean": float(np.mean(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals))
        }
    return summary