"""
Módulo de Experimentos
Ejecuta múltiples réplicas (Monte Carlo) para cada escenario de prueba
"""
import os
import sys
import csv
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import InventoryDB
from sim.sim_core import SimulationEngine


def run_experiment(scenario_name: str,
                   n_replicas: int = 10,
                   n_techs: int = 2,
                   lambda_orders: float = 0.5,
                   t_move_unit: float = 2.0,
                   t_inspect: float = 1.0,
                   p_reloc: float = 0.1,
                   misplacement_rate: float = 0.0,
                   strategy: str = 'actual',
                   simulation_time: float = 480.0,
                   rfid_factor: float = 0.2,
                   priority_prob: dict = None,
                   seed: int = None,
                   congestion_enabled: bool = True):
    """
    Ejecuta un experimento con múltiples réplicas
    
    Args:
        scenario_name: Nombre del escenario
        n_replicas: Número de réplicas Monte Carlo
        n_techs: Número de técnicos
        lambda_orders: Tasa de llegada de órdenes (por hora)
        t_move_unit: Tiempo de movimiento entre racks (minutos)
        t_inspect: Tiempo de inspección de slot (minutos)
        p_reloc: Probabilidad de reubicación aleatoria
        misplacement_rate: Tasa de nodos mal ubicados
        strategy: Estrategia de organización
        simulation_time: Tiempo de simulación (minutos)
    
    Returns:
        Lista de resultados de cada réplica
    """
    print(f"\n{'='*60}")
    print(f"Ejecutando experimento: {scenario_name}")
    print(f"Estrategia: {strategy}")
    print(f"Réplicas: {n_replicas}")
    print(f"{'='*60}\n")
    
    results = []
    db = InventoryDB("data/inventory.db")
    
    for replica in range(1, n_replicas + 1):
        print(f"Réplica {replica}/{n_replicas}...", end=" ", flush=True)
        
        # Crear motor de simulación
        # Usar seed diferente para cada réplica si no se especifica
        replica_seed = seed + replica if seed is not None else None
        
        sim_engine = SimulationEngine(
            inventory_db=db,
            n_techs=n_techs,
            lambda_orders=lambda_orders,
            t_move_unit=t_move_unit,
            t_inspect=t_inspect,
            p_reloc=p_reloc,
            misplacement_rate=misplacement_rate,
            strategy=strategy,
            simulation_time=simulation_time,
            rfid_factor=rfid_factor,
            priority_prob=priority_prob,
            seed=replica_seed,
            congestion_enabled=congestion_enabled
        )
        
        # Ejecutar simulación
        stats = sim_engine.run()
        
        # Guardar resultados
        result = {
            'scenario': scenario_name,
            'replica': replica,
            'strategy': strategy,
            'n_techs': n_techs,
            'lambda_orders': lambda_orders,
            'misplacement_rate': misplacement_rate,
            'mean_search_time': stats['mean_search_time'],
            'p95_search_time': stats['p95_search_time'],
            'error_rate': stats['error_rate'],
            'orders_processed': stats['orders_processed'],
            'orders_failed': stats['orders_failed'],
            'avg_utilization': stats['avg_utilization'],
            'total_orders': stats['orders_processed'] + stats['orders_failed'],
            'mean_queue_length': stats.get('mean_queue_length', 0.0),
            'max_queue_length': stats.get('max_queue_length', 0),
            'total_steps_walked': stats.get('total_steps_walked', 0.0),
            'mean_steps_walked': stats.get('mean_steps_walked', 0.0)
        }
        
        results.append(result)
        print(f"✓ (T_mean={result['mean_search_time']:.2f} min)")
    
    return results


def save_results(results: list, filename: str = None):
    """
    Guarda los resultados en un archivo CSV
    
    Args:
        results: Lista de diccionarios con resultados
        filename: Nombre del archivo (opcional)
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/experiment_{timestamp}.csv"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if not results:
        return
    
    fieldnames = list(results[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✓ Resultados guardados en: {filename}")


def run_all_scenarios():
    """Ejecuta todos los escenarios de prueba"""
    all_results = []
    
    # Escenario Baseline
    print("\n" + "="*60)
    print("ESCENARIO 1: BASELINE")
    print("="*60)
    results = run_experiment(
        scenario_name="baseline",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='actual',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/baseline.csv")
    
    # Escenario: Orden por Modelo
    print("\n" + "="*60)
    print("ESCENARIO 2: ORDEN POR MODELO")
    print("="*60)
    results = run_experiment(
        scenario_name="by_model",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='by_model',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/by_model.csv")
    
    # Escenario: RFID Simulado
    print("\n" + "="*60)
    print("ESCENARIO 3: RFID SIMULADO")
    print("="*60)
    results = run_experiment(
        scenario_name="rfid",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='rfid',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/rfid.csv")
    
    # Escenario: Búsqueda Estadística
    print("\n" + "="*60)
    print("ESCENARIO 4: BÚSQUEDA ESTADÍSTICA")
    print("="*60)
    results = run_experiment(
        scenario_name="statistical",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='statistical',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/statistical.csv")
    
    # Escenario: Alta Demanda (lambda x2)
    print("\n" + "="*60)
    print("ESCENARIO 5: ALTA DEMANDA (λ x2)")
    print("="*60)
    results = run_experiment(
        scenario_name="high_demand_2x",
        n_replicas=10,
        n_techs=2,
        lambda_orders=1.0,  # x2
        strategy='actual',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/high_demand_2x.csv")
    
    # Escenario: Alta Demanda (lambda x4)
    print("\n" + "="*60)
    print("ESCENARIO 6: ALTA DEMANDA (λ x4)")
    print("="*60)
    results = run_experiment(
        scenario_name="high_demand_4x",
        n_replicas=10,
        n_techs=2,
        lambda_orders=2.0,  # x4
        strategy='actual',
        misplacement_rate=0.0
    )
    all_results.extend(results)
    save_results(results, "results/high_demand_4x.csv")
    
    # Escenario: Nodos Mal Ubicados (5%)
    print("\n" + "="*60)
    print("ESCENARIO 7: NODOS MAL UBICADOS (5%)")
    print("="*60)
    results = run_experiment(
        scenario_name="misplaced_5pct",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='actual',
        misplacement_rate=0.05
    )
    all_results.extend(results)
    save_results(results, "results/misplaced_5pct.csv")
    
    # Escenario: Nodos Mal Ubicados (10%)
    print("\n" + "="*60)
    print("ESCENARIO 8: NODOS MAL UBICADOS (10%)")
    print("="*60)
    results = run_experiment(
        scenario_name="misplaced_10pct",
        n_replicas=10,
        n_techs=2,
        lambda_orders=0.5,
        strategy='actual',
        misplacement_rate=0.10
    )
    all_results.extend(results)
    save_results(results, "results/misplaced_10pct.csv")
    
    # Guardar todos los resultados combinados
    save_results(all_results, "results/all_experiments.csv")
    
    print("\n" + "="*60)
    print("✓ TODOS LOS EXPERIMENTOS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar experimentos de simulación')
    parser.add_argument('--all', action='store_true', help='Ejecutar todos los escenarios')
    parser.add_argument('--scenario', type=str, help='Ejecutar un escenario específico')
    parser.add_argument('--replicas', type=int, default=10, help='Número de réplicas')
    
    args = parser.parse_args()
    
    if args.all:
        run_all_scenarios()
    elif args.scenario:
        # Ejecutar escenario específico
        scenarios = {
            'baseline': {'strategy': 'actual', 'lambda_orders': 0.5, 'misplacement_rate': 0.0},
            'by_model': {'strategy': 'by_model', 'lambda_orders': 0.5, 'misplacement_rate': 0.0},
            'rfid': {'strategy': 'rfid', 'lambda_orders': 0.5, 'misplacement_rate': 0.0},
            'statistical': {'strategy': 'statistical', 'lambda_orders': 0.5, 'misplacement_rate': 0.0},
        }
        
        if args.scenario in scenarios:
            config = scenarios[args.scenario]
            results = run_experiment(
                scenario_name=args.scenario,
                n_replicas=args.replicas,
                **config
            )
            save_results(results, f"results/{args.scenario}.csv")
        else:
            print(f"Escenario '{args.scenario}' no reconocido")
    else:
        print("Usa --all para ejecutar todos los escenarios o --scenario <nombre> para uno específico")

