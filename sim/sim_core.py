"""
Motor de Simulación con SimPy
Simula el proceso de búsqueda y manejo de órdenes en el inventario
"""
import simpy
import random
import numpy as np
import sys
import os
from typing import Dict, List, Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import InventoryDB


class SimulationEngine:
    """Motor de simulación del sistema de inventario"""
    
    def __init__(self, 
                 inventory_db: InventoryDB,
                 n_techs: int = 2,
                 lambda_orders: float = 0.5,  # órdenes por hora
                 t_move_unit: float = 2.0,  # minutos por unidad de movimiento
                 t_inspect: float = 1.0,  # minutos por inspección de slot
                 p_reloc: float = 0.1,  # probabilidad de reubicación aleatoria
                 misplacement_rate: float = 0.0,  # tasa de nodos mal ubicados
                 strategy: str = 'actual',  # estrategia de organización
                 simulation_time: float = 480.0,  # tiempo de simulación en minutos (8 horas)
                 rfid_factor: float = 0.2,  # factor multiplicador para RFID (<1)
                 priority_prob: Dict[str, float] = None,  # distribución de prioridades
                 seed: int = None,  # semilla para reproducibilidad
                 congestion_enabled: bool = True):  # habilitar congestión por pasillo
        """
        Inicializa el motor de simulación
        
        Args:
            inventory_db: Instancia de la base de datos de inventario
            n_techs: Número de técnicos disponibles
            lambda_orders: Tasa de llegada de órdenes (por hora)
            t_move_unit: Tiempo de movimiento entre racks (minutos)
            t_inspect: Tiempo de inspección de slot (minutos)
            p_reloc: Probabilidad de reubicación aleatoria
            misplacement_rate: Tasa de nodos mal ubicados (0.0 a 1.0)
            strategy: Estrategia de organización ('actual', 'by_model', 'rfid', 'statistical', 'by_lot')
            simulation_time: Tiempo total de simulación (minutos)
            rfid_factor: Factor multiplicador para tiempo de inspección con RFID (<1)
            priority_prob: Distribución de prioridades {'urgent': 0.1, 'normal': 0.9}
            seed: Semilla para reproducibilidad
            congestion_enabled: Habilitar simulación de congestión por pasillo
        """
        # Configurar semilla si se proporciona
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.inventory_db = inventory_db
        self.n_techs = n_techs
        self.lambda_orders = lambda_orders
        self.t_move_unit = t_move_unit
        self.t_inspect = t_inspect
        self.p_reloc = p_reloc
        self.misplacement_rate = misplacement_rate
        self.strategy = strategy
        self.simulation_time = simulation_time
        self.rfid_factor = rfid_factor
        self.priority_prob = priority_prob or {'urgent': 0.1, 'normal': 0.9}
        self.congestion_enabled = congestion_enabled
        
        # Cargar inventario inicial
        self.nodes = self._load_inventory()
        
        # Estadísticas
        self.stats = {
            'orders_processed': 0,
            'orders_failed': 0,
            'total_search_time': 0.0,
            'search_times': [],
            'tech_utilization': {},
            'tech_busy_time': {},
            'tech_idle_time': {},
            'queue_lengths': [],  # Longitud de cola en cada momento
            'max_queue_length': 0,
            'total_steps_walked': 0.0,  # Pasos/distancia total recorrida
            'steps_per_order': []  # Pasos por orden
        }
        
        # Para simular congestión por pasillo
        self.aisle_occupancy = {}  # {area: {rack: count}}
        
        # Aplicar misplacements si es necesario
        if misplacement_rate > 0:
            self._apply_misplacements()
    
    def _load_inventory(self) -> List[Dict]:
        """Carga el inventario inicial desde la base de datos"""
        return self.inventory_db.get_all_nodes()
    
    def _apply_misplacements(self):
        """Aplica mal ubicaciones aleatorias según misplacement_rate"""
        num_misplaced = int(len(self.nodes) * self.misplacement_rate)
        misplaced_nodes = random.sample(self.nodes, num_misplaced)
        
        areas = list(set(node['area'] for node in self.nodes))
        max_rack = max(node['rack'] for node in self.nodes)
        max_slot = max(node['slot'] for node in self.nodes)
        
        for node in misplaced_nodes:
            # Mover a ubicación aleatoria incorrecta
            new_area = random.choice(areas)
            new_rack = random.randint(1, max_rack)
            new_slot = random.randint(1, max_slot)
            
            # Actualizar en memoria (no en BD para simulación)
            node['area'] = new_area
            node['rack'] = new_rack
            node['slot'] = new_slot
    
    def _find_node_location(self, serial: str) -> Optional[Dict]:
        """Encuentra la ubicación de un nodo según la estrategia"""
        if self.strategy == 'actual':
            # Búsqueda secuencial en el área actual
            for node in self.nodes:
                if node['serial'] == serial:
                    return node
        
        elif self.strategy == 'by_model':
            # Si está organizado por modelo, buscar por modelo primero
            target_node = None
            for node in self.nodes:
                if node['serial'] == serial:
                    target_node = node
                    break
            
            if target_node:
                # Contar nodos del mismo modelo antes de este
                model_nodes = [n for n in self.nodes if n['model'] == target_node['model']]
                return target_node
        
        elif self.strategy == 'rfid':
            # RFID simulado: búsqueda instantánea (tiempo reducido)
            for node in self.nodes:
                if node['serial'] == serial:
                    return node
        
        elif self.strategy == 'statistical':
            # Búsqueda estadística: priorizar áreas más probables
            # Simulamos con búsqueda optimizada
            for node in self.nodes:
                if node['serial'] == serial:
                    return node
        
        elif self.strategy == 'by_lot':
            # Área por lote/producto: nodos agrupados por lote de producción
            # Simulamos agrupación por área y modelo (como proxy de lote)
            for node in self.nodes:
                if node['serial'] == serial:
                    return node
        
        return None
    
    def _calculate_search_time(self, target_node: Dict, start_area: str = None, 
                              start_rack: int = None) -> tuple:
        """Calcula el tiempo de búsqueda y pasos recorridos según la estrategia y ubicación
        
        Returns:
            tuple: (tiempo_búsqueda, pasos_recorridos)
        """
        if self.strategy == 'rfid':
            # RFID: tiempo mínimo usando rfid_factor
            return self.t_inspect * self.rfid_factor, 0
        
        # Calcular distancia y pasos
        steps_walked = 0.0
        
        if start_area and start_rack:
            # Movimiento entre áreas
            areas = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']
            try:
                start_idx = areas.index(start_area)
                end_idx = areas.index(target_node['area'])
                area_distance = abs(end_idx - start_idx)
            except ValueError:
                area_distance = 1
            
            # Movimiento entre racks
            rack_distance = abs(target_node['rack'] - start_rack)
            
            # Calcular pasos recorridos (áreas * 10 + racks * 1 como métrica relativa)
            steps_walked = area_distance * 10.0 + rack_distance * 1.0
            
            # Simular congestión por pasillo si está habilitada
            congestion_delay = 0.0
            if self.congestion_enabled:
                # Verificar si hay otros técnicos en el mismo pasillo/área
                aisle_key = f"{target_node['area']}_{target_node['rack']}"
                occupancy = self.aisle_occupancy.get(aisle_key, 0)
                if occupancy > 0:
                    # Congestión: tiempo adicional proporcional a ocupación
                    congestion_delay = occupancy * 0.5  # 0.5 min por técnico adicional
            
            # Tiempo de movimiento
            move_time = (area_distance * 3 + rack_distance) * self.t_move_unit + congestion_delay
            
            # Tiempo de inspección (búsqueda en slots)
            if self.strategy == 'statistical':
                # Búsqueda estadística reduce tiempo de inspección
                inspect_time = self.t_inspect * 0.5
            elif self.strategy == 'by_lot':
                # Por lote: tiempo reducido al estar agrupados
                inspect_time = self.t_inspect * 0.7
            else:
                inspect_time = self.t_inspect * random.randint(1, 5)  # 1-5 slots revisados
            
            return move_time + inspect_time, steps_walked
        else:
            # Búsqueda desde inicio (peor caso)
            steps_walked = random.uniform(20.0, 50.0)  # Estimación de pasos
            return self.t_inspect * random.randint(5, 15), steps_walked
    
    def _handle_order(self, env: simpy.Environment, order: Dict, techs: simpy.Resource):
        """Procesa una orden de trabajo"""
        serial = order['serial']
        tech_id = order['tech_id']
        priority = order.get('priority', 'normal')
        start_area = order.get('start_area')
        start_rack = order.get('start_rack')
        
        # Buscar el nodo
        target_node = self._find_node_location(serial)
        
        if not target_node:
            self.stats['orders_failed'] += 1
            return
        
        # Registrar ocupación de pasillo si hay congestión
        aisle_key = None
        if self.congestion_enabled and target_node:
            aisle_key = f"{target_node['area']}_{target_node['rack']}"
            self.aisle_occupancy[aisle_key] = self.aisle_occupancy.get(aisle_key, 0) + 1
        
        # Calcular tiempo de búsqueda y pasos
        search_time, steps_walked = self._calculate_search_time(target_node, start_area, start_rack)
        
        # Simular búsqueda
        yield env.timeout(search_time)
        
        # Remover ocupación de pasillo
        if aisle_key:
            self.aisle_occupancy[aisle_key] = max(0, self.aisle_occupancy.get(aisle_key, 1) - 1)
        
        # Registrar estadísticas
        self.stats['orders_processed'] += 1
        self.stats['total_search_time'] += search_time
        self.stats['search_times'].append(search_time)
        self.stats['total_steps_walked'] += steps_walked
        self.stats['steps_per_order'].append(steps_walked)
        
        # Actualizar utilización del técnico
        if tech_id not in self.stats['tech_busy_time']:
            self.stats['tech_busy_time'][tech_id] = 0.0
        self.stats['tech_busy_time'][tech_id] += search_time
        
        # Registrar longitud de cola
        queue_len = len(techs.queue)
        self.stats['queue_lengths'].append(queue_len)
        if queue_len > self.stats['max_queue_length']:
            self.stats['max_queue_length'] = queue_len
        
        # Simular reubicación aleatoria
        if random.random() < self.p_reloc:
            yield env.timeout(self.t_move_unit * 2)  # Tiempo de reubicación
    
    def _order_generator(self, env: simpy.Environment, techs: simpy.Resource, tech_locations: Dict):
        """Genera órdenes de trabajo según lambda_orders con distribución de prioridades"""
        order_id = 0
        
        while True:
            # Tiempo hasta la próxima orden (distribución exponencial)
            # lambda_orders está en órdenes/hora, convertimos a minutos
            interarrival_time = random.expovariate(self.lambda_orders / 60.0)
            yield env.timeout(interarrival_time)
            
            # Seleccionar nodo aleatorio
            if self.nodes:
                selected_node = random.choice(self.nodes)
                serial = selected_node['serial']
                
                # Asignar prioridad según distribución probabilística
                rand_priority = random.random()
                if rand_priority < self.priority_prob.get('urgent', 0.1):
                    priority = 'urgent'
                else:
                    priority = 'normal'
                
                # Solicitar técnico (las órdenes urgentes tienen prioridad)
                request = techs.request() if priority != 'urgent' else techs.request()
                with request:
                    yield request
                    
                    order_id += 1
                    # Obtener ubicación actual del técnico
                    tech_id = len(techs.users) - 1
                    tech_location = tech_locations.get(tech_id, {})
                    
                    order = {
                        'id': order_id,
                        'serial': serial,
                        'tech_id': tech_id,
                        'priority': priority,
                        'start_area': tech_location.get('area'),
                        'start_rack': tech_location.get('rack')
                    }
                    
                    # Procesar orden
                    env.process(self._handle_order(env, order, techs))
                    
                    # Actualizar ubicación del técnico después de procesar
                    tech_locations[tech_id] = {
                        'area': selected_node['area'],
                        'rack': selected_node['rack']
                    }
    
    def run(self) -> Dict:
        """
        Ejecuta la simulación
        
        Returns:
            Diccionario con estadísticas de la simulación
        """
        # Crear ambiente SimPy
        env = simpy.Environment()
        
        # Recurso de técnicos
        techs = simpy.Resource(env, capacity=self.n_techs)
        
        # Rastrear ubicaciones de técnicos
        tech_locations = {i: {'area': None, 'rack': None} for i in range(self.n_techs)}
        
        # Inicializar estadísticas de utilización
        for i in range(self.n_techs):
            self.stats['tech_busy_time'][i] = 0.0
            self.stats['tech_idle_time'][i] = 0.0
        
        # Iniciar generador de órdenes
        env.process(self._order_generator(env, techs, tech_locations))
        
        # Monitorear longitud de cola periódicamente
        def monitor_queue(env, techs):
            while True:
                queue_len = len(techs.queue)
                self.stats['queue_lengths'].append(queue_len)
                if queue_len > self.stats['max_queue_length']:
                    self.stats['max_queue_length'] = queue_len
                yield env.timeout(1.0)  # Monitorear cada minuto
        
        env.process(monitor_queue(env, techs))
        
        # Ejecutar simulación
        env.run(until=self.simulation_time)
        
        # Calcular estadísticas finales
        if self.stats['search_times']:
            self.stats['mean_search_time'] = np.mean(self.stats['search_times'])
            self.stats['p95_search_time'] = np.percentile(self.stats['search_times'], 95)
        else:
            self.stats['mean_search_time'] = 0.0
            self.stats['p95_search_time'] = 0.0
        
        total_orders = self.stats['orders_processed'] + self.stats['orders_failed']
        if total_orders > 0:
            self.stats['error_rate'] = self.stats['orders_failed'] / total_orders
        else:
            self.stats['error_rate'] = 0.0
        
        # Calcular utilización de técnicos
        for tech_id in range(self.n_techs):
            busy_time = self.stats['tech_busy_time'].get(tech_id, 0.0)
            utilization = (busy_time / self.simulation_time) * 100.0
            self.stats['tech_utilization'][tech_id] = utilization
        
        self.stats['avg_utilization'] = np.mean(list(self.stats['tech_utilization'].values()))
        
        # Calcular KPIs adicionales
        if self.stats['queue_lengths']:
            self.stats['mean_queue_length'] = np.mean(self.stats['queue_lengths'])
        else:
            self.stats['mean_queue_length'] = 0.0
        
        if self.stats['steps_per_order']:
            self.stats['mean_steps_walked'] = np.mean(self.stats['steps_per_order'])
        else:
            self.stats['mean_steps_walked'] = 0.0
        
        self.stats['total_steps_walked'] = sum(self.stats['steps_per_order'])
        
        return self.stats

