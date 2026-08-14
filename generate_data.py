"""
Script para generar datos sintéticos de inventario
Genera entre 500 y 2000 líneas de datos de prueba
"""
import random
import os
from database import InventoryDB


def generate_synthetic_data(num_nodes: int = 1000):
    """
    Genera datos sintéticos de nodos de inventario
    
    Args:
        num_nodes: Número de nodos a generar (por defecto 1000)
    """
    # Modelos posibles
    models = [
        "Cisco-2960X", "Cisco-3750G", "Cisco-3850", 
        "HP-ProCurve-2920", "HP-ProCurve-5406",
        "Juniper-EX2200", "Juniper-EX3300",
        "Aruba-2930F", "Aruba-6300M"
    ]
    
    # Áreas posibles
    areas = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]
    
    # Racks por área (1-20)
    racks_per_area = 20
    
    # Slots por rack (1-48)
    slots_per_rack = 48
    
    db = InventoryDB("data/inventory.db")
    
    print(f"Generando {num_nodes} nodos sintéticos...")
    
    generated = 0
    for i in range(num_nodes):
        model = random.choice(models)
        area = random.choice(areas)
        rack = random.randint(1, racks_per_area)
        slot = random.randint(1, slots_per_rack)
        
        # Generar número de serie único
        serial = f"{model[:3].upper()}-{random.randint(10000, 99999)}-{random.randint(100, 999)}"
        
        # Intentar añadir el nodo
        if db.add_node(serial, model, area, rack, slot):
            generated += 1
        
        if (i + 1) % 100 == 0:
            print(f"  Procesados: {i + 1}/{num_nodes}")
    
    print(f"\n[OK] Generados {generated} nodos exitosamente")
    print(f"  Modelos: {len(models)}")
    print(f"  Áreas: {len(areas)}")
    print(f"  Base de datos: data/inventory.db")


if __name__ == "__main__":
    # Generar entre 500 y 2000 nodos (por defecto 1000)
    import sys
    num_nodes = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    generate_synthetic_data(num_nodes)


