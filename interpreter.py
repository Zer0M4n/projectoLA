import io
import sys

# Excepción de control de flujo para manejar la instrucción 'return'
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

class InterpreterError(Exception):
    """Error del intérprete con información de línea"""
    def __init__(self, message, line_num=None):
        self.message = message
        self.line_num = line_num
        super().__init__(self.format_message())
    
    def format_message(self):
        if self.line_num:
            return f"❌ Error en línea {self.line_num}: {self.message}"
        return f"❌ Error: {self.message}"

class Interpreter:
    def __init__(self):
        self.global_env = {}
        self.functions = {}
        self.output = io.StringIO()
        self.current_line = 0

    def run(self, code):
        sys_stdout = sys.stdout
        sys.stdout = self.output
        self.global_env = {}
        self.functions = {}

        try:
            lines = self._tokenize(code)
            self._execute_block(lines, self.global_env) 
        except ReturnValue as e:
            pass 
        finally:
            sys.stdout = sys_stdout

        return self.output.getvalue()

    # --- Tokenización básica con indentación ---
    def _tokenize(self, code):
        result = []
        for raw in code.strip().splitlines():
            if not raw.strip():
                continue
            raw_processed = raw.replace('\t', '    ') 
            indent = len(raw_processed) - len(raw_processed.lstrip())
            result.append((indent, raw.strip()))
        return result

    # --- Ejecutar un bloque de líneas ---
    def _execute_block(self, lines, env, start=0, base_indent=0):
        i = start
        while i < len(lines):
            indent, line = lines[i]
            
            if indent < base_indent:
                return i

            if line.startswith("func "):
                i = self._define_function(lines, i)
                continue

            elif line.startswith("if "):
                i = self._handle_if_else(lines, i, env, base_indent)
                continue
            
            elif line.startswith("else:") or line.startswith("elif "):
                pass 

            elif line.startswith("var "):
                var_name, expr = line[4:].split("=", 1)
                env[var_name.strip()] = self._eval_expr(expr.strip(), env)

            elif line.startswith("print("):
                val = self._eval_expr(line[6:-1], env)
                print(val)

            else:
                self._eval_expr(line, env)

            i += 1
        return i

    # --- Definición de funciones ---
    def _define_function(self, lines, index):
        _, line = lines[index]
        name = line[5:line.index("(")].strip()
        args = line[line.index("(")+1:line.index(")")].strip()
        arg_list = [a.strip() for a in args.split(",") if a.strip()]

        body = []
        index += 1
        
        if index < len(lines):
            func_indent = lines[index][0]
            while index < len(lines) and lines[index][0] >= func_indent:
                body.append(lines[index])
                index += 1
        
        if index < len(lines) and lines[index][0] > lines[index-1][0]:
            index -= 1

        self.functions[name] = (arg_list, body)
        return index

    # --- Manejo de IF/ELSE ---
    def _handle_if_else(self, lines, index, env, base_indent):
        indent, line = lines[index]
        condition = line[3:].rstrip(":").strip()
        cond_value = bool(self._eval_expr(condition, env))

        current_index = index + 1
        if_block, else_block = [], []
        
        if_indent = 0
        if current_index < len(lines):
            if_indent = lines[current_index][0]
            while current_index < len(lines) and lines[current_index][0] >= if_indent:
                if lines[current_index][0] > indent: 
                    if_block.append(lines[current_index])
                    current_index += 1
                else: 
                    break 

        index_after_if_block = current_index

        else_indent = 0
        if index_after_if_block < len(lines) and lines[index_after_if_block][1].startswith("else:"):
            current_index = index_after_if_block + 1
            if current_index < len(lines):
                else_indent = lines[current_index][0]
                while current_index < len(lines) and lines[current_index][0] >= else_indent:
                    if lines[current_index][0] > indent:
                        else_block.append(lines[current_index])
                        current_index += 1
                    else:
                        break

        try:
            if cond_value and if_block:
                self._execute_block(if_block, env, 0, if_block[0][0])
            elif else_block:
                self._execute_block(else_block, env, 0, else_block[0][0])
        except ReturnValue as e:
            raise e
        
        return current_index

    # --- Evaluación de expresiones ---
    def _eval_expr(self, expr, env):
        safe_builtins = {
            "str": str, "int": int, "float": float,
            "print": print, "len": len, "range": range,
        }

        expr = expr.strip()
        
        if expr.startswith("return "):
            return_value_expr = expr[len("return "):].strip()
            value = self._eval_expr(return_value_expr, env) 
            raise ReturnValue(value)
        
        # CORRECCIÓN: Crear entorno con variables Y funciones
        func_env = env.copy()
        
        # SOLUCIÓN AL PROBLEMA: Usar una función factory para evitar el problema de closure
        def make_function_caller(fname):
            def caller(*args):
                return self._call_function(fname, list(args))
            return caller
        
        for fname in self.functions:
            func_env[fname] = make_function_caller(fname)

        try:
            return eval(expr, {"__builtins__": safe_builtins}, func_env)
        except ReturnValue as e:
            raise e
        except Exception as e:
            raise Exception(f"Error evaluando '{expr}': {e}")

    # --- Llamadas a funciones ---
    def _call_function(self, name, arg_values):
        args, body = self.functions[name]
        
        # Crear entorno local con copia del global
        local_env = self.global_env.copy() 
        
        for i, arg_name in enumerate(args):
            if i < len(arg_values):
                local_env[arg_name] = arg_values[i]
        
        return_value = None
        
        try:
            if body:
                base_indent = body[0][0]
                self._execute_block(body, local_env, 0, base_indent)
            
        except ReturnValue as e:
            return_value = e.value
        
        return return_value


# Prueba
if __name__ == "__main__":
    print("="*50)
    print("PRUEBA 1: Factorial recursivo")
    print("="*50)
    test_code1 = """func factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

var resultado = factorial(5)
print(resultado)"""
    
    interp = Interpreter()
    output = interp.run(test_code1)
    print("Salida:")
    print(output)
    print()
    
    print("="*50)
    print("PRUEBA 2: Variables simples")
    print("="*50)
    test_code2 = """var x = 10
var y = 20
var suma = x + y
print(suma)"""
    
    interp2 = Interpreter()
    output2 = interp2.run(test_code2)
    print("Salida:")
    print(output2)
    print()
    
    print("="*50)
    print("PRUEBA 3: Sin recursión")
    print("="*50)
    test_code3 = """func doble(n):
    return n * 2

var numero = 5
var resultado = doble(numero)
print(resultado)"""
    
    interp3 = Interpreter()
    output3 = interp3.run(test_code3)
    print("Salida:")
    print(output3)