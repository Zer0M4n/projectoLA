"""
Checker sintáctico mejorado para el lenguaje Pyra.
Detecta errores de sintaxis, indentación y buenas prácticas.
"""

import re

class Checker:
    def __init__(self):
        self.keywords = {'var', 'func', 'if', 'elif', 'else', 'return', 'print', 'while', 'for', 'in', 'break', 'continue'}
        self.typos = {
            'retun': 'return',
            'retunr': 'return',
            'retur': 'return',
            'pritn': 'print',
            'prnit': 'print',
            'fucn': 'func',
            'funct': 'func',
            'esle': 'else',
            'fi': 'if',
            'vra': 'var',
            'vaar': 'var',
            'whlie': 'while',
            'wile': 'while',
            'fro': 'for',
            'braek': 'break',
            'contiue': 'continue',
            'contineu': 'continue'
        }

    def check(self, source):
        if not source:
            return []

        errors = []
        lines = source.splitlines()
        
        errors.extend(self.check_indentation(lines))
        errors.extend(self.check_block_syntax(lines))
        errors.extend(self.check_var_declarations(lines))
        errors.extend(self.check_balanced_delimiters(lines))
        errors.extend(self.check_return_placement(lines))
        errors.extend(self.check_break_continue_placement(lines))
        errors.extend(self.check_typos(lines))
        errors.extend(self.check_empty_blocks(lines))
        errors.extend(self.check_string_literals(lines))
        
        return self.remove_duplicates(errors)

    def check_indentation(self, lines):
        errors = []
        prev_indent = 0
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if "\t" in raw:
                errors.append({
                    "line": i,
                    "column": raw.find("\t") + 1,
                    "message": "Usa 4 espacios en lugar de tabulaciones",
                    "severity": "error"
                })
                continue
            
            leading = len(raw) - len(raw.lstrip(" "))
            
            if leading % 4 != 0:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": "Indentacion debe ser multiplo de 4 espacios",
                    "severity": "error"
                })
        
        return errors

    def check_block_syntax(self, lines):
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if stripped.startswith("func "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final de la definicion de funcion",
                        "severity": "error"
                    })
                
                if "(" not in stripped or ")" not in stripped:
                    errors.append({
                        "line": i,
                        "column": 5,
                        "message": "Sintaxis de funcion invalida",
                        "severity": "error"
                    })
            
            if stripped.startswith("if ") or stripped.startswith("elif "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final de la condicion",
                        "severity": "error"
                    })
            
            if stripped.startswith("while "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final del while",
                        "severity": "error"
                    })
            
            if stripped.startswith("for "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final del for",
                        "severity": "error"
                    })
                
                if " in " not in stripped:
                    errors.append({
                        "line": i,
                        "column": 5,
                        "message": "Falta 'in' en el bucle for",
                        "severity": "error"
                    })
            
            if stripped.startswith("else"):
                if stripped != "else:":
                    errors.append({
                        "line": i,
                        "column": 1,
                        "message": "Sintaxis incorrecta: debe ser 'else:'",
                        "severity": "error"
                    })
        
        return errors

    def check_var_declarations(self, lines):
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            
            if stripped.startswith("var "):
                if "=" not in stripped:
                    errors.append({
                        "line": i,
                        "column": 1,
                        "message": "Declaracion invalida: debe ser 'var nombre = valor'",
                        "severity": "error"
                    })
                    continue
                
                parts = stripped[4:].split("=", 1)
                var_name = parts[0].strip()
                
                if not var_name:
                    errors.append({
                        "line": i,
                        "column": 5,
                        "message": "Falta nombre de variable",
                        "severity": "error"
                    })
                    continue
                
                pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
                if not re.match(pattern, var_name):
                    errors.append({
                        "line": i,
                        "column": 5,
                        "message": "Nombre de variable invalido",
                        "severity": "error"
                    })
                
                if len(parts) < 2 or not parts[1].strip():
                    errors.append({
                        "line": i,
                        "column": raw.find("=") + 2,
                        "message": "Falta valor en la declaracion",
                        "severity": "error"
                    })
        
        return errors

    def check_balanced_delimiters(self, lines):
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            open_paren = stripped.count("(")
            close_paren = stripped.count(")")
            
            if open_paren != close_paren:
                col = stripped.find("(") + 1 if open_paren > close_paren else stripped.find(")") + 1
                errors.append({
                    "line": i,
                    "column": col if col > 0 else 1,
                    "message": "Parentesis desbalanceados",
                    "severity": "error"
                })
        
        return errors

    def check_return_placement(self, lines):
        errors = []
        in_func = False
        func_indent = 0
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            indent = len(raw) - len(raw.lstrip(" "))
            
            if stripped.startswith("func ") and stripped.endswith(":"):
                in_func = True
                func_indent = indent
                continue
            
            if in_func and indent <= func_indent:
                in_func = False
            
            if stripped.startswith("return") and not in_func:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": "'return' solo puede usarse dentro de una funcion",
                    "severity": "error"
                })
        
        return errors

    def check_break_continue_placement(self, lines):
        errors = []
        in_loop = False
        loop_indent = 0
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            indent = len(raw) - len(raw.lstrip(" "))
            
            if (stripped.startswith("while ") or stripped.startswith("for ")) and stripped.endswith(":"):
                in_loop = True
                loop_indent = indent
                continue
            
            if in_loop and indent <= loop_indent:
                in_loop = False
            
            if (stripped == "break" or stripped == "continue") and not in_loop:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": f"'{stripped}' solo puede usarse dentro de un bucle",
                    "severity": "error"
                })
        
        return errors

    def check_typos(self, lines):
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            for typo, correct in self.typos.items():
                pattern = r'\b' + re.escape(typo) + r'\b'
                if re.search(pattern, raw):
                    errors.append({
                        "line": i,
                        "column": raw.find(typo) + 1,
                        "message": f"Posible error: ¿quisiste escribir '{correct}'?",
                        "severity": "warning"
                    })
        
        return errors

    def check_empty_blocks(self, lines):
        errors = []
        
        for i in range(len(lines)):
            stripped = lines[i].strip()
            
            if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
                continue
            
            current_indent = len(lines[i]) - len(lines[i].lstrip(" "))
            has_body = False
            
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                next_stripped = next_line.strip()
                
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                
                if next_indent > current_indent:
                    has_body = True
                    break
                else:
                    break
            
            if not has_body:
                errors.append({
                    "line": i + 1,
                    "column": len(lines[i].rstrip()) + 1,
                    "message": "Bloque vacio",
                    "severity": "warning"
                })
        
        return errors

    def check_string_literals(self, lines):
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            single_quotes = len(re.findall(r"(?<!\\)'", raw))
            double_quotes = len(re.findall(r'(?<!\\)"', raw))
            
            if single_quotes % 2 != 0:
                errors.append({
                    "line": i,
                    "column": raw.find("'") + 1,
                    "message": "Comillas simples desbalanceadas",
                    "severity": "error"
                })
            
            if double_quotes % 2 != 0:
                errors.append({
                    "line": i,
                    "column": raw.find('"') + 1,
                    "message": "Comillas dobles desbalanceadas",
                    "severity": "error"
                })
        
        return errors

    def remove_duplicates(self, errors):
        seen = set()
        clean = []
        
        for e in errors:
            key = (e["line"], e.get("column", 0), e["message"])
            if key not in seen:
                seen.add(key)
                clean.append(e)
        
        return sorted(clean, key=lambda x: (x["line"], x.get("column", 0)))


if __name__ == "__main__":
    print("="*60)
    print("PRUEBA: Codigo de ejemplo")
    print("="*60)
    test = """func factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

var resultado = factorial(5)
print(resultado)"""
    
    checker = Checker()
    errors = checker.check(test)
    
    if errors:
        for err in errors:
            print(f"[{err['severity'].upper()}] Linea {err['line']}: {err['message']}")
    else:
        print("Sin errores")