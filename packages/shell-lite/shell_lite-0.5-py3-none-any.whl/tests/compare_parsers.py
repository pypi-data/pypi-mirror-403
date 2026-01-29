import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shell_lite.lexer import Lexer
from shell_lite.parser import Parser
from shell_lite.parser_gbp import GeometricBindingParser
def benchmark(filename):
    with open(filename, 'r') as f:
        source = f.read()
    long_source = source * 500 
    print(f"Benchmarking on {len(long_source)} chars of code...")
    lexer = Lexer(long_source)
    tokens = lexer.tokenize()
    tokens_copy = list(tokens)
    start = time.perf_counter()
    p_old = Parser(list(tokens)) # fresh copy? Parser consumes? yes
    ast_old = p_old.parse()
    end = time.perf_counter()
    t_old = end - start
    print(f"Recursive Descent: {t_old:.4f}s")
    start = time.perf_counter()
    p_new = GeometricBindingParser(list(tokens))
    ast_new = p_new.parse()
    end = time.perf_counter()
    t_new = end - start
    print(f"Geometric-Binding: {t_new:.4f}s")
    diff = t_old / t_new if t_new > 0 else 0
    print(f"Speedup: {diff:.2f}x")
if __name__ == "__main__":
    benchmark("tests/benchmark.shl")
