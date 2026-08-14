"""
Punto de entrada principal de la aplicación
"""
import os
import sys

# Verificar que existe la base de datos
if not os.path.exists("data/inventory.db"):
    print("Base de datos no encontrada. Generando datos iniciales...")
    try:
        from generate_data import generate_synthetic_data
        generate_synthetic_data(1000)
        print("[OK] Datos generados. Iniciando aplicacion...\n")
    except Exception as e:
        print(f"Error al generar datos: {e}")
        sys.exit(1)

# Iniciar aplicación GUI
try:
    from gui.app import InventoryApp
    
    if __name__ == "__main__":
        print("Iniciando aplicación GUI...")
        app = InventoryApp()
        app.mainloop()
except Exception as e:
    import traceback
    print(f"Error al iniciar la aplicación: {e}")
    traceback.print_exc()
    input("Presiona Enter para salir...")
    sys.exit(1)

