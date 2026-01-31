from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable
from .lexer import Token
from .ast_nodes import *
@dataclass
class GeoNode:
    """Represents a topological node in the source code geometry."""
    head_token: Token
    line: int
    indent_level: int
    tokens: List[Token] = field(default_factory=list)
    children: List['GeoNode'] = field(default_factory=list)
    parent: Optional['GeoNode'] = None
    
    def __repr__(self):
        return f"GeoNode(line={self.line}, indent={self.indent_level}, head={self.head_token.type})"
class GeometricBindingParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != 'COMMENT']  # Should keep NEWLINE/INDENT/DEDENT for context? 
        self.root_nodes: List[GeoNode] = []
        self.precedence = {
            'OR': 1, 'AND': 2, 'NOT': 3,
            'EQ': 4, 'NEQ': 4, 'LT': 5, 'GT': 5, 'LE': 5, 'GE': 5, 'IS': 5,
            'PLUS': 6, 'MINUS': 6,
            'MUL': 7, 'DIV': 7, 'MOD': 7,
            'POW': 8,
            'DOT': 9, 'LPAREN': 10, 'LBRACKET': 10
        }
    def parse(self) -> List[Node]:
        """Main entry point."""
        self.topology_scan()
        ast_nodes = []
        for geo_node in self.root_nodes:
            ast_node = self.bind_node(geo_node)
            if ast_node:
                ast_nodes.append(ast_node)
        return ast_nodes
    def topology_scan(self):
        """
        Phase 1: Scans tokens to build GeoNodes.
        Phase 2: Links them into a tree based on nesting.
        """
        node_stack: List[GeoNode] = [] # The active parents
        current_tokens_accumulator = []
        current_node: Optional[GeoNode] = None
        last_line_node: Optional[GeoNode] = None  # Track the last completed line's node
        block_stack: List[GeoNode] = [] 
        for token in self.tokens:
            if token.type == 'EOF':
                break
            if token.type == 'INDENT':
                # Use last_line_node as parent if current_node is None (NEWLINE came before INDENT)
                parent_to_push = current_node if current_node else last_line_node
                if parent_to_push:
                     block_stack.append(parent_to_push)
                current_node = None
                continue
            if token.type == 'DEDENT':
                 if block_stack:
                     block_stack.pop()
                 continue
            if token.type == 'NEWLINE':
                last_line_node = current_node  # Save before resetting
                current_node = None
                continue
            if current_node is None:
                current_node = GeoNode(
                    head_token=token,
                    line=token.line,
                    indent_level=len(block_stack), # Logical depth
                    tokens=[token] # Start collecting tokens
                )
                if block_stack:
                    parent = block_stack[-1]
                    parent.children.append(current_node)
                    current_node.parent = parent
                else:
                    self.root_nodes.append(current_node)
            else:
                current_node.tokens.append(token)
    def bind_node(self, node: GeoNode) -> Node:
        """Phase 2: Semantic Binding Dispatcher."""
        head_type = node.head_token.type
        if head_type == 'IF':
            return self.bind_if(node)
        elif head_type == 'WHILE':
            return self.bind_while(node)
        elif head_type == 'FOR' or head_type == 'LOOP':
            return self.bind_for(node)
        elif head_type == 'USE':
            return self.bind_use(node)
        elif head_type == 'SERVE':
            return self.bind_serve(node)
        elif head_type == 'DEFINE':
            return self.bind_define(node)
        elif head_type == 'WHEN':
            return self.bind_when(node)
        elif head_type == 'ON':
            return self.bind_on(node)
        elif head_type == 'FUNCTION' or head_type == 'TO':
             return self.bind_func(node)
        elif head_type == 'PRINT' or head_type == 'SAY':
            return self.bind_print(node)
        elif head_type == 'RETURN':
            return self.bind_return(node)
        elif head_type == 'REPEAT':
            return self.bind_repeat(node)
        elif head_type == 'START':
            return self.bind_start(node)
        elif head_type == 'LISTEN':
            return self.bind_listen(node)
        elif head_type == 'ID':
            # Assignment: ID ASSIGN ... (second token must be ASSIGN)
            # Function call with kwargs: ID ID ASSIGN ... (ASSIGN comes later)
            if len(node.tokens) >= 2 and node.tokens[1].type == 'ASSIGN':
                return self.bind_assignment(node)
            return self.bind_call_or_expr(node)
        else:
            return self.bind_call_or_expr(node)
    def peek_type(self, node: GeoNode, offset: int) -> str:
        if offset < len(node.tokens):
            return node.tokens[offset].type
        return ""
    def bind_if(self, node: GeoNode) -> If:
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        condition = self.parse_expr_iterative(expr_tokens)
        body = [self.bind_node(child) for child in node.children]
        else_body = None
        return If(condition, body, else_body)
    def bind_while(self, node: GeoNode) -> While:
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        condition = self.parse_expr_iterative(expr_tokens)
        body = [self.bind_node(child) for child in node.children]
        return While(condition, body)
    def bind_repeat(self, node: GeoNode) -> Repeat:
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        if expr_tokens and expr_tokens[-1].type == 'TIMES':
            expr_tokens.pop()
        count = self.parse_expr_iterative(expr_tokens)
        body = [self.bind_node(child) for child in node.children]
        return Repeat(count, body)
    def bind_print(self, node: GeoNode) -> Print:
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        expr = self.parse_expr_iterative(expr_tokens)
        return Print(expr)
    def bind_return(self, node: GeoNode) -> Return:
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        expr = self.parse_expr_iterative(expr_tokens)
        return Return(expr)
    def bind_assignment(self, node: GeoNode) -> Assign:
        assign_idx = -1
        for i, t in enumerate(node.tokens):
            if t.type == 'ASSIGN':
                assign_idx = i
                break
        name = node.tokens[0].value # Simplification: Assume simple ID assignment
        expr_tokens = node.tokens[assign_idx+1:]
        value = self.parse_expr_iterative(expr_tokens)
        return Assign(name, value)
    def bind_expression_stmt(self, node: GeoNode) -> Any:
        return self.parse_expr_iterative(node.tokens)
    def bind_start(self, node: GeoNode) -> Listen:
        # 'start website' -> Listen(8080)
        # We could parse args if needed, but for now we assume default
        return Listen(Number(8080))
    def bind_listen(self, node: GeoNode) -> Listen:
        # 'listen 8080' or 'listen port 8080'
        expr_tokens = self._extract_expr_tokens(node.tokens, start=1)
        if expr_tokens and expr_tokens[0].type == 'PORT':
             expr_tokens.pop(0)
        port = self.parse_expr_iterative(expr_tokens)
        return Listen(port)
    def bind_func(self, node: GeoNode) -> FunctionDef:
        start = 1
        if node.tokens[0].type == 'DEFINE': start = 2
        name = node.tokens[start].value
        args = []
        # Look for 'using' keyword (which is tokenized as ID)
        collecting_args = False
        for t in node.tokens[start+1:]:
            if t.type == 'USING':
                collecting_args = True
                continue
            if t.type == 'ID' and collecting_args:
                args.append((t.value, None, None))
            elif t.type == 'COLON': break
            elif t.type == 'COMMA': continue
        body = [self.bind_node(child) for child in node.children]
        return FunctionDef(name, args, body)
    def bind_use(self, node: GeoNode) -> Import:
        # 'use "filename.shl"'
        for t in node.tokens:
            if t.type == 'STRING':
                return Import(t.value)
        return Import(node.tokens[1].value if len(node.tokens) > 1 else '')
    def bind_serve(self, node: GeoNode) -> ServeStatic:
        # 'serve files from "public" at "/static"'
        folder = String('public')
        url = String('/static')
        tokens = node.tokens
        for i, t in enumerate(tokens):
            if t.type == 'FROM' and i+1 < len(tokens):
                folder = self.parse_expr_iterative([tokens[i+1]])
            if t.type == 'AT' and i+1 < len(tokens):
                url = self.parse_expr_iterative([tokens[i+1]])
        return ServeStatic(folder, url)
    def bind_define(self, node: GeoNode) -> FunctionDef:
        # 'define page Name using arg1, arg2'
        tokens = node.tokens
        name = ''
        args = []
        i = 1
        # Skip 'page' or 'component' if present
        if i < len(tokens) and tokens[i].type == 'PAGE':
            i += 1
        if i < len(tokens) and tokens[i].type == 'ID':
            name = tokens[i].value
            i += 1
        # Parse 'using' args
        if i < len(tokens) and tokens[i].type == 'USING':
            i += 1
            while i < len(tokens):
                if tokens[i].type == 'ID':
                    args.append((tokens[i].value, None, None))
                elif tokens[i].type == 'COMMA':
                    pass
                else:
                    break
                i += 1
        body = [self.bind_node(child) for child in node.children]
        return FunctionDef(name, args, body)
    def bind_when(self, node: GeoNode) -> OnRequest:
        # 'when someone visits "/path"'
        tokens = node.tokens
        path = String('/')
        for i, t in enumerate(tokens):
            if t.type == 'STRING':
                path = String(t.value)
                break
        body = [self.bind_node(child) for child in node.children]
        return OnRequest(path, body)
    def bind_on(self, node: GeoNode) -> OnRequest:
        # 'on request to "/path"'
        tokens = node.tokens
        path = String('/')
        for t in tokens:
            if t.type == 'STRING':
                path = String(t.value)
                break
        body = [self.bind_node(child) for child in node.children]
        return OnRequest(path, body)
    def bind_call_or_expr(self, node: GeoNode) -> Any:
        # Handle function calls like 'Head "title"' or 'Navbar'
        tokens = node.tokens
        if len(tokens) >= 1 and tokens[0].type == 'ID':
            name = tokens[0].value
            args = []
            kwargs = []
            # Parse remaining tokens as arguments, handling key=value for HTML attributes
            i = 1
            while i < len(tokens):
                t = tokens[i]
                # Check for key=value pattern (e.g. class="container", style="...", href="...")
                # HTML attributes may be tokenized as various types: ID, STRUCTURE, HREF, REL, NAME, etc.
                is_attr_key = t.type in ('ID', 'STRUCTURE', 'HREF', 'REL', 'NAME', 'STYLE', 'CONTENT', 'CHARSET', 'SRC', 'ALT', 'TYPE', 'VALUE', 'PLACEHOLDER', 'METHOD', 'ACTION')
                is_kwarg = (is_attr_key and i + 2 < len(tokens) and tokens[i + 1].type == 'ASSIGN')
                if is_kwarg:
                    key = t.value
                    val_token = tokens[i + 2]
                    if val_token.type == 'STRING':
                        kwargs.append((key, String(val_token.value)))
                    elif val_token.type == 'NUMBER':
                        kwargs.append((key, Number(int(val_token.value) if '.' not in val_token.value else float(val_token.value))))
                    else:
                        kwargs.append((key, VarAccess(val_token.value)))
                    i += 3
                    continue
                elif t.type == 'STRING':
                    args.append(String(t.value))
                elif t.type == 'NUMBER':
                    args.append(Number(int(t.value) if '.' not in t.value else float(t.value)))
                elif t.type == 'ID':
                    args.append(VarAccess(t.value))
                i += 1
            # Check for children (indented body)
            body = None
            if node.children:
                body = [self.bind_node(child) for child in node.children]
            return Call(name, args, kwargs=kwargs, body=body)
        return self.parse_expr_iterative(tokens)
    def _extract_expr_tokens(self, tokens: List[Token], start: int = 0) -> List[Token]:
        end = len(tokens)
        if tokens[-1].type == 'COLON':
            end -= 1
        return tokens[start:end]
    def parse_expr_iterative(self, tokens: List[Token]) -> Node:
        """
        Shunting-yard variant to produce AST directly.
        Two stacks: 
        1. values: [Node]
        2. ops: [Token (operator)]
        """
        if not tokens: return None
        values: List[Node] = []
        ops: List[str] = []
        def apply_op():
            if not ops: return
            op_type = ops.pop()
            if len(values) >= 2:
                right = values.pop()
                left = values.pop()
                op_map = {
                    'PLUS': '+', 'MINUS': '-', 'MUL': '*', 'DIV': '/', 'MOD': '%',
                    'LT': '<', 'GT': '>', 'LE': '<=', 'GE': '>=', 'EQ': '==', 'NEQ': '!=',
                    'AND': 'and', 'OR': 'or'
                }
                op_str = op_map.get(op_type, op_type)
                values.append(BinOp(left, op_str, right))
        def precedence(op_type):
            return self.precedence.get(op_type, 0)
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == 'NUMBER':
                values.append(Number(int(t.value) if '.' not in t.value else float(t.value)))
            elif t.type == 'STRING':
                values.append(String(t.value))
            elif t.type == 'LBRACKET':
                # Consumed nested list
                depth = 1
                j = i + 1
                elements_tokens = []
                current_elem = []
                while j < len(tokens):
                    if tokens[j].type == 'LBRACKET': depth += 1
                    elif tokens[j].type == 'RBRACKET': depth -= 1
                    
                    if depth == 0:
                        if current_elem: elements_tokens.append(current_elem)
                        break
                    
                    if tokens[j].type == 'COMMA' and depth == 1:
                        elements_tokens.append(current_elem)
                        current_elem = []
                    else:
                        current_elem.append(tokens[j])
                    j += 1
                
                # Parse elements
                items = [self.parse_expr_iterative(elem) for elem in elements_tokens if elem]
                values.append(ListVal(items))
                i = j # Advance past list
            elif t.type == 'ID':
                if i+1 < len(tokens) and tokens[i+1].type == 'LPAREN':
                    values.append(VarAccess(t.value))
                else:
                    values.append(VarAccess(t.value))
            elif t.type == 'LPAREN':
                ops.append('LPAREN')
            elif t.type == 'RPAREN':
                while ops and ops[-1] != 'LPAREN':
                    apply_op()
                if ops: ops.pop() # Pop LPAREN
            elif t.type in self.precedence:
                while (ops and ops[-1] != 'LPAREN' and 
                       precedence(ops[-1]) >= precedence(t.type)):
                    apply_op()
                ops.append(t.type)
            i += 1
        while ops:
            apply_op()
        return values[0] if values else None
