class Environment:
    def __init__(self):
        self.vars = {}
        self.protected = set()
    def get(self, name):
        if name not in self.vars:
            raise NameError(f"Undefined variable '{name}' (not declared in this scope)")
        return self.vars[name]
    def set(self, name, value):
        self.vars[name] = value
