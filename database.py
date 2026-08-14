"""
Módulo de Base de Datos para el Sistema de Inventario
Maneja la creación y operaciones de la base de datos SQLite
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple


class InventoryDB:
    """Clase para manejar la base de datos de inventario"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        """Inicializa la conexión a la base de datos"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging para mejor concurrencia
        return conn
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de nodos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                serial TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                area TEXT NOT NULL,
                rack INTEGER NOT NULL,
                slot INTEGER NOT NULL,
                last_update TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
        """)
        
        # Tabla de órdenes de trabajo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workorders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal',
                created_at TEXT NOT NULL,
                assigned_to TEXT,
                completed_at TEXT,
                result TEXT,
                FOREIGN KEY (serial) REFERENCES nodes(serial)
            )
        """)
        
        # Tabla de historial de movimientos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movement_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial TEXT NOT NULL,
                old_area TEXT,
                old_rack INTEGER,
                old_slot INTEGER,
                new_area TEXT NOT NULL,
                new_rack INTEGER NOT NULL,
                new_slot INTEGER NOT NULL,
                moved_at TEXT NOT NULL,
                moved_by TEXT,
                reason TEXT,
                FOREIGN KEY (serial) REFERENCES nodes(serial)
            )
        """)
        
        # Índices para mejorar el rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model ON nodes(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_area ON nodes(area)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_serial_wo ON workorders(serial)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_serial_mov ON movement_history(serial)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_moved_at ON movement_history(moved_at)")
        
        conn.commit()
        conn.close()
    
    def add_node(self, serial: str, model: str, area: str, rack: int, slot: int, status: str = 'active'):
        """Añade un nodo a la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO nodes (serial, model, area, rack, slot, last_update, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (serial, model, area, rack, slot, datetime.now().isoformat(), status))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_location(self, serial: str) -> Optional[Dict]:
        """Obtiene la ubicación de un nodo por su número de serie"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT serial, model, area, rack, slot, last_update, status
            FROM nodes
            WHERE serial = ?
        """, (serial,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'serial': row[0],
                'model': row[1],
                'area': row[2],
                'rack': row[3],
                'slot': row[4],
                'last_update': row[5],
                'status': row[6]
            }
        return None
    
    def update_location(self, serial: str, area: str = None, rack: int = None, slot: int = None, 
                       moved_by: str = None, reason: str = None):
        """Actualiza la ubicación de un nodo y registra en historial"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Obtener ubicación actual antes de actualizar
        cursor.execute("SELECT area, rack, slot FROM nodes WHERE serial = ?", (serial,))
        old_location = cursor.fetchone()
        old_area, old_rack, old_slot = old_location if old_location else (None, None, None)
        
        updates = []
        params = []
        
        if area is not None:
            updates.append("area = ?")
            params.append(area)
        if rack is not None:
            updates.append("rack = ?")
            params.append(rack)
        if slot is not None:
            updates.append("slot = ?")
            params.append(slot)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("last_update = ?")
        params.append(datetime.now().isoformat())
        params.append(serial)
        
        cursor.execute(f"""
            UPDATE nodes
            SET {', '.join(updates)}
            WHERE serial = ?
        """, params)
        
        # Registrar en historial de movimientos
        if old_location and (old_area != area or old_rack != rack or old_slot != slot):
            new_area = area if area is not None else old_area
            new_rack = rack if rack is not None else old_rack
            new_slot = slot if slot is not None else old_slot
            
            cursor.execute("""
                INSERT INTO movement_history 
                (serial, old_area, old_rack, old_slot, new_area, new_rack, new_slot, moved_at, moved_by, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (serial, old_area, old_rack, old_slot, new_area, new_rack, new_slot, 
                  datetime.now().isoformat(), moved_by, reason))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def get_movement_history(self, serial: str = None, limit: int = 100) -> List[Dict]:
        """Obtiene el historial de movimientos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if serial:
            cursor.execute("""
                SELECT id, serial, old_area, old_rack, old_slot, new_area, new_rack, new_slot, 
                       moved_at, moved_by, reason
                FROM movement_history
                WHERE serial = ?
                ORDER BY moved_at DESC
                LIMIT ?
            """, (serial, limit))
        else:
            cursor.execute("""
                SELECT id, serial, old_area, old_rack, old_slot, new_area, new_rack, new_slot, 
                       moved_at, moved_by, reason
                FROM movement_history
                ORDER BY moved_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'serial': row[1],
            'old_area': row[2],
            'old_rack': row[3],
            'old_slot': row[4],
            'new_area': row[5],
            'new_rack': row[6],
            'new_slot': row[7],
            'moved_at': row[8],
            'moved_by': row[9],
            'reason': row[10]
        } for row in rows]
    
    def list_by_model(self, model: str) -> List[Dict]:
        """Lista todos los nodos de un modelo específico"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT serial, model, area, rack, slot, last_update, status
            FROM nodes
            WHERE model = ?
            ORDER BY area, rack, slot
        """, (model,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'serial': row[0],
            'model': row[1],
            'area': row[2],
            'rack': row[3],
            'slot': row[4],
            'last_update': row[5],
            'status': row[6]
        } for row in rows]
    
    def list_by_area(self, area: str) -> List[Dict]:
        """Lista todos los nodos de un área específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT serial, model, area, rack, slot, last_update, status
            FROM nodes
            WHERE area = ?
            ORDER BY rack, slot
        """, (area,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'serial': row[0],
            'model': row[1],
            'area': row[2],
            'rack': row[3],
            'slot': row[4],
            'last_update': row[5],
            'status': row[6]
        } for row in rows]
    
    def create_workorder(self, serial: str, priority: str = 'normal', assigned_to: str = None) -> int:
        """Crea una nueva orden de trabajo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workorders (serial, priority, created_at, assigned_to)
            VALUES (?, ?, ?, ?)
        """, (serial, priority, datetime.now().isoformat(), assigned_to))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def complete_workorder(self, order_id: int, result: str):
        """Marca una orden de trabajo como completada"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workorders
            SET completed_at = ?, result = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), result, order_id))
        
        conn.commit()
        conn.close()
    
    def get_all_nodes(self) -> List[Dict]:
        """Obtiene todos los nodos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT serial, model, area, rack, slot, last_update, status
            FROM nodes
            ORDER BY area, rack, slot
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'serial': row[0],
            'model': row[1],
            'area': row[2],
            'rack': row[3],
            'slot': row[4],
            'last_update': row[5],
            'status': row[6]
        } for row in rows]

