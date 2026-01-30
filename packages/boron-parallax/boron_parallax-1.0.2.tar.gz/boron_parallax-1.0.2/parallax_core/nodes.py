# nodes.py - COMPLETE

class Number:
    def __init__(self, value): self.value = value
class Var:
    def __init__(self, name): self.name = name
class Assign:
    def __init__(self, name, expr): self.name = name; self.expr = expr
class BinOp:
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right
class Superpose:
    def __init__(self, values): self.values = values
class Observe:
    def __init__(self, expr): self.expr = expr
class If:
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body
class Block:
    def __init__(self, statements): self.statements = statements
class Compare:
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

# NEW NODES
class ClassDef:
    def __init__(self, name, methods):
        self.name = name
        self.methods = {m.name: m for m in methods}

class FuncDef:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class MethodCall:
    def __init__(self, instance, method_name, args):
        self.instance = instance
        self.method_name = method_name
        self.args = args

class FuncCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class While:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ListLit:
    def __init__(self, elements):
        self.elements = elements

class Return:
    def __init__(self, expr):
        self.expr = expr
# Add this to nodes.py
class Select:
    def __init__(self, target, condition, block=None):
        self.target = target
        self.condition = condition
        self.block = block  # ← NEW

# Add this to the end of nodes.py
class GetAttr:
    def __init__(self, instance, name):
        self.instance = instance
        self.name = name
class Let:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class Repeat:
    def __init__(self, count, body):
        self.count = count
        self.body = body

class Where:
    def __init__(self, target, body):
        self.target = target
        self.body = body

class Aggregate:
    def __init__(self, expr):
        self.expr = expr
class String:
    def __init__(self, value): self.value = value