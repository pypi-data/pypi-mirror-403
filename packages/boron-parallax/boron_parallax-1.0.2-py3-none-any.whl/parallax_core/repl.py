from environment import Environment
from evaluator import eval_node
from parser import parse

env = Environment()

print("Parallax REPL — superpositional reality online")
print("Type 'exit' to quit")

while True:
    try:
        line = input(">> ").strip()
        if line == "exit":
            break
        tree = parse(line)
        eval_node(tree, env)
    except Exception as e:
        print("Error:", e)
