from interpreter import Interpreter  # Asegúrate de que el archivo se llame interpreter.py

def run_test(title, code, expected_output):
    print(f"\n=== {title} ===")
    interp = Interpreter()
    result = interp.run(code).strip()
    print("Salida:")
    print(result)
    if result == expected_output.strip():
        print("✔ OK")
    else:
        print("❌ Esperado:")
        print(expected_output.strip())


# --- TEST 1: Variables numéricas y operaciones ---
test1 = """
var x = 10
var y = 5
print(x + y)
print(x * y)
"""
expected1 = """
15
50
"""
run_test("Variables numéricas", test1, expected1)


# --- TEST 2: Strings y concatenación ---
test2 = """
var saludo = "Hola"
var nombre = "César"
print(saludo + " " + nombre)
"""
expected2 = """
Hola César
"""
run_test("Strings y concatenación", test2, expected2)


# --- TEST 3: If / else ---
test3 = """
var edad = 20
if edad >= 18:
    print("Mayor de edad")
else:
    print("Menor de edad")
"""
expected3 = """
Mayor de edad
"""
run_test("Condicional if/else", test3, expected3)


# --- TEST 4: Función simple ---
test4 = """
func hola():
    print("Hola mundo")

hola()
"""
expected4 = """
Hola mundo
"""
run_test("Función sin parámetros", test4, expected4)


# --- TEST 5: Función con parámetros ---
test5 = """
func saludar(nombre):
    print("Hola " + nombre)

saludar("César")
saludar("Ana")
"""
expected5 = """
Hola César
Hola Ana
"""
run_test("Función con parámetros", test5, expected5)


# --- TEST 6: Función con return ---
test6 = """
func sumar(a, b):
    return a + b

var resultado = sumar(5, 3)
print("Resultado = " + str(resultado))
"""
expected6 = """
Resultado = 8
"""
run_test("Función con return", test6, expected6)


# --- TEST 7: Funciones anidadas y variables ---
test7 = """
func cuadrado(n):
    return n * n

func suma_de_cuadrados(a, b):
    var x = cuadrado(a)
    var y = cuadrado(b)
    return x + y

print("Resultado = " + str(suma_de_cuadrados(3, 4)))
"""
expected7 = """
Resultado = 25
"""
run_test("Funciones anidadas", test7, expected7)


# --- TEST 8: Uso combinado de todo ---
test8 = """
var nombre = "César"
var edad = 22

func presentar(nombre, edad):
    if edad >= 18:
        print(nombre + " es mayor de edad")
    else:
        print(nombre + " es menor de edad")

presentar(nombre, edad)

func doble(n):
    return n * 2

var resultado = doble(10)
print("El doble es " + str(resultado))
"""
expected8 = """
César es mayor de edad
El doble es 20
"""
run_test("Uso combinado de todo", test8, expected8)
