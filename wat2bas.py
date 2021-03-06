#!/usr/bin/env python3
import sys
import json
from pprint import pprint, pformat
from typing import Union
import urllib.parse
import re

inp = (open(sys.argv[1], "r") if len(sys.argv) >= 2 else sys.stdin)
out = open(sys.argv[2], "w") if len(sys.argv) >= 3 else sys.stdout

class SString:
    """S式内のstring"""
    def __init__(self):
        s = b""
        escape_mode = False
        while True:
            c = inp.read(1)
            if escape_mode:
                if c == "n":
                    s += b"\n"
                elif c in "0123456789abcdef":
                    c += inp.read(1)
                    s += bytes([int(c, 16)])
                else:
                    print("fall", c)
                    s += c.encode("ascii")
                escape_mode = False
            elif c == "\\":
                escape_mode = True
            elif c == "\"":
                break
            elif c == "":
                raise Exception("invalid string terminate")
            else:
                s += c.encode("utf-8")
        print(s)
        self.bytes = s
        self.value = s.decode("latin-1")
    
    def __repr__(self) -> str:
        return "SString("+pformat(self.value)+")"

def parse_s():
    result = []
    current = ""
    maybe_comment = False
    comment_now = False
    while True:
        c = inp.read(1)
        if maybe_comment and c == ";":
            current = current[:-1]
            comment_now = True
        if c == "\n" if comment_now else (c == " " or c == "\n"):
            if len(current) > 0:
                result.append(current)
                current = ""
            comment_now = False
        elif c == "" or c == ")":
            if len(current) > 0:
                result.append(current)
            return result
        elif not comment_now:
            if c == "\"":
                result.append(SString())
            elif c == "(":
                result.append(parse_s())
            else:
                maybe_comment = c == ";"
                current += c

RE_SEMIINDEX = re.compile("^;([0-9]+);$")

def get_name(input: Union[str, list, int]):
    if type(input) is int:
        return "_WASM_INDEXED_" + str(input)
    if type(input) is str:
        if input.startswith("$"):
            return "_WASM_NAMED_" + urllib.parse.quote(input[1:].replace("_", "__")).replace("%", "_")
        else:
            return "_WASM_INDEXED_" + str(int(input))
    elif len(input) == 1:
        matched = RE_SEMIINDEX.match(input[0])
        return "_WASM_INDEXED_" + str(int(matched.group(1)))
    else:
        raise Exception("invalid name", input)

def type_to_suffix(ty: str):
    if ty == "i32":
        return "%"
    elif ty == "f64":
        return "#"
    return ""

def stack_name(ty: str):
    return "STACK_" + ty + type_to_suffix(ty)

modules: list = parse_s()[0]
if modules[0] != "module":
    raise Exception("expect module")
modules.pop(0)

types = {}

out.write(f"""
DIM MEMORY%[{17 * 16384}]
""")
out.write(open("./runtime.txt", "r").read())

func_return_types = {}

main_func = ""

for mod in modules:
    module_type = mod.pop(0)
    print("# " + module_type)
    if module_type == "type":
        name = get_name(mod.pop(0))
        types[name] = mod
        print(name)
        pprint(mod)
    elif module_type == "import":
        import_module = mod.pop(0).value
        import_name = mod.pop(0).value
        import_obj = mod.pop(0)
        import_type = import_obj.pop(0)
        if import_type == "func":
            print("# import", import_name)
            local_name = get_name(import_obj.pop(0))
            if import_name == "print":
                print("# import", local_name)
                func_return_types[local_name] = "void"
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name} PTR%
    ' ?"DEBUG:PRINT_CALLED", PTR%
    VAR C%
    WHILE TRUE
        C% = READ16(PTR%)
        PTR% = PTR% + 2
        IF C% == 0 THEN BREAK
        PRINT CHR$(C%);
    WEND
END\n
""")
            elif import_name == "input_int32":
                func_return_types[local_name] = "i32"
                print("# import", local_name)
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name}(PTR%)
    VAR C%
    IF PTR% != 0 THEN
        WHILE TRUE
            C% = READ16(PTR%)
            PTR% = PTR% + 2
            IF C% == 0 THEN BREAK
            PRINT CHR$(C%);
        WEND
    ENDIF
    INPUT C%
    RETURN C%
END\n
""")
            elif import_name == "vsync":
                func_return_types[local_name] = "void"
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name} FRAME%
    VSYNC FRAME%
END\n
""")
            elif import_name == "acls":
                func_return_types[local_name] = "void"
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name} DUMMY%
    ACLS
END\n
""")
            elif import_name == "rnd":
                func_return_types[local_name] = "i32"
                print("# import", local_name)
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name}(MAX%)
    RETURN RND(MAX%)
