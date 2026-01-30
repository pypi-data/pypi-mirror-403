import random

def collapse(value, strategy="observe"):
    if strategy == "observe":
        return value
    if strategy == "first":
        return value.collapse_first()
    if strategy == "random":
        return random.choice(list(value.values))
    if strategy == "max":
        return max(value.values)
    if strategy == "min":
        return min(value.values)

    raise ValueError("Unknown collapse strategy")
