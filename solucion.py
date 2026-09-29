"""
Módulo solucion.py adaptado desde Ev1.
Mantiene las funciones puras de evaluación de inventario para compatibilidad directa
y soporte de scripts o consola.
"""
import json
import os
from tabulate import tabulate

from core.services import decidir_salida_inventario


def procesar_solicitud_cli():
    print("=== SISTEMA DE CONTROL DE INVENTARIO Y DESPACHOS (CLI - EVA 3) ===")

    producto = input("Ingrese el nombre del producto: ").strip()

    try:
        stock_actual = int(input("Ingrese el stock actual en bodega: "))
        cantidad_solicitada = int(input("Ingrese la cantidad a retirar: "))
    except ValueError:
        print("\nError: Debe ingresar números enteros válidos para el stock y la cantidad.")
        return

    # Evaluar decisión con las 4 reglas del negocio
    estado, motivo = decidir_salida_inventario(producto, stock_actual, cantidad_solicitada)

    print(f"\n[RESULTADO]: {estado}")
    print(f"[MOTIVO]: {motivo}\n")

    nuevo_registro = {
        "producto": producto,
        "stock_actual": stock_actual,
        "cantidad_solicitada": cantidad_solicitada,
        "estado": estado,
        "motivo": motivo
    }

    archivo_json = "datos.json"
    registros = []

    if os.path.exists(archivo_json):
        with open(archivo_json, "r", encoding="utf-8") as f:
            try:
                registros = json.load(f)
            except json.JSONDecodeError:
                registros = []

    registros.append(nuevo_registro)

    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=2, ensure_ascii=False)

    print("--- HISTORIAL DE MOVIMIENTOS REGISTRADOS ---")
    print(tabulate(registros, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    procesar_solicitud_cli()
