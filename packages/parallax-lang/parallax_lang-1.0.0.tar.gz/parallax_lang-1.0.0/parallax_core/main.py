import sys
from .environment import Environment
from .evaluator import eval_node
from .parser import parse

# 1. Define the Debug version of run_file
def run_file(path):
    if not path.endswith(".prlx"):
        raise ValueError("Parallax files must use .prlx extension")

    env = Environment()

    try:
        with open(path, "r") as f:
            code = f.read()
        
        # DEBUG PRINTS
        print(f"--- DEBUG: READING {path} ---")
        print(f"Code Length: {len(code)}")
        print(f"Content:\n{code}\n-----------------------------")

        if not code.strip():
            print("ERROR: File is empty!")
            return

        tree = parse(code)
        # DEBUG TREE
        print(f"--- DEBUG: PARSE TREE ---")
        print(tree.statements if hasattr(tree, 'statements') else tree)
        print("-------------------------")

        eval_node(tree, env)

    except Exception as e:
        print(f"RUNTIME ERROR: {e}")
        raise e

def run_repl():
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



def entry_point():
    """This function is the entry point for the 'prlx' command"""
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_repl()

if __name__ == "__main__":
    entry_point()