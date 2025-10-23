import io
import sys
import re

# Excepciones de control de flujo
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

class BreakLoop(Exception):
    """Excepción para manejar 'break'"""
    pass

class ContinueLoop(Exception):
    """Excepción para manejar 'continue'"""
    pass

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
        self.current_line = 0

        try:
            lines = self._tokenize(code)
            self._execute_block(lines, self.global_env) 
        except ReturnValue:
            pass
        except InterpreterError as e:
            print(e.format_message())
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        finally:
            sys.stdout = sys_stdout

        return self.output.getvalue()

    # --- Tokenización básica con indentación ---
    def _tokenize(self, code):
        result = []
        for line_num, raw in enumerate(code.strip().splitlines(), start=1):
            if not raw.strip() or raw.strip().startswith("#"):
                continue
            raw_processed = raw.replace('\t', '    ') 
            indent = len(raw_processed) - len(raw_processed.lstrip())
            result.append((indent, raw.strip(), line_num))
        return result

    # --- Ejecutar un bloque de líneas ---
    def _execute_block(self, lines, env, start=0, base_indent=0):
        i = start
        while i < len(lines):
            indent, line, line_num = lines[i]
            self.current_line = line_num
            
            if indent < base_indent:
                return i

            try:
                if line.startswith("func "):
                    i = self._define_function(lines, i)
                    continue

                elif line.startswith("if "):
                    i = self._handle_if_elif_else(lines, i, env, base_indent)
                    continue
                
                elif line.startswith("while "):
                    i = self._handle_while(lines, i, env, base_indent)
                    continue
                
                elif line.startswith("for "):
                    i = self._handle_for(lines, i, env, base_indent)
                    continue
                
                elif line == "break":
                    raise BreakLoop()
                
                elif line == "continue":
                    raise ContinueLoop()
                
                elif line.startswith("else:") or line.startswith("elif "):
                    pass 

                elif line.startswith("var "):
                    self._handle_var_declaration(line, env, line_num)

                elif line.startswith("print("):
                    val = self._eval_expr(line[6:-1], env, line_num)
                    print(val)

                else:
                    # Detectar reasignación de variable (sin var)
                    if "=" in line and not line.startswith(("if ", "elif ", "while ", "for ", "func ", "return")):
                        self._handle_assignment(line, env, line_num)
                    else:
                        self._eval_expr(line, env, line_num)

            except (ReturnValue, BreakLoop, ContinueLoop):
                raise
            except InterpreterError:
                raise
            except Exception as e:
                raise InterpreterError(str(e), line_num)

            i += 1
        return i

    # --- Definición de funciones ---
    def _define_function(self, lines, index):
        _, line, line_num = lines[index]
        
        try:
            name = line[5:line.index("(")].strip()
            args = line[line.index("(")+1:line.index(")")].strip()
            arg_list = [a.strip() for a in args.split(",") if a.strip()]
        except (ValueError, AttributeError):
            raise InterpreterError("Sintaxis de función inválida", line_num)

        body = []
        index += 1
        
        if index < len(lines):
            func_indent = lines[index][0]
            while index < len(lines) and lines[index][0] >= func_indent:
                body.append(lines[index])
                index += 1
        
        if not body:
            raise InterpreterError(f"Función '{name}' está vacía", line_num)

        self.functions[name] = (arg_list, body)
        return index

    # --- Manejo de declaración de variables ---
    def _handle_var_declaration(self, line, env, line_num):
        """Maneja declaraciones de variables (var nombre = valor)"""
        try:
            if "=" not in line[4:]:
                raise InterpreterError("Declaración inválida: falta '=' (debe ser 'var nombre = valor')", line_num)
            
            var_name, expr = line[4:].split("=", 1)
            var_name = var_name.strip()
            expr = expr.strip()
            
            if not var_name:
                raise InterpreterError("Falta nombre de variable", line_num)
            
            if not expr:
                raise InterpreterError("Falta valor en la declaración", line_num)
            
            value = self._eval_expr(expr, env, line_num)
            env[var_name] = value
        except InterpreterError:
            raise
        except Exception as e:
            raise InterpreterError(f"Error en declaración de variable: {e}", line_num)

    # --- Manejo de reasignación de variables ---
    def _handle_assignment(self, line, env, line_num):
        """Maneja reasignaciones de variables (nombre = valor, sin var)"""
        try:
            if "=" not in line:
                raise InterpreterError("Asignación inválida", line_num)
            
            var_name, expr = line.split("=", 1)
            var_name = var_name.strip()
            expr = expr.strip()
            
            if not var_name:
                raise InterpreterError("Falta nombre de variable", line_num)
            
            if not expr:
                raise InterpreterError("Falta valor en la asignación", line_num)
            
            # Verificar que la variable exista (opcional, puedes crear nuevas sin var)
            # if var_name not in env:
            #     raise InterpreterError(f"Variable '{var_name}' no está definida. Usa 'var {var_name} = ...' para declararla", line_num)
            
            value = self._eval_expr(expr, env, line_num)
            env[var_name] = value
        except InterpreterError:
            raise
        except Exception as e:
            raise InterpreterError(f"Error en asignación: {e}", line_num)

    # --- Manejo de IF/ELIF/ELSE ---
    def _handle_if_elif_else(self, lines, index, env, base_indent):
        blocks = []  # Lista de (condición, cuerpo)
        else_block = None
        current_index = index
        
        while current_index < len(lines):
            indent, line, line_num = lines[current_index]
            
            if indent < base_indent:
                break
            
            if indent == base_indent:
                # Detectar if o elif
                if line.startswith("if ") or line.startswith("elif "):
                    prefix = "if " if line.startswith("if ") else "elif "
                    condition = line[len(prefix):].rstrip(":").strip()
                    
                    if not condition:
                        raise InterpreterError(f"Falta condición después de '{prefix.strip()}'", line_num)
                    
                    current_index += 1
                    body = []
                    if current_index < len(lines):
                        body_indent = lines[current_index][0]
                        while current_index < len(lines) and lines[current_index][0] >= body_indent:
                            if lines[current_index][0] > indent:
                                body.append(lines[current_index])
                                current_index += 1
                            else:
                                break
                    
                    blocks.append((condition, body, line_num))
                
                # Detectar else
                elif line == "else:":
                    current_index += 1
                    else_block = []
                    if current_index < len(lines):
                        else_indent = lines[current_index][0]
                        while current_index < len(lines) and lines[current_index][0] >= else_indent:
                            if lines[current_index][0] > indent:
                                else_block.append(lines[current_index])
                                current_index += 1
                            else:
                                break
                    break
                else:
                    break
            else:
                break
        
        # Ejecutar el primer bloque verdadero
        executed = False
        for condition, body, cond_line_num in blocks:
            try:
                cond_value = bool(self._eval_expr(condition, env, cond_line_num))
            except Exception as e:
                raise InterpreterError(f"Error en condición: {e}", cond_line_num)
            
            if cond_value:
                if body:
                    self._execute_block(body, env, 0, body[0][0])
                executed = True
                break
        
        # Ejecutar else si ninguna condición fue verdadera
        if not executed and else_block:
            self._execute_block(else_block, env, 0, else_block[0][0])
        
        return current_index

    # --- Manejo de bucles WHILE ---
    def _handle_while(self, lines, index, env, base_indent):
        indent, line, line_num = lines[index]
        condition = line[6:].rstrip(":").strip()
        
        if not condition:
            raise InterpreterError("Falta condición en bucle while", line_num)
        
        # Capturar cuerpo del while
        body = []
        current_index = index + 1
        if current_index < len(lines):
            body_indent = lines[current_index][0]
            while current_index < len(lines) and lines[current_index][0] >= body_indent:
                if lines[current_index][0] > indent:
                    body.append(lines[current_index])
                    current_index += 1
                else:
                    break
        
        if not body:
            raise InterpreterError("Bucle while vacío", line_num)
        
        # Ejecutar bucle con límite de iteraciones
        iterations = 0
        max_iterations = 100000
        
        while iterations < max_iterations:
            try:
                cond_value = bool(self._eval_expr(condition, env, line_num))
            except Exception as e:
                raise InterpreterError(f"Error en condición del while: {e}", line_num)
            
            if not cond_value:
                break
            
            try:
                self._execute_block(body, env, 0, body[0][0])
                iterations += 1
            except BreakLoop:
                break
            except ContinueLoop:
                iterations += 1
                continue
        
        if iterations >= max_iterations:
            raise InterpreterError("Bucle while excedió el límite de 100,000 iteraciones (posible bucle infinito)", line_num)
        
        return current_index

    # --- Manejo de bucles FOR ---
    def _handle_for(self, lines, index, env, base_indent):
        indent, line, line_num = lines[index]
        
        # Extraer variable e iterable: for var in iterable:
        match = re.match(r'for\s+(\w+)\s+in\s+(.+):', line)
        if not match:
            raise InterpreterError("Sintaxis de bucle for inválida (debe ser: for variable in iterable:)", line_num)
        
        var_name = match.group(1)
        iterable_expr = match.group(2).strip()
        
        # Capturar cuerpo del for
        body = []
        current_index = index + 1
        if current_index < len(lines):
            body_indent = lines[current_index][0]
            while current_index < len(lines) and lines[current_index][0] >= body_indent:
                if lines[current_index][0] > indent:
                    body.append(lines[current_index])
                    current_index += 1
                else:
                    break
        
        if not body:
            raise InterpreterError("Bucle for vacío", line_num)
        
        # Evaluar iterable
        try:
            iterable = self._eval_expr(iterable_expr, env, line_num)
        except Exception as e:
            raise InterpreterError(f"Error al evaluar iterable: {e}", line_num)
        
        # Verificar que sea iterable
        try:
            iter(iterable)
        except TypeError:
            raise InterpreterError(f"'{iterable_expr}' no es iterable", line_num)
        
        # Ejecutar bucle
        for value in iterable:
            env[var_name] = value
            try:
                self._execute_block(body, env, 0, body[0][0])
            except BreakLoop:
                break
            except ContinueLoop:
                continue
        
        return current_index

    # --- Evaluación de expresiones ---
    def _eval_expr(self, expr, env, line_num=None):
        safe_builtins = {
            "str": str, 
            "int": int, 
            "float": float,
            "bool": bool,
            "print": print, 
            "len": len, 
            "range": range,
            "list": list,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "reversed": reversed,
            "enumerate": enumerate,
        }

        expr = expr.strip()
        
        if expr.startswith("return "):
            return_value_expr = expr[len("return "):].strip()
            value = self._eval_expr(return_value_expr, env, line_num) if return_value_expr else None
            raise ReturnValue(value)
        
        if expr == "return":
            raise ReturnValue(None)
        
        # Crear entorno con variables Y funciones
        func_env = env.copy()
        
        # Agregar builtins
        func_env.update(safe_builtins)
        
        # Usar una función factory para evitar el problema de closure
        def make_function_caller(fname):
            def caller(*args):
                return self._call_function(fname, list(args))
            return caller
        
        for fname in self.functions:
            func_env[fname] = make_function_caller(fname)

        try:
            return eval(expr, {"__builtins__": {}}, func_env)
        except ReturnValue:
            raise
        except NameError as e:
            var_name = str(e).split("'")[1] if "'" in str(e) else "desconocida"
            raise InterpreterError(f"Variable o función '{var_name}' no está definida", line_num)
        except SyntaxError as e:
            raise InterpreterError(f"Sintaxis inválida en expresión", line_num)
        except ZeroDivisionError:
            raise InterpreterError("División por cero", line_num)
        except TypeError as e:
            raise InterpreterError(f"Error de tipo: {e}", line_num)
        except IndexError as e:
            raise InterpreterError(f"Índice fuera de rango: {e}", line_num)
        except KeyError as e:
            raise InterpreterError(f"Clave no encontrada: {e}", line_num)
        except ValueError as e:
            raise InterpreterError(f"Valor inválido: {e}", line_num)
        except Exception as e:
            raise InterpreterError(f"Error al evaluar expresión: {e}", line_num)

    # --- Llamadas a funciones ---
    def _call_function(self, name, arg_values):
        if name not in self.functions:
            raise InterpreterError(f"Función '{name}' no está definida")
        
        args, body = self.functions[name]
        
        # Verificar número de argumentos
        if len(arg_values) < len(args):
            raise InterpreterError(f"Función '{name}' espera {len(args)} argumentos, pero recibió {len(arg_values)}")
        
        if len(arg_values) > len(args):
            raise InterpreterError(f"Función '{name}' espera {len(args)} argumentos, pero recibió {len(arg_values)} (demasiados)")
        
        # Crear entorno local con copia del global
        local_env = self.global_env.copy() 
        
        for i, arg_name in enumerate(args):
            local_env[arg_name] = arg_values[i]
        
        return_value = None
        
        try:
            if body:
                base_indent = body[0][0]
                self._execute_block(body, local_env, 0, base_indent)
        except ReturnValue as e:
            return_value = e.value
        
        return return_value


