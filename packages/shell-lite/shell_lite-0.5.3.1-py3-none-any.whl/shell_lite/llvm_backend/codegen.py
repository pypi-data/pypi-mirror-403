from llvmlite import ir
from ..ast_nodes import *
class LLVMCompiler:
    def __init__(self):
        self.module = ir.Module(name="shell_lite_module")
        self.module.triple = "x86_64-pc-windows-msvc" # Assume Windows for now based on user OS
        self.int32 = ir.IntType(32)
        self.char_ptr = ir.IntType(8).as_pointer()
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(self.int32, [voidptr_ty], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        malloc_ty = ir.FunctionType(voidptr_ty, [self.int32])
        self.malloc = ir.Function(self.module, malloc_ty, name="malloc")
        free_ty = ir.FunctionType(ir.VoidType(), [voidptr_ty])
        self.free = ir.Function(self.module, free_ty, name="free")
        strlen_ty = ir.FunctionType(self.int32, [voidptr_ty])
        self.strlen = ir.Function(self.module, strlen_ty, name="strlen")
        strcpy_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, voidptr_ty])
        self.strcpy = ir.Function(self.module, strcpy_ty, name="strcpy")
        strcat_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, voidptr_ty])
        self.strcat = ir.Function(self.module, strcat_ty, name="strcat")
        fopen_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, voidptr_ty])
        self.fopen = ir.Function(self.module, fopen_ty, name="fopen")
        fclose_ty = ir.FunctionType(self.int32, [voidptr_ty])
        self.fclose = ir.Function(self.module, fclose_ty, name="fclose")
        fwrite_ty = ir.FunctionType(self.int32, [voidptr_ty, self.int32, self.int32, voidptr_ty])
        self.fwrite = ir.Function(self.module, fwrite_ty, name="fwrite")
        fread_ty = ir.FunctionType(self.int32, [voidptr_ty, self.int32, self.int32, voidptr_ty])
        self.fread = ir.Function(self.module, fread_ty, name="fread")
        fgets_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, self.int32, voidptr_ty])
        self.fgets = ir.Function(self.module, fgets_ty, name="fgets")
        fseek_ty = ir.FunctionType(self.int32, [voidptr_ty, self.int32, self.int32])
        self.fseek = ir.Function(self.module, fseek_ty, name="fseek")
        ftell_ty = ir.FunctionType(self.int32, [voidptr_ty])
        self.ftell = ir.Function(self.module, ftell_ty, name="ftell")
        rewind_ty = ir.FunctionType(ir.VoidType(), [voidptr_ty])
        self.rewind = ir.Function(self.module, rewind_ty, name="rewind")
        get_stdin_ty = ir.FunctionType(voidptr_ty, [self.int32])
        self.get_stdin = ir.Function(self.module, get_stdin_ty, name="__acrt_iob_func")
        system_ty = ir.FunctionType(self.int32, [voidptr_ty])
        self.system = ir.Function(self.module, system_ty, name="system")
        func_type = ir.FunctionType(self.int32, [], var_arg=False)
        self.main_func = ir.Function(self.module, func_type, name="main")
        block = self.main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.scopes = [{}] 
        self.loop_stack = []
        self.str_constants = {}
    def _get_scope(self):
        return self.scopes[-1]
    def _alloca(self, name, typ=None):
        if typ is None: typ = self.int32
        with self.builder.goto_entry_block():
             ptr = self.builder.alloca(typ, size=None, name=name)
        return ptr
    def compile(self, statements):
        for stmt in statements:
            self.visit(stmt)
        self.builder.ret(ir.Constant(self.int32, 0))
        return self.module
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    def generic_visit(self, node):
        print(f"Warning: LLVM Backend does not support {type(node).__name__} yet.")
        return None
    def visit_Number(self, node: Number):
        return ir.Constant(self.int32, int(node.value))
    def visit_String(self, node: String):
        return self._get_string_constant(node.value)
    def visit_BinOp(self, node: BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if op == '+':
            is_str_op = False
            if left.type == self.char_ptr or right.type == self.char_ptr:
                is_str_op = True
            if is_str_op:
                if left.type == self.int32:
                    left = self.builder.inttoptr(left, self.char_ptr, name="cast_l")
                if right.type == self.int32:
                    right = self.builder.inttoptr(right, self.char_ptr, name="cast_r")
            if is_str_op:
                 len1 = self.builder.call(self.strlen, [left], name="len1")
                 len2 = self.builder.call(self.strlen, [right], name="len2")
                 total_len = self.builder.add(len1, len2, name="total_len")
                 total_len_null = self.builder.add(total_len, ir.Constant(self.int32, 1), name="alloc_len")
                 new_str = self.builder.call(self.malloc, [total_len_null], name="new_str")
                 self.builder.call(self.strcpy, [new_str, left])
                 self.builder.call(self.strcat, [new_str, right])
                 return new_str
            return self.builder.add(left, right, name="addtmp")
        elif op == '-':
            return self.builder.sub(left, right, name="subtmp")
        elif op == '*':
            return self.builder.mul(left, right, name="multmp")
        elif op == '/':
            return self.builder.sdiv(left, right, name="divtmp")
        elif op == '==' or op == 'is':
            return self.builder.icmp_signed('==', left, right, name="eqtmp")
        elif op == '!=' or op == 'is not':
            return self.builder.icmp_signed('!=', left, right, name="netmp")
        elif op == '<':
            return self.builder.icmp_signed('<', left, right, name="lttmp")
        elif op == '<=':
            return self.builder.icmp_signed('<=', left, right, name="letmp")
        elif op == '>':
            return self.builder.icmp_signed('>', left, right, name="gttmp")
        elif op == '>=':
            return self.builder.icmp_signed('>=', left, right, name="getmp")
        else:
            raise Exception(f"Unknown operator: {op}")
    def visit_If(self, node: If):
        cond_val = self.visit(node.condition)
        if cond_val.type != ir.IntType(1):
             cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int32, 0), name="ifcond")
        then_bb = self.builder.append_basic_block(name="then")
        else_bb = self.builder.append_basic_block(name="else")
        merge_bb = self.builder.append_basic_block(name="ifcont")
        self.builder.cbranch(cond_val, then_bb, else_bb)
        self.builder.position_at_end(then_bb)
        for stmt in node.body:
            self.visit(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        self.builder.position_at_end(else_bb)
        if node.else_body:
            for stmt in node.else_body:
                self.visit(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        self.builder.position_at_end(merge_bb)
    def visit_While(self, node: While):
        cond_bb = self.builder.append_basic_block(name="loop.cond")
        body_bb = self.builder.append_basic_block(name="loop.body")
        after_bb = self.builder.append_basic_block(name="loop.after")
        self.loop_stack.append((cond_bb, after_bb))
        self.builder.branch(cond_bb)
        self.builder.position_at_end(cond_bb)
        cond_val = self.visit(node.condition)
        if cond_val.type != ir.IntType(1):
             cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(self.int32, 0), name="loopcond")
        self.builder.cbranch(cond_val, body_bb, after_bb)
        self.builder.position_at_end(body_bb)
        for stmt in node.body:
            self.visit(stmt)
        self.builder.branch(cond_bb) # Loop back
        self.builder.position_at_end(after_bb)
        self.loop_stack.pop()
    def visit_Repeat(self, node: Repeat):
        count_val = self.visit(node.count)
        import random
        uid = random.randint(0, 10000)
        i_ptr = self._alloca(f"_loop_i_{uid}")
        self.builder.store(ir.Constant(self.int32, 0), i_ptr)
        cond_bb = self.builder.append_basic_block(name="repeat.cond")
        body_bb = self.builder.append_basic_block(name="repeat.body")
        after_bb = self.builder.append_basic_block(name="repeat.after")
        self.loop_stack.append((cond_bb, after_bb))
        self.builder.branch(cond_bb)
        self.builder.position_at_end(cond_bb)
        curr_i = self.builder.load(i_ptr, name="i_load")
        cmp = self.builder.icmp_signed('<', curr_i, count_val, name="loopcheck")
        self.builder.cbranch(cmp, body_bb, after_bb)
        self.builder.position_at_end(body_bb)
        for stmt in node.body:
            self.visit(stmt)
        curr_i_Body = self.builder.load(i_ptr)
        next_i = self.builder.add(curr_i_Body, ir.Constant(self.int32, 1), name="inc_i")
        self.builder.store(next_i, i_ptr)
        self.builder.branch(cond_bb)
        self.builder.position_at_end(after_bb)
        self.loop_stack.pop()
    def visit_FunctionDef(self, node: FunctionDef):
        arg_types = [self.int32] * len(node.args) 
        arg_types = []
        for arg in node.args:
            name, _, hint = arg # arg is tuple
            if True: # FORCE ALL ARGS TO STRINGS FOR SHELL LITE (Phase 7 Fix)
                 arg_types.append(self.char_ptr)
            else:
                 arg_types.append(self.int32)
        func_ty = ir.FunctionType(self.int32, arg_types) # Return int32 (or pointer casted)
        func = ir.Function(self.module, func_ty, name=node.name)
        old_builder = self.builder
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.scopes.append({}) # New scope
        for i, arg in enumerate(func.args):
            arg_name = node.args[i][0]
            arg.name = arg_name
            ptr = self.builder.alloca(arg.type, name=arg_name)
            self.builder.store(arg, ptr)
            self.scopes[-1][arg_name] = ptr
        for stmt in node.body:
            self.visit(stmt)
        if not self.builder.block.is_terminated:
             self.builder.ret(ir.Constant(self.int32, 0))
        self.scopes.pop()
        self.builder = old_builder
    def visit_Return(self, node: Return):
        val = self.visit(node.value)
        if val.type == self.char_ptr:
             val = self.builder.ptrtoint(val, self.int32)
        self.builder.ret(val)
    def visit_Call(self, node: Call):
        if node.name in self.module.globals:
            func = self.module.globals[node.name]
        elif node.name == 'read':
             if len(node.args) > 0:
                 return self.visit_FileRead(FileRead(node.args[0]))
             else:
                 return ir.Constant(self.int32, 0)
        else:
             print(f"Warning: Function {node.name} not found")
             return ir.Constant(self.int32, 0)
        args = [self.visit(a) for a in node.args]
        return self.builder.call(func, args, name="calltmp")
    def visit_Assign(self, node: Assign):
        value = self.visit(node.value)
        scope = self._get_scope()
        if node.name not in scope:
            ptr = self._alloca(node.name, typ=value.type)
            scope[node.name] = ptr
        else:
            ptr = scope[node.name]
        self.builder.store(value, ptr)
        return value
    def visit_Execute(self, node: Execute):
        cmd = self.visit(node.code)
        self.builder.call(self.system, [cmd])
        return ir.Constant(self.int32, 0)
    def visit_Stop(self, node: Stop):
        if not self.loop_stack:
            print("Error: stop used outside of loop")
            return
        after_bb = self.loop_stack[-1][1]
        self.builder.branch(after_bb)
        dead_bb = self.builder.append_basic_block(name="dead")
        self.builder.position_at_end(dead_bb)
    def visit_Skip(self, node: Skip):
        if not self.loop_stack:
            print("Error: skip used outside of loop")
            return
        cond_bb = self.loop_stack[-1][0]
        self.builder.branch(cond_bb)
        dead_bb = self.builder.append_basic_block(name="dead")
        self.builder.position_at_end(dead_bb)
    def _get_stdin_handle(self):
        return self.builder.call(self.get_stdin, [ir.Constant(self.int32, 0)])
    def visit_Input(self, node: Input):
        buffer_len = ir.Constant(self.int32, 256)
        buffer = self.builder.call(self.malloc, [buffer_len], name="input_buf")
        stdin = self._get_stdin_handle()
        self.builder.call(self.fgets, [buffer, buffer_len, stdin])
        return buffer
    def visit_FileWrite(self, node: FileWrite):
        path = self.visit(node.path)
        content = self.visit(node.content)
        mode = self._get_string_constant("w")
        fp = self.builder.call(self.fopen, [path, mode], name="fp")
        length = self.builder.call(self.strlen, [content])
        self.builder.call(self.fwrite, [content, ir.Constant(self.int32, 1), length, fp])
        self.builder.call(self.fclose, [fp])
        return ir.Constant(self.int32, 0)
    def visit_FileRead(self, node: FileRead):
        path = self.visit(node.path)
        mode = self._get_string_constant("rb") # Binary to avoid text translation issues? Or "r"
        fp = self.builder.call(self.fopen, [path, mode], name="fp")
        self.builder.call(self.fseek, [fp, ir.Constant(self.int32, 0), ir.Constant(self.int32, 2)])
        size = self.builder.call(self.ftell, [fp], name="fsize")
        self.builder.call(self.rewind, [fp])
        alloc_size = self.builder.add(size, ir.Constant(self.int32, 1))
        buffer = self.builder.call(self.malloc, [alloc_size], name="fbuf")
        self.builder.call(self.fread, [buffer, ir.Constant(self.int32, 1), size, fp])
        null_term_ptr = self.builder.gep(buffer, [size])
        self.builder.store(ir.Constant(ir.IntType(8), 0), null_term_ptr)
        self.builder.call(self.fclose, [fp])
        return buffer
    def visit_VarAccess(self, node: VarAccess):
        scope = self._get_scope()
        if node.name in scope:
            ptr = scope[node.name]
            return self.builder.load(ptr, name=node.name)
        else:
            raise Exception(f"Variable '{node.name}' not defined")
    def _get_string_constant(self, text):
        text += '\0'
        if text in self.str_constants:
            return self.str_constants[text]
        byte_arr = bytearray(text.encode("utf8"))
        c_str_ty = ir.ArrayType(ir.IntType(8), len(byte_arr))
        global_var = ir.GlobalVariable(self.module, c_str_ty, name=f".str_{len(self.str_constants)}")
        global_var.linkage = 'internal'
        global_var.global_constant = True
        global_var.initializer = ir.Constant(c_str_ty, byte_arr)
        ptr = self.builder.bitcast(global_var, self.char_ptr)
        self.str_constants[text] = ptr
        return ptr
    def visit_Print(self, node: Print):
        value = self.visit(node.expression)
        if value.type == self.char_ptr:
            fmt_str = self._get_string_constant("%s\n")
            self.builder.call(self.printf, [fmt_str, value])
        else:
            if value.type != self.int32:
                 pass
            fmt_str = self._get_string_constant("%d\n")
            self.builder.call(self.printf, [fmt_str, value])