END\n
""")
            elif import_name == "beep":
                func_return_types[local_name] = "void"
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name} NUM%
    BEEP NUM%
END\n
""")
            elif import_name == "button":
                func_return_types[local_name] = "i32"
                print("# import", local_name)
                out.write(f"""'IMPORT BASIC FUNC
DEF {local_name}(MODE%)
    RETURN BUTTON(MODE%)
END\n
""")
        else:
            print("# not supporting import", import_type)
    elif module_type == "func": # handle func
        name = get_name(mod.pop(0))
        print(name)
        out.write(f"DEF {name}\n")
        out.write(f"DIM {stack_name('i32')}[0], {stack_name('f64')}[0], JMPSTACK$[0]\n")
        local_types = []
        end_stack = []
        block_stack = ["RETURN"]
        block_index = 0
        while len(mod) > 0:
            elem = mod.pop(0)
            if type(elem) is list:
                if elem[0] == "local":
                    i = 0
                    local_types = elem[1:]
                    for l in elem[1:]:
                        out.write(f"VAR LOCAL_{i}{type_to_suffix(l)}\n")
                        i += 1
                else:
                    pprint(elem)
            elif type(elem) is str:
                if elem == "local.set":
                    ii = int(mod.pop(0))
                    lt = local_types[ii]
                    out.write(f"LOCAL_{ii}{type_to_suffix(lt)} = POP({stack_name(lt)})\n")
                elif elem == "local.tee":
                    ii = int(mod.pop(0))
                    out.write(f"LOCAL_{ii}{type_to_suffix(lt)} = {stack_name(lt)}[LEN({stack_name(lt)})-1]\n")
                elif elem == "i32.const":
                    out.write(f"PUSH {stack_name('i32')}, {mod.pop(0)}\n")
                elif elem == "local.get":
                    ii = int(mod.pop(0))
                    lt = local_types[ii]
                    out.write(f"PUSH {stack_name(lt)}, LOCAL_{ii}{type_to_suffix(lt)}\n")
                elif elem == "i32.sub":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) DIV POP({stack_name(lt)})\n")
                elif elem == "i32.add":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) + POP({stack_name(lt)})\n")
                elif elem == "i32.shl":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) << POP({stack_name(lt)})\n")
                elif elem == "i32.gt_u":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, WASM_GT_U(POP({stack_name(lt)}), POP({stack_name(lt)}))\n")
                elif elem == "i32.gt_s":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) > POP({stack_name(lt)})\n")
                elif elem == "i32.ge_s":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) >= POP({stack_name(lt)})\n")
                elif elem == "i32.lt_s":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) < POP({stack_name(lt)})\n")
                elif elem == "i32.eq":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) == POP({stack_name(lt)})\n")
                elif elem == "i32.ne":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, POP({stack_name(lt)}) != POP({stack_name(lt)})\n")
                elif elem == "global.get":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, GLOBAL{get_name(mod.pop(0))}\n")
                elif elem == "global.set":
                    lt = "i32"
                    out.write(f"GLOBAL{get_name(mod.pop(0))} = POP({stack_name(lt)})\n")
                elif elem == "return":
                    out.write("RETURN\n")
                elif elem == "call":
                    func_name = get_name(mod.pop(0))
                    return_type = func_return_types[func_name]
                    if return_type == "void":
                        out.write(f"{func_name} POP({stack_name('i32')})\n")
                    elif return_type == "i32":
                        out.write(f"PUSH {stack_name('i32')}, {func_name}(POP({stack_name('i32')}))\n")
                elif elem == "end":
                    block_stack.pop()
                    out.write(end_stack.pop())
                elif elem == "block":
                    out.write(f"@BS_{block_index}\n")
                    block_stack.append(f"GOTO @BE_{block_index}")
                    end_stack.append(f"@BE_{block_index}\n")
                    block_index += 1
                elif elem == "loop":
                    out.write(f"@BS_{block_index}\n")
                    block_stack.append(f"GOTO @BS_{block_index}")
                    end_stack.append(f"@BE_{block_index}\n")
                    block_index += 1
                elif elem == "i32.load":
                    out.write(f"PUSH {stack_name('i32')}, READ32(POP({stack_name('i32')}))\n")
                elif elem == "br_if":
                    out.write(f"IF POP({stack_name('i32')}) != 0 THEN {block_stack[-1-int(mod.pop(0))]}\n")
                elif elem == "br":
                    out.write(f"{block_stack[-1-int(mod.pop(0))]}\n")
                elif elem == "select":
                    lt = "i32"
                    out.write(f"PUSH {stack_name(lt)}, WASMSELECT(POP({stack_name(lt)}), POP({stack_name(lt)}), POP({stack_name(lt)}))\n")
                else:
                    out.write(f"' UNKNOWN: " + elem + "\n")
                    pprint(elem)
        out.write(f"END\n")
    elif module_type == "export":
        if mod[1][0] == "func" and mod[0].value == "main":
            main_func = f"{get_name(mod[1][1])}\n"
    elif module_type == "data":
        address = 0
        while len(mod):
            elem = mod.pop(0)
            if type(elem) is list:
                if elem[0] == "i32.const":
                    address = int(elem[1])
            elif type(elem) is SString:
                for c in elem.bytes:
                    if c != 0:
                        # skip 0
                        out.write(f"WRITE8 {address}, {c}\n")
                    address += 1
            else:
                pprint(elem)
    else:
        pprint(mod)

out.write(main_func)