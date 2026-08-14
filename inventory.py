"""
Módulo de Lógica del Sistema de Inventario
API interno para manipular datos del inventario
"""
from database import InventoryDB
from typing import Optional, Dict, List
import random


class InventorySystem:
    """Sistema de gestión de inventario"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        """Inicializa el sistema de inventario"""
        self.db = InventoryDB(db_path)
    
    def get_location(self, serial: str) -> Optional[Dict]:
        """
        Consulta la ubicación de un nodo por número de serie
        
        Args:
            serial: Número de serie del nodo
            
        Returns:
            Diccionario con la información del nodo o None si no existe
        """
        return self.db.get_location(serial)
    
    def update_location(self, serial: str, area: str = None, rack: int = None, slot: int = None, 
                       moved_by: str = None, reason: str = None) -> bool:
        """
        Actualiza la ubicación de un nodo
        
        Args:
            serial: Número de serie del nodo
            area: Nueva área (opcional)
            rack: Nuevo rack (opcional)
            slot: Nuevo slot (opcional)
            moved_by: Usuario que realiza el movimiento (opcional)
            reason: Razón del movimiento (opcional)
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        return self.db.update_location(serial, area, rack, slot, moved_by, reason)
    
    def get_movement_history(self, serial: str = None, limit: int = 100) -> List[Dict]:
        """
        Obtiene el historial de movimientos
        
        Args:
            serial: Número de serie del nodo (opcional, si es None obtiene todos)
            limit: Límite de registros a retornar
            
        Returns:
            Lista de diccionarios con información de movimientos
        """
        return self.db.get_movement_history(serial, limit)
    
    def report_misplacement(self, serial: str, correct_area: str = None, 
                           correct_rack: int = None, correct_slot: int = None) -> bool:
        """
        Reporta un nodo mal ubicado y lo corrige
        
        Args:
            serial: Número de serie del nodo
            correct_area: Área correcta (opcional)
            correct_rack: Rack correcto (opcional)
            correct_slot: Slot correcto (opcional)
            
        Returns:
            True si el reporte fue exitoso, False en caso contrario
        """
        # Si no se proporciona la ubicación correcta, se marca como mal ubicado
        if correct_area is None and correct_rack is None and correct_slot is None:
            # Solo actualizamos el estado
            return self.db.update_location(serial)
        else:
            # Corregimos la ubicación
            return self.db.update_location(serial, correct_area, correct_rack, correct_slot)
    
    def list_by_model(self, model: str) -> List[Dict]:
        """
        Lista todos los nodos de un modelo específico
        
        Args:
            model: Modelo a buscar
            
        Returns:
            Lista de diccionarios con información de los nodos
        """
        return self.db.list_by_model(model)
    
    def list_by_area(self, area: str) -> List[Dict]:
        """
        Lista todos los nodos de un área específica
        
        Args:
            area: Área a buscar
            
        Returns:
            Lista de diccionarios con información de los nodos
        """
        return self.db.list_by_area(area)
    
    def filter_nodes(self, model: str = None, area: str = None) -> List[Dict]:
        """
        Filtra nodos por modelo y/o área
        
        Args:
            model: Modelo a filtrar (opcional)
            area: Área a filtrar (opcional)
            
        Returns:
            Lista de nodos que cumplen los criterios
        """
        if model and area:
            # Filtro combinado
            all_nodes = self.db.get_all_nodes()
            return [node for node in all_nodes if node['model'] == model and node['area'] == area]
        elif model:
            return self.list_by_model(model)
        elif area:
            return self.list_by_area(area)
        else:
            return self.db.get_all_nodes()
    
    def create_workorder(self, serial: str, priority: str = 'normal', assigned_to: str = None) -> int:
        """
        Crea una orden de trabajo para un nodo
        
        Args:
            serial: Número de serie del nodo
            priority: Prioridad de la orden (normal, high, urgent)
            assigned_to: Técnico asignado (opcional)
            
        Returns:
            ID de la orden de trabajo creada
        """
        return self.db.create_workorder(serial, priority, assigned_to)
    
    def get_all_models(self) -> List[str]:
        """Obtiene lista de todos los modelos únicos"""
        nodes = self.db.get_all_nodes()
        models = set(node['model'] for node in nodes)
        return sorted(list(models))
    
    def get_all_areas(self) -> List[str]:
        """Obtiene lista de todas las áreas únicas"""
        nodes = self.db.get_all_nodes()
        areas = set(node['area'] for node in nodes)
        return sorted(list(areas))


