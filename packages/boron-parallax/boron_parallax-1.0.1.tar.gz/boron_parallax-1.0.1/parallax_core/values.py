from collections import Counter

class SuperValue:
    def __init__(self, values):
        # values is a LIST, multiplicity matters
        self.values = list(values)

    def __add__(self, other):
        return SuperValue([x + y for x in self.values for y in other.values])

    def __sub__(self, other):
        return SuperValue([x - y for x in self.values for y in other.values])

    def __mul__(self, other):
        return SuperValue([x * y for x in self.values for y in other.values])

    def __truediv__(self, other):
        return SuperValue([x / y for x in self.values for y in other.values])
    
    # Comparisons return lists of booleans (SuperValue)
    def __eq__(self, other):
        return SuperValue([x == y for x in self.values for y in other.values])
    
    def __ne__(self, other):
        return SuperValue([x != y for x in self.values for y in other.values])

    def distribution(self):
        if not self.values: return {}
        total = len(self.values)
        counts = Counter(self.values)
        return {k: v / total for k, v in counts.items()}

    def __repr__(self):
        if not self.values: return "<Empty Superposition>"
        # Check if this holds AggregateValues (X objects)
        if isinstance(self.values[0], AggregateValue):
             return f"<Meta-Value X: {self.values[0]}>"
             
        dist = self.distribution()
        return " | ".join(f"{k}: {v*100:.1f}%" for k, v in dist.items())


class AggregateValue:
    """
    The 'X' Structure.
    Represents a meta-view of a value across all timelines.
    """
    def __init__(self, super_value):
        # If passed a raw list (from internal logic), wrap it
        if isinstance(super_value, list):
             self.values = super_value
        elif hasattr(super_value, 'values'):
             self.values = super_value.values
        else:
             self.values = [super_value]
        
    def freq(self, val):
        """Returns frequency (0.0 to 1.0) of a specific value."""
        if not self.values: return 0.0
        # Check for matching values
        count = sum(1 for v in self.values if v == val)
        return count / len(self.values)

    def min(self):
        return min(self.values) if self.values else 0

    def max(self):
        return max(self.values) if self.values else 0
        
    def percentile(self, p):
        """Returns the value at the p-th percentile (0-100)."""
        if not self.values: return 0
        try:
            sorted_vals = sorted(self.values)
            idx = int((p / 100.0) * len(sorted_vals))
            return sorted_vals[min(idx, len(sorted_vals)-1)]
        except:
            return 0 # Fallback for non-sortable types

    def __repr__(self):
        return f"[X: {len(self.values)} timelines]"