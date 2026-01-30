from lark import Lark, Transformer
from .nodes import *
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Build the full path to grammar.lark
GRAMMAR_PATH = os.path.join(BASE_DIR, "grammar.lark")

# 3. Open it using the full path
_lark = Lark(open(GRAMMAR_PATH).read(), parser="lalr")

class ASTBuilder(Transformer):
    def start(self, items):
        return Block(items)

    def number(self, items):
        return Number(int(items[0]))
    
    def string(self, items):
        return String(items[0][1:-1])

    def var(self, items):
        return Var(str(items[0]))

    # --- COMPARISONS ---
    def eq(self, items): return Compare(items[0], "==", items[1])
    def neq(self, items): return Compare(items[0], "!=", items[1])
    def gt(self, items): return Compare(items[0], ">", items[1])
    def lt(self, items): return Compare(items[0], "<", items[1])
    def ge(self, items): return Compare(items[0], ">=", items[1])
    def le(self, items): return Compare(items[0], "<=", items[1])

    def add(self, items): return BinOp(items[0], "+", items[1])
    def sub(self, items): return BinOp(items[0], "-", items[1])
    def mul(self, items): return BinOp(items[0], "*", items[1])
    def div(self, items): return BinOp(items[0], "/", items[1])

    def assign(self, items):
        return Assign(str(items[0]), items[1])

    # --- NEW: LET, REPEAT, WHERE, AGGREGATE ---
    def let_stmt(self, items):
        return Let(str(items[0]), items[1])

    def repeat_stmt(self, items):
        return Repeat(items[0], items[1])

    def where_stmt(self, items):
        return Where(str(items[0]), items[1])
    
    def x_expr(self, items):
        return Aggregate(items[0])

    def func_def(self, items):
        name = str(items[0])
        params = items[1] if len(items) > 2 else []
        body = items[-1]
        return FuncDef(name, params, body)
    # ------------------------------------------

    def return_stmt(self, items):
        return Return(items[0])

    def observe_stmt(self, items):
        return Observe(items[0])

    def superpose(self, items):
        return Superpose(items)

    def func_call(self, items):
        name = str(items[0])
        args = items[1] if len(items) > 1 else []
        return FuncCall(name, args)

    def method_call(self, items):
        instance = items[0]
        name = str(items[1])
        args = items[2] if len(items) > 2 else []
        return MethodCall(instance, name, args)

    def args(self, items):
        return items

    def params(self, items):
        return [str(x) for x in items]

    # --- THE FIX IS HERE ---
    def block(self, items):
        return Block(items)  # <-- Wraps list in Block object
    # -----------------------

    def method_def(self, items):
        name = str(items[0])
        params = items[1] if len(items) > 2 else []
        body = items[-1]
        return FuncDef(name, params, body)

    def class_def(self, items):
        return ClassDef(str(items[0]), items[1:])

    def select_stmt(self, items):
        return Select(str(items[0]), items[1])
        
    def get_attr(self, items):
        return GetAttr(items[0], str(items[1]))

    def if_stmt(self, items):
        condition = items[0]
        true_block = items[1]
        false_block = items[2] if len(items) > 2 else None
        return If(condition, true_block, false_block)

    def while_stmt(self, items):
        return While(items[0], items[1])

def parse(code):
    return ASTBuilder().transform(_lark.parse(code))