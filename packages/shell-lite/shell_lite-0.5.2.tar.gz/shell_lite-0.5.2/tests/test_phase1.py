"""
Comprehensive Test Suite for ShellLite v0.5.1 Phase 1 Changes

Tests:
1. GBP Performance Benchmarks (multiple runs)
2. Begin/End Syntax (various cases)
3. Lexer bracket_depth tracking
4. Parser stability
"""

import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shell_lite.lexer import Lexer
from shell_lite.parser import Parser
from shell_lite.parser_gbp import GeometricBindingParser
from shell_lite.interpreter import Interpreter

PASSED = 0
FAILED = 0

def test(name, condition):
    global PASSED, FAILED
    if condition:
        print(f"  [PASS] {name}")
        PASSED += 1
    else:
        print(f"  [FAIL] {name}")
        FAILED += 1

def run_code(source):
    """Parse and execute code, return captured output"""
    import io
    from contextlib import redirect_stdout
    
    lex = Lexer(source)
    tokens = lex.tokenize()
    parser = GeometricBindingParser(tokens)
    ast = parser.parse()
    
    interp = Interpreter()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        for node in ast:
            interp.visit(node)
    return buffer.getvalue().strip()

# ============================================================
# TEST 1: GBP Performance
# ============================================================
print("\n" + "="*60)
print("TEST 1: GBP Performance Benchmarks")
print("="*60)

with open('tests/benchmark.shl', 'r') as f:
    source = f.read()

long_source = source * 500
lexer = Lexer(long_source)
tokens = lexer.tokenize()

# Run multiple iterations
ITERATIONS = 20

rd_times = []
for _ in range(ITERATIONS):
    tokens_copy = list(tokens)
    start = time.perf_counter()
    p = Parser(tokens_copy)
    ast = p.parse()
    end = time.perf_counter()
    rd_times.append(end - start)

gbp_times = []
for _ in range(ITERATIONS):
    tokens_copy = list(tokens)
    start = time.perf_counter()
    p = GeometricBindingParser(tokens_copy)
    ast = p.parse()
    end = time.perf_counter()
    gbp_times.append(end - start)

rd_min = min(rd_times)
gbp_min = min(gbp_times)
rd_mean = statistics.mean(rd_times)
gbp_mean = statistics.mean(gbp_times)
speedup_min = rd_min / gbp_min if gbp_min > 0 else 0
speedup_mean = rd_mean / gbp_mean if gbp_mean > 0 else 0

print(f"\n  Benchmark: {len(long_source)} chars, {ITERATIONS} iterations")
print(f"  RD  Mean: {rd_mean:.4f}s, Min: {rd_min:.4f}s")
print(f"  GBP Mean: {gbp_mean:.4f}s, Min: {gbp_min:.4f}s")
print(f"  Speedup (Min/Min): {speedup_min:.2f}x")
print(f"  Speedup (Mean):    {speedup_mean:.2f}x")
print()

test("GBP speedup >= 2.0x (min/min)", speedup_min >= 2.0)
test("GBP speedup >= 1.5x (mean)", speedup_mean >= 1.5)

# ============================================================
# TEST 2: Begin/End Syntax - Functions
# ============================================================
print("\n" + "="*60)
print("TEST 2: Begin/End Syntax - Functions")
print("="*60)

# Test: No-argument function
output = run_code('''
to greet
begin
say "Hello World"
end
greet
''')
test("No-arg function with begin/end", output == "Hello World")

# Test: If statement with begin/end
output = run_code('''
x = 10
if x > 5
begin
say "big"
end
''')
test("If statement with begin/end", output == "big")

# Test: Nested begin/end
output = run_code('''
x = 10
if x > 0
begin
if x > 5
begin
say "nested"
end
end
''')
test("Nested begin/end", output == "nested")

# Test: Multiple functions with begin/end
output = run_code('''
to one
begin
say "1"
end

to other
begin
say "2"
end

one
other
''')
test("Multiple functions with begin/end", output == "1\n2")

# ============================================================
# TEST 3: Lexer - Bracket Depth Tracking
# ============================================================
print("\n" + "="*60)
print("TEST 3: Lexer - Bracket Depth Tracking")
print("="*60)

# Test: Multi-line list doesn't produce INDENT inside brackets
source = '''my_list = [
    1,
    2,
    3
]'''
lex = Lexer(source)
tokens = lex.tokenize()
token_types = [t.type for t in tokens]

# Should NOT have INDENT between LBRACKET and RBRACKET
has_indent_in_list = False
in_list = False
for t in tokens:
    if t.type == 'LBRACKET':
        in_list = True
    elif t.type == 'RBRACKET':
        in_list = False
    elif t.type == 'INDENT' and in_list:
        has_indent_in_list = True
        break

test("No INDENT inside multi-line list", not has_indent_in_list)

# ============================================================
# TEST 4: Parser Stability - Mixed Constructs
# ============================================================
print("\n" + "="*60)
print("TEST 4: Parser Stability - Mixed Constructs")
print("="*60)

# Test: Mix of indentation and begin/end shouldn't crash
try:
    output = run_code('''
x = 5
if x > 0
begin
say "begin/end"
end

if x > 0:
    say "indentation"
''')
    # Note: This might not work perfectly due to mixing, but shouldn't crash
    test("Mixed indentation and begin/end parses", True)
except Exception as e:
    test("Mixed indentation and begin/end parses", False)
    print(f"    Error: {e}")

# Test: Traditional indentation still works
try:
    output = run_code('''
x = 5
if x > 0:
    say "indentation works"
''')
    test("Traditional indentation parses", "indentation" in output)
except Exception as e:
    test("Traditional indentation parses", False)
    print(f"    Error: {e}")

# ============================================================
# TEST 5: Performance with Deep Nesting
# ============================================================
print("\n" + "="*60)
print("TEST 5: Performance with Deep Nesting")
print("="*60)

deep_source = '''
x = 1
if x > 0:
    if x > 0:
        if x > 0:
            if x > 0:
                if x > 0:
                    print "deep"
''' * 100

lex = Lexer(deep_source)
tokens = lex.tokenize()

# Just time GBP
start = time.perf_counter()
p = GeometricBindingParser(list(tokens))
ast = p.parse()
end = time.perf_counter()
deep_time = end - start

print(f"\n  Deep nesting ({len(deep_source)} chars): {deep_time:.4f}s")
test("Deep nesting parses in < 1s", deep_time < 1.0)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\n  Passed: {PASSED}")
print(f"  Failed: {FAILED}")
print(f"  Total:  {PASSED + FAILED}")
print()

if FAILED == 0:
    print("  ALL TESTS PASSED!")
else:
    print(f"  {FAILED} test(s) FAILED")
    sys.exit(1)
