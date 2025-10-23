"""
Checker sintáctico mejorado para el lenguaje Pyra.
Detecta errores de sintaxis, indentación y buenas prácticas.
"""

import re

class Checker:
    def __init__(self):
        self.keywords = {'var', 'func', 'if', 'elif', 'else', 'return', 'print'}
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
            'vaar': 'var'
        }

    def check(self, source: str):
        if not source:
            return []

        errors = []
        lines = source.splitlines()
        
        # Ejecutar validaciones
        errors.extend(self._check_indentation(lines))
        errors.extend(self._check_block_syntax(lines))
        errors.extend(self._check_var_declarations(lines))
        errors.extend(self._check_balanced_delimiters(lines))
        errors.extend(self._check_return_placement(lines))
        errors.extend(self._check_typos(lines))
        errors.extend(self._check_empty_blocks(lines))
        errors.extend(self._check_function_syntax(lines))
        errors.extend(self._check_string_literals(lines))
        
        return self._remove_duplicates(errors)

    def _check_indentation(self, lines):
        """Verifica indentación (múltiplos de 4 espacios, sin tabs)"""
        errors = []
        prev_indent = 0
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            # Detectar tabs
            if "\t" in raw:
                errors.append({
                    "line": i,
                    "column": raw.find("\t") + 1,
                    "message": "Usa 4 espacios en lugar de tabulaciones",
                    "severity": "error"
                })
                continue
            
            # Calcular indentación
            leading = len(raw) - len(raw.lstrip(" "))
            
            # Verificar múltiplo de 4
            if leading % 4 != 0:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": f"Indentación debe ser múltiplo de 4 espacios (encontrado: {leading})",
                    "severity": "error"
                })
                continue
            
            # Verificar saltos de indentación válidos
            indent_diff = leading - prev_indent
            
            # Si aumenta la indentación, debe ser exactamente 4
            if indent_diff > 4:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": f"Indentación aumenta demasiado (debe aumentar de 4 en 4)",
                    "severity": "error"
                })
            
            # Actualizar para líneas que definen bloques
            if stripped.endswith(":"):
                prev_indent = leading + 4
            elif not stripped.startswith(("else:", "elif ")):
                prev_indent = leading
        
        return errors

    def _check_block_syntax(self, lines):
        """Verifica estructuras de control terminen con ':'"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            # func NAME(args):
            if stripped.startswith("func "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final de la definición de función",
                        "severity": "error"
                    })
                
                if "(" not in stripped or ")" not in stripped:
                    errors.append({
                        "line": i,
                        "column": 5,
                        "message": "Sintaxis de función inválida: debe ser 'func nombre(params):'",
                        "severity": "error"
                    })
                else:
                    # Verificar orden de paréntesis
                    open_pos = stripped.find("(")
                    close_pos = stripped.rfind(")")
                    if open_pos > close_pos or close_pos < open_pos:
                        errors.append({
                            "line": i,
                            "column": open_pos + 1,
                            "message": "Paréntesis mal formados en función",
                            "severity": "error"
                        })
            
            # if/elif
            if stripped.startswith("if ") or stripped.startswith("elif "):
                if not stripped.endswith(":"):
                    errors.append({
                        "line": i,
                        "column": len(stripped) + 1,
                        "message": "Falta ':' al final de la condición",
                        "severity": "error"
                    })
                
                # Verificar que no esté vacío
                keyword = "if" if stripped.startswith("if ") else "elif"
                condition = stripped[len(keyword)+1:].rstrip(":")
                if not condition.strip():
                    errors.append({
                        "line": i,
                        "column": len(keyword) + 2,
                        "message": f"Falta condición después de '{keyword}'",
                        "severity": "error"
                    })
            
            # else
            if stripped.startswith("else"):
                if stripped != "else:":
                    errors.append({
                        "line": i,
                        "column": 1,
                        "message": "Sintaxis incorrecta: debe ser 'else:' (sin condición)",
                        "severity": "error"
                    })
        
        return errors

    def _check_var_declarations(self, lines):
        """Verifica declaraciones de variables"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped.startswith("var "):
                continue
            
            # Verificar que tenga '='
            if "=" not in stripped:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": "Declaración inválida: debe ser 'var nombre = valor'",
                    "severity": "error"
                })
                continue
            
            # Extraer partes
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
            
            # Verificar nombre válido
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                errors.append({
                    "line": i,
                    "column": 5,
                    "message": f"Nombre de variable '{var_name}' inválido (debe empezar con letra o _)",
                    "severity": "error"
                })
            
            # Verificar que tenga valor
            if len(parts) < 2 or not parts[1].strip():
                errors.append({
                    "line": i,
                    "column": raw.find("=") + 2,
                    "message": "Falta valor en la declaración",
                    "severity": "error"
                })
        
        return errors

    def _check_balanced_delimiters(self, lines):
        """Verifica balance de paréntesis, corchetes y llaves"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            # Contar delimitadores
            open_paren = stripped.count("(")
            close_paren = stripped.count(")")
            open_bracket = stripped.count("[")
            close_bracket = stripped.count("]")
            open_brace = stripped.count("{")
            close_brace = stripped.count("}")
            
            # Paréntesis
            if open_paren != close_paren:
                col = stripped.find("(") + 1 if open_paren > close_paren else stripped.find(")") + 1
                errors.append({
                    "line": i,
                    "column": col if col > 0 else 1,
                    "message": f"Paréntesis desbalanceados (abiertos: {open_paren}, cerrados: {close_paren})",
                    "severity": "error"
                })
            
            # Corchetes
            if open_bracket != close_bracket:
                col = stripped.find("[") + 1 if open_bracket > close_bracket else stripped.find("]") + 1
                errors.append({
                    "line": i,
                    "column": col if col > 0 else 1,
                    "message": f"Corchetes desbalanceados (abiertos: {open_bracket}, cerrados: {close_bracket})",
                    "severity": "error"
                })
            
            # Llaves
            if open_brace != close_brace:
                col = stripped.find("{") + 1 if open_brace > close_brace else stripped.find("}") + 1
                errors.append({
                    "line": i,
                    "column": col if col > 0 else 1,
                    "message": f"Llaves desbalanceadas (abiertas: {open_brace}, cerradas: {close_brace})",
                    "severity": "error"
                })
        
        return errors

    def _check_return_placement(self, lines):
        """Detecta 'return' fuera de función"""
        errors = []
        in_func = False
        func_indent = 0
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            indent = len(raw) - len(raw.lstrip(" "))
            
            # Detectar inicio de función
            if stripped.startswith("func ") and stripped.endswith(":"):
                in_func = True
                func_indent = indent
                continue
            
            # Salir del contexto de función si disminuye indentación
            if in_func and indent <= func_indent:
                in_func = False
            
            # Verificar return
            if stripped.startswith("return") and not in_func:
                errors.append({
                    "line": i,
                    "column": 1,
                    "message": "'return' solo puede usarse dentro de una función",
                    "severity": "error"
                })
        
        return errors

    def _check_typos(self, lines):
        """Detecta errores tipográficos comunes"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            for typo, correct in self.typos.items():
                # Buscar como palabra completa
                if re.search(r'\b' + re.escape(typo) + r'\b', raw):
                    errors.append({
                        "line": i,
                        "column": raw.find(typo) + 1,
                        "message": f"Posible error tipográfico: ¿quisiste escribir '{correct}'?",
                        "severity": "warning"
                    })
        
        return errors

    def _check_empty_blocks(self, lines):
        """Detecta bloques vacíos después de ':'"""
        errors = []
        
        for i in range(len(lines)):
            stripped = lines[i].strip()
            
            if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
                continue
            
            current_indent = len(lines[i]) - len(lines[i].lstrip(" "))
            has_body = False
            
            # Buscar contenido indentado
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
                    "message": "Bloque vacío: se esperaba contenido indentado",
                    "severity": "warning"
                })
        
        return errors

    def _check_function_syntax(self, lines):
        """Verifica sintaxis específica de funciones"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if not stripped.startswith("func "):
                continue
            
            # Verificar espacios alrededor del nombre
            match = re.match(r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped)
            if not match:
                if "(" in stripped:
                    errors.append({
                        "line": i,
                        "column": 6,
                        "message": "Nombre de función inválido",
                        "severity": "error"
                    })
            else:
                func_name = match.group(1)
                
                # Advertir sobre nombres no convencionales
                if func_name[0].isupper():
                    errors.append({
                        "line": i,
                        "column": 6,
                        "message": "Convención: nombres de funciones suelen empezar con minúscula",
                        "severity": "warning"
                    })
        
        return errors

    def _check_string_literals(self, lines):
        """Verifica comillas balanceadas"""
        errors = []
        
        for i, raw in enumerate(lines, start=1):
            # Contar comillas (ignorando escapadas básicamente)
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

    def _remove_duplicates(self, errors):
        """Elimina errores duplicados y ordena"""
        seen = set()
        clean = []
        
        for e in errors:
            key = (e["line"], e.get("column", 0), e["message"])
            if key not in seen:
                seen.add(key)
                clean.append(e)
        
        # Ordenar por línea y columna
        return sorted(clean, key=lambda x: (x["line"], x.get("column", 0)))


# Pruebas
if __name__ == "__main__":
    print("="*60)
    print("PRUEBA 1: Código correcto")
    print("="*60)
    test1 = """func factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

var resultado = factorial(5)
print(resultado)"""
    
    checker = Checker()
    errors = checker.check(test1)
    if errors:
        for err in errors:
            print(f"[{err['severity'].upper()}] Línea {err['line']}, Col {err['column']}: {err['message']}")
    else:
        print("✓ Sin errores")
    
    print("\n" + "="*60)
    print("PRUEBA 2: Código con errores")
    print("="*60)
    test2 = """func doble(n)
    retun n * 2

var x 
if x > 0
    print(x)"""
    
    errors = checker.check(test2)
    for err in errors:
        print(f"[{err['severity'].upper()}] Línea {err['line']}, Col {err['column']}: {err['message']}")
    
    print("\n" + "="*60)
    print("PRUEBA 3: Indentación incorrecta")
    print("="*60)
    test3 = """func test():
  var x = 5
     var y = 10
    return x + y"""
    
    errors = checker.check(test3)
    for err in errors:
        print(f"[{err['severity'].upper()}] Línea {err['line']}, Col {err['column']}: {err['message']}")