# Pruebas completas
if __name__ == "__main__":
    print("="*60)
    print("PRUEBA 1: Factorial recursivo")
    print("="*60)
    test1 = """func factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

var resultado = factorial(5)
print(resultado)"""
    
    interp = Interpreter()
    print(interp.run(test1))
    
    print("="*60)
    print("PRUEBA 2: Bucle while con reasignación")
    print("="*60)
    test2 = """var i = 0
while i < 5:
    print(i)
    i = i + 1"""
    
    interp2 = Interpreter()
    print(interp2.run(test2))
    
    print("="*60)
    print("PRUEBA 3: Bucle for con range")
    print("="*60)
    test3 = """for i in range(5):
    print(i)"""
    
    interp3 = Interpreter()
    print(interp3.run(test3))
    
    print("="*60)
    print("PRUEBA 4: Bucle for con string")
    print("="*60)
    test4 = """for letra in "Hola":
    print(letra)"""
    
    interp4 = Interpreter()
    print(interp4.run(test4))
    
    print("="*60)
    print("PRUEBA 5: Break y Continue")
    print("="*60)
    test5 = """for i in range(10):
    if i == 3:
        continue
    if i == 7:
        break
    print(i)"""
    
    interp5 = Interpreter()
    print(interp5.run(test5))
    
    print("="*60)
    print("PRUEBA 6: If/Elif/Else")
    print("="*60)
    test6 = """var x = 10
if x > 10:
    print("Mayor")
elif x == 10:
    print("Igual")
else:
    print("Menor")"""
    
    interp6 = Interpreter()
    print(interp6.run(test6))
    
    print("="*60)
    print("PRUEBA 7: Funciones con built-ins")
    print("="*60)
    test7 = """var numeros = [1, 2, 3, 4, 5]
print(sum(numeros))
print(max(numeros))
print(len(numeros))"""
    
    interp7 = Interpreter()
    print(interp7.run(test7))
    
    print("="*60)
    print("PRUEBA 8: Error - Variable no definida")
    print("="*60)
    test8 = """print(variable_no_existe)"""
    
    interp8 = Interpreter()
    print(interp8.run(test8))
    
    print("="*60)
    print("PRUEBA 9: Error - División por cero")
    print("="*60)
    test9 = """var x = 10 / 0"""
    
    interp9 = Interpreter()
    print(interp9.run(test9))
    
    print("="*60)
    print("PRUEBA 10: Error - Bucle infinito detectado")
    print("="*60)
    test10 = """var i = 0
while i < 10:
    print(i)"""
    
    interp10 = Interpreter()
    print(interp10.run(test10))