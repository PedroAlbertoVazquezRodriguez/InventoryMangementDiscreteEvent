# Sistema de Inventario y Motor de Simulación

Aplicación GUI completa para gestión de inventario y simulación de estrategias de organización.

## Características

### 1. Sistema de Inventario (Prototipo)
- Base de datos SQLite para almacenamiento de nodos y órdenes de trabajo
- Consulta de ubicación por número de serie
- Filtrado por modelo y área
- Actualización de ubicaciones
- Reporte de nodos mal ubicados

### 2. Motor de Simulación
- Simulación con SimPy de procesos de búsqueda
- Múltiples estrategias de organización:
  - **Actual**: Búsqueda secuencial
  - **Por Modelo**: Organización por modelo
  - **RFID Simulado**: Búsqueda optimizada
  - **Estadística**: Búsqueda basada en probabilidades
- Experimentos con réplicas Monte Carlo
- Análisis de KPIs (tiempo medio, percentil 95, tasa de error, utilización)

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Generar datos iniciales (opcional, se genera automáticamente si no existe):
```bash
python generate_data.py 1000
```

## Uso

### Aplicación GUI

Ejecutar la aplicación principal:
```bash
python main.py
```

La aplicación incluye 4 pestañas:
- **Consulta**: Buscar y filtrar nodos del inventario
- **Gestión**: Actualizar ubicaciones y reportar mal ubicaciones
- **Simulación**: Ejecutar simulaciones y experimentos
- **Resultados**: Información sobre análisis de resultados

### Ejecutar Experimentos desde Línea de Comandos

Ejecutar todos los escenarios:
```bash
python experiments/run_experiment.py --all
```

Ejecutar un escenario específico:
```bash
python experiments/run_experiment.py --scenario baseline --replicas 10
```

## Estructura del Proyecto

```
ErardoProto/
├── data/                  # Base de datos SQLite
├── sim/                   # Motor de simulación
│   └── sim_core.py
├── experiments/           # Scripts de experimentos
│   └── run_experiment.py
├── results/               # Resultados CSV
├── notebooks/             # Notebooks de análisis
│   └── analysis.ipynb
├── gui/                   # Interfaz gráfica
│   └── app.py
├── database.py            # Módulo de base de datos
├── inventory.py           # Lógica del sistema
├── generate_data.py       # Generador de datos sintéticos
├── main.py                # Punto de entrada
└── requirements.txt       # Dependencias
```

## Escenarios de Prueba

1. **Baseline**: Distribución actual, 2 técnicos, λ=0.5/h
2. **Orden por Modelo**: Reorganización por modelo
3. **RFID Simulado**: Búsqueda optimizada
4. **Búsqueda Estadística**: Estrategia probabilística
5. **Alta Demanda (λ x2)**: λ=1.0/h
6. **Alta Demanda (λ x4)**: λ=2.0/h
7. **Nodos Mal Ubicados (5%)**: misplacement_rate=0.05
8. **Nodos Mal Ubicados (10%)**: misplacement_rate=0.10

## Análisis de Resultados

Los resultados se guardan en `results/*.csv`. Usa el notebook `notebooks/analysis.ipynb` para:
- Cargar y visualizar resultados
- Comparar estrategias
- Analizar KPIs
- Generar gráficos comparativos

## Parámetros de Simulación

- **n_techs**: Número de técnicos (default: 2)
- **lambda_orders**: Tasa de llegada de órdenes por hora (default: 0.5)
- **t_move_unit**: Tiempo de movimiento entre racks en minutos (default: 2.0)
- **t_inspect**: Tiempo de inspección de slot en minutos (default: 1.0)
- **p_reloc**: Probabilidad de reubicación aleatoria (default: 0.1)
- **misplacement_rate**: Tasa de nodos mal ubicados (default: 0.0)
- **simulation_time**: Tiempo total de simulación en minutos (default: 480)

## Requisitos

- Python 3.8+
- SimPy 4.0+
- CustomTkinter 5.2+
- Pandas, NumPy, Matplotlib, Seaborn

## Autor

Proyecto desarrollado para UANL-FIME


