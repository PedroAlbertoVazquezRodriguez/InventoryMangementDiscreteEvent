"""
Aplicación GUI Principal
Interfaz gráfica moderna y organizada para el Sistema de Inventario y Simulación
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, Menu
import threading
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory import InventorySystem
from sim.sim_core import SimulationEngine
from database import InventoryDB
from experiments.run_experiment import run_experiment, save_results
import pandas as pd
import glob
from datetime import datetime


class InventoryApp(ctk.CTk):
    """Aplicación principal con GUI moderna"""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("Sistema de Inventario y Simulación")
        self.geometry("1600x1000")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Inicializar sistema de inventario
        try:
            self.inventory = InventorySystem()
        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar el sistema:\n{str(e)}")
            self.destroy()
            return
        
        # Crear menú superior
        self.create_menu()
        
        # Crear layout principal
        self.create_main_layout()
        
        # Inicializar dashboard
        self.update_statistics()
        
        # Historial de resultados para comparación
        self.results_history = []
        self.baseline_results = None
    
    def create_menu(self):
        """Crea el menú superior"""
        menubar = Menu(self)
        self.config(menu=menubar)
        
        # Menú Inventario
        inventario_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inventario", menu=inventario_menu)
        inventario_menu.add_command(label="Consultar por Serie", command=lambda: self.show_page("dashboard"))
        inventario_menu.add_command(label="Filtrar por Modelo", command=lambda: self.show_page("inventory"))
        inventario_menu.add_command(label="Filtrar por Área", command=lambda: self.show_page("inventory"))
        inventario_menu.add_separator()
        inventario_menu.add_command(label="Actualizar Ubicación", command=lambda: self.show_page("management"))
        inventario_menu.add_command(label="Reportar Mal Ubicación", command=lambda: self.show_page("management"))
        
        # Menú Simulación
        simulacion_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulación", menu=simulacion_menu)
        simulacion_menu.add_command(label="Ejecutar Simulación", command=lambda: self.show_page("simulation"))
        simulacion_menu.add_command(label="Ejecutar Experimento", command=lambda: self.show_page("simulation"))
        simulacion_menu.add_separator()
        simulacion_menu.add_command(label="Estrategia: Actual", command=lambda: self.set_strategy("actual"))
        simulacion_menu.add_command(label="Estrategia: Por Modelo", command=lambda: self.set_strategy("by_model"))
        simulacion_menu.add_command(label="Estrategia: RFID", command=lambda: self.set_strategy("rfid"))
        simulacion_menu.add_command(label="Estrategia: Estadística", command=lambda: self.set_strategy("statistical"))
        
        # Menú Análisis
        analisis_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Análisis", menu=analisis_menu)
        analisis_menu.add_command(label="Ver Resultados", command=lambda: self.show_page("results"))
        analisis_menu.add_command(label="Abrir Notebook", command=self.open_notebook)
        analisis_menu.add_command(label="Actualizar Estadísticas", command=self.update_statistics)
        
        # Menú Herramientas
        herramientas_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=herramientas_menu)
        herramientas_menu.add_command(label="Generar Datos de Prueba", command=self.generate_test_data)
        herramientas_menu.add_command(label="Exportar Resultados", command=self.export_results)
        
        # Menú Ayuda
        ayuda_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.show_about)
    
    def create_main_layout(self):
        """Crea el layout principal con barra superior y área de contenido"""
        # Container principal
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Barra superior de navegación
        self.create_top_navbar()
        
        # Área de contenido principal
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="#F5F5F5")
        self.content_area.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Páginas de contenido
        self.pages = {}
        self.current_page = None
        
        # Crear todas las páginas
        self.create_dashboard_page()
        self.create_inventory_page()
        self.create_management_page()
        self.create_simulation_page()
        self.create_results_page()
        
        # Mostrar dashboard por defecto
        self.show_page("dashboard")
    
    def create_top_navbar(self):
        """Crea la barra superior de navegación"""
        navbar = ctk.CTkFrame(self.main_container, height=70, corner_radius=0, fg_color="#2C3E50")
        navbar.pack(fill="x", padx=0, pady=0)
        navbar.pack_propagate(False)
        
        # Contenedor interno
        nav_content = ctk.CTkFrame(navbar, fg_color="transparent")
        nav_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Logo/Título a la izquierda
        title_frame = ctk.CTkFrame(nav_content, fg_color="transparent")
        title_frame.pack(side="left", padx=(0, 30))
        
        title = ctk.CTkLabel(title_frame, text="Sistema de Inventario y Simulación", 
                            font=ctk.CTkFont(size=18, weight="bold"),
                            text_color="white")
        title.pack(side="left")
        
        # Botones de navegación en el centro
        nav_buttons_frame = ctk.CTkFrame(nav_content, fg_color="transparent")
        nav_buttons_frame.pack(side="left", fill="x", expand=True, padx=20)
        
        self.nav_buttons = {}
        
        nav_items = [
            ("Dashboard", "dashboard", "#3498DB"),
            ("Consulta", "inventory", "#2ECC71"),
            ("Gestión", "management", "#E67E22"),
            ("Simulación", "simulation", "#9B59B6"),
            ("Resultados", "results", "#E74C3C")
        ]
        
        for text, page_id, color in nav_items:
            btn = ctk.CTkButton(nav_buttons_frame, 
                               text=text,
                               command=lambda p=page_id: self.show_page(p),
                               height=45,
                               width=140,
                               font=ctk.CTkFont(size=13, weight="bold"),
                               fg_color=color,
                               hover_color=self.darken_color(color),
                               corner_radius=8,
                               text_color="white")
            btn.pack(side="left", padx=8)
            self.nav_buttons[page_id] = btn
        
        # Información del sistema a la derecha
        info_frame = ctk.CTkFrame(nav_content, fg_color="transparent")
        info_frame.pack(side="right", padx=(20, 0))
        
        self.status_label = ctk.CTkLabel(info_frame, 
                                        text="Sistema Operativo",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#BDC3C7")
        self.status_label.pack(side="right")
    
    def darken_color(self, hex_color):
        """Oscurece un color hexadecimal"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def show_page(self, page_id):
        """Muestra una página específica"""
        # Ocultar página actual
        if self.current_page:
            self.pages[self.current_page].pack_forget()
        
        # Mostrar nueva página
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True, padx=20, pady=20)
            self.current_page = page_id
            
            # Actualizar botones de navegación
            colors = {
                "dashboard": "#3498DB",
                "inventory": "#2ECC71",
                "management": "#E67E22",
                "simulation": "#9B59B6",
                "results": "#E74C3C"
            }
            
            for btn_id, btn in self.nav_buttons.items():
                if btn_id == page_id:
                    # Botón activo: más oscuro y con borde
                    btn.configure(fg_color=self.darken_color(colors[btn_id]),
                                 border_width=2,
                                 border_color="white")
                else:
                    # Botón inactivo: color normal sin borde
                    btn.configure(fg_color=colors.get(btn_id, "#3498DB"),
                                 border_width=0)
    
    def create_dashboard_page(self):
        """Crea la página del dashboard"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages["dashboard"] = page
        
        # Header
        header = ctk.CTkFrame(page, fg_color="white", corner_radius=15, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        title = ctk.CTkLabel(header_content, text="Panel de Control", 
                            font=ctk.CTkFont(size=32, weight="bold"))
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(header_content, text="Actualizar", 
                                   command=self.update_statistics,
                                   width=120, height=35)
        refresh_btn.pack(side="right")
        
        # Tarjetas de estadísticas
        stats_container = ctk.CTkFrame(page, fg_color="transparent")
        stats_container.pack(fill="x", pady=(0, 20))
        
        # Obtener estadísticas
        try:
            all_nodes = self.inventory.db.get_all_nodes()
            total_nodes = len(all_nodes)
            models = set(n['model'] for n in all_nodes)
            areas = set(n['area'] for n in all_nodes)
            active_nodes = len([n for n in all_nodes if n['status'] == 'active'])
        except:
            total_nodes = 0
            models = set()
            areas = set()
            active_nodes = 0
        
        # Crear tarjetas
        cards_data = [
            ("Total de Nodos", total_nodes, "#3498DB"),
            ("Modelos", len(models), "#2ECC71"),
            ("Áreas", len(areas), "#E67E22"),
            ("Activos", active_nodes, "#9B59B6")
        ]
        
        self.stats_labels = {}
        for i, (label, value, color) in enumerate(cards_data):
            card = ctk.CTkFrame(stats_container, fg_color="white", corner_radius=15)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            stats_container.grid_columnconfigure(i, weight=1)
            
            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(fill="both", expand=True, padx=25, pady=20)
            
            ctk.CTkLabel(card_content, text=label, 
                        font=ctk.CTkFont(size=14),
                        text_color="gray").pack(anchor="w")
            
            value_label = ctk.CTkLabel(card_content, text=str(value), 
                                      font=ctk.CTkFont(size=42, weight="bold"),
                                      text_color=color)
            value_label.pack(anchor="w", pady=(10, 0))
            self.stats_labels[label] = value_label
        
        # Gráficos en dos columnas
        charts_container = ctk.CTkFrame(page, fg_color="transparent")
        charts_container.pack(fill="both", expand=True, pady=20)
        
        # Gráfico de modelos
        chart1_frame = ctk.CTkFrame(charts_container, fg_color="white", corner_radius=15)
        chart1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(chart1_frame, text="Distribución por Modelo", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        self.model_chart_container = ctk.CTkFrame(chart1_frame, fg_color="transparent")
        self.model_chart_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.create_model_chart()
        
        # Gráfico de áreas
        chart2_frame = ctk.CTkFrame(charts_container, fg_color="white", corner_radius=15)
        chart2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(chart2_frame, text="Distribución por Área", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        self.area_chart_container = ctk.CTkFrame(chart2_frame, fg_color="transparent")
        self.area_chart_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.create_area_chart()
        
        # Heatmap de áreas/racks
        heatmap_frame = ctk.CTkFrame(charts_container, fg_color="white", corner_radius=15)
        heatmap_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(heatmap_frame, text="Heatmap de Densidad por Área/Rack", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        self.heatmap_container = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
        self.heatmap_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.create_heatmap()
        
        charts_container.grid_columnconfigure(0, weight=1)
        charts_container.grid_columnconfigure(1, weight=1)
    
    def create_model_chart(self):
        """Crea gráfico de barras de modelos"""
        try:
            all_nodes = self.inventory.db.get_all_nodes()
            from collections import Counter
            model_counts = Counter(n['model'] for n in all_nodes)
            
            models = list(model_counts.keys())[:8]
            counts = [model_counts[m] for m in models]
            
            fig, ax = plt.subplots(figsize=(8, 4), facecolor='white')
            bars = ax.barh(models, counts, color=['#3498DB', '#2ECC71', '#E67E22', '#9B59B6', '#E74C3C', '#1ABC9C', '#F39C12', '#34495E'])
            ax.set_xlabel('Cantidad', fontsize=11, color='#555')
            ax.set_title('Top 8 Modelos', fontsize=13, fontweight='bold', color='#2C3E50', pad=10)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            ax.tick_params(colors='#555', labelsize=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E0E0E0')
            ax.spines['bottom'].set_color('#E0E0E0')
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.model_chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(self.model_chart_container, text=f"Error: {e}").pack()
    
    def create_area_chart(self):
        """Crea gráfico de pastel de áreas"""
        try:
            all_nodes = self.inventory.db.get_all_nodes()
            from collections import Counter
            area_counts = Counter(n['area'] for n in all_nodes)
            
            areas = list(area_counts.keys())
            counts = [area_counts[a] for a in areas]
            
            fig, ax = plt.subplots(figsize=(7, 6), facecolor='white')
            colors = ['#3498DB', '#2ECC71', '#E67E22', '#9B59B6', '#E74C3C', '#1ABC9C', '#F39C12', '#34495E']
            ax.pie(counts, labels=areas, autopct='%1.1f%%', colors=colors[:len(areas)], 
                  startangle=90, textprops={'fontsize': 10, 'color': '#555'})
            ax.set_title('Distribución por Área', fontsize=13, fontweight='bold', color='#2C3E50', pad=15)
            fig.patch.set_facecolor('white')
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.area_chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            ctk.CTkLabel(self.area_chart_container, text=f"Error: {e}").pack()
    
    def create_heatmap(self):
        """Crea un heatmap de densidad por área/rack"""
        try:
            import seaborn as sns
            all_nodes = self.inventory.db.get_all_nodes()
            
            if not all_nodes:
                ctk.CTkLabel(self.heatmap_container, text="No hay datos para mostrar").pack()
                return
            
            # Crear matriz de densidad área x rack
            area_rack_data = {}
            for node in all_nodes:
                area = node['area']
                rack = node['rack']
                key = (area, rack)
                area_rack_data[key] = area_rack_data.get(key, 0) + 1
            
            # Obtener todas las áreas y racks únicos
            areas = sorted(set(n['area'] for n in all_nodes))
            racks = sorted(set(n['rack'] for n in all_nodes))
            
            # Crear matriz
            matrix = []
            for area in areas:
                row = []
                for rack in racks:
                    count = area_rack_data.get((area, rack), 0)
                    row.append(count)
                matrix.append(row)
            
            # Crear heatmap
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
            sns.heatmap(matrix, annot=True, fmt='d', cmap='YlOrRd', 
                       xticklabels=racks, yticklabels=areas,
                       cbar_kws={'label': 'Número de Nodos'}, ax=ax,
                       linewidths=0.5, linecolor='gray')
            ax.set_xlabel('Rack', fontsize=12, color='#555')
            ax.set_ylabel('Área', fontsize=12, color='#555')
            ax.set_title('Densidad de Nodos por Área y Rack', 
                        fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
            ax.tick_params(colors='#555', labelsize=9)
            fig.patch.set_facecolor('white')
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.heatmap_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except ImportError:
            ctk.CTkLabel(self.heatmap_container, 
                       text="Seaborn no disponible. Instale con: pip install seaborn").pack()
        except Exception as e:
            ctk.CTkLabel(self.heatmap_container, text=f"Error: {e}").pack()
    
    def create_inventory_page(self):
        """Crea la página de consulta de inventario"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages["inventory"] = page
        
        # Header
        header = ctk.CTkFrame(page, fg_color="white", corner_radius=15, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(header_content, text="Consulta de Inventario", 
                    font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Panel de búsqueda
        search_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        search_panel.pack(fill="x", pady=(0, 20))
        
        search_content = ctk.CTkFrame(search_panel, fg_color="transparent")
        search_content.pack(fill="x", padx=25, pady=25)
        
        ctk.CTkLabel(search_content, text="Búsqueda por Número de Serie", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        search_row = ctk.CTkFrame(search_content, fg_color="transparent")
        search_row.pack(fill="x")
        
        self.serial_entry = ctk.CTkEntry(search_row, width=400, height=45,
                                         placeholder_text="Ingrese el número de serie...",
                                         font=ctk.CTkFont(size=14))
        self.serial_entry.pack(side="left", padx=(0, 15))
        self.serial_entry.bind("<Return>", lambda e: self.search_by_serial())
        
        ctk.CTkButton(search_row, text="Buscar", 
                     command=self.search_by_serial,
                     height=45, width=120,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#3498DB").pack(side="left")
        
        # Panel de filtros
        filter_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        filter_panel.pack(fill="x", pady=(0, 20))
        
        filter_content = ctk.CTkFrame(filter_panel, fg_color="transparent")
        filter_content.pack(fill="x", padx=25, pady=25)
        
        ctk.CTkLabel(filter_content, text="Filtros de Búsqueda", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        filter_row = ctk.CTkFrame(filter_content, fg_color="transparent")
        filter_row.pack(fill="x")
        
        ctk.CTkLabel(filter_row, text="Modelo:", 
                    font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        try:
            models = ["Todos"] + self.inventory.get_all_models()
        except:
            models = ["Todos"]
        self.model_filter = ctk.CTkComboBox(filter_row, width=200, height=40, values=models)
        self.model_filter.set("Todos")
        self.model_filter.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(filter_row, text="Área:", 
                    font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        try:
            areas = ["Todas"] + self.inventory.get_all_areas()
        except:
            areas = ["Todas"]
        self.area_filter = ctk.CTkComboBox(filter_row, width=150, height=40, values=areas)
        self.area_filter.set("Todas")
        self.area_filter.pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(filter_row, text="Aplicar Filtros", 
                     command=self.filter_nodes,
                     height=40, width=150,
                     font=ctk.CTkFont(size=14),
                     fg_color="#2ECC71").pack(side="left")
        
        # Panel de resultados
        results_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        results_panel.pack(fill="both", expand=True)
        
        results_header = ctk.CTkFrame(results_panel, fg_color="transparent")
        results_header.pack(fill="x", padx=25, pady=(25, 15))
        
        ctk.CTkLabel(results_header, text="Resultados", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.results_count_label = ctk.CTkLabel(results_header, text="0 nodos encontrados", 
                                               font=ctk.CTkFont(size=12), text_color="gray")
        self.results_count_label.pack(side="right")
        
        # Treeview
        tree_container = ctk.CTkFrame(results_panel)
        tree_container.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        scrollbar = ctk.CTkScrollbar(tree_container)
        scrollbar.pack(side="right", fill="y")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="black", 
                       fieldbackground="white", rowheight=35, font=('Arial', 11))
        style.configure("Treeview.Heading", background="#3498DB", foreground="white", 
                       font=('Arial', 12, 'bold'))
        style.map("Treeview", background=[("selected", "#3498DB")])
        
        self.tree = ttk.Treeview(tree_container, columns=("Serial", "Modelo", "Área", "Rack", "Slot", "Estado"),
                                show="headings", yscrollcommand=scrollbar.set, height=18)
        
        self.tree.heading("Serial", text="Número de Serie")
        self.tree.heading("Modelo", text="Modelo")
        self.tree.heading("Área", text="Área")
        self.tree.heading("Rack", text="Rack")
        self.tree.heading("Slot", text="Slot")
        self.tree.heading("Estado", text="Estado")
        
        self.tree.column("Serial", width=200)
        self.tree.column("Modelo", width=200)
        self.tree.column("Área", width=120)
        self.tree.column("Rack", width=100)
        self.tree.column("Slot", width=100)
        self.tree.column("Estado", width=120)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        try:
            self.filter_nodes()
        except:
            pass
    
    def create_management_page(self):
        """Crea la página de gestión"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages["management"] = page
        
        # Header
        header = ctk.CTkFrame(page, fg_color="white", corner_radius=15, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(header_content, text="Gestión de Nodos", 
                    font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Panel de actualización
        update_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        update_panel.pack(fill="x", pady=(0, 20))
        
        update_content = ctk.CTkFrame(update_panel, fg_color="transparent")
        update_content.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkLabel(update_content, text="Actualizar Ubicación", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        fields_grid = ctk.CTkFrame(update_content, fg_color="transparent")
        fields_grid.pack(fill="x")
        
        labels_texts = ["Número de Serie:", "Nueva Área:", "Nuevo Rack:", "Nuevo Slot:"]
        entries = []
        
        for i, label_text in enumerate(labels_texts):
            row = ctk.CTkFrame(fields_grid, fg_color="transparent")
            row.pack(fill="x", pady=12)
            
            ctk.CTkLabel(row, text=label_text, 
                        font=ctk.CTkFont(size=14), width=150).pack(side="left", padx=(0, 15))
            
            entry = ctk.CTkEntry(row, width=300, height=40)
            entry.pack(side="left")
            entries.append(entry)
        
        self.update_serial, self.update_area, self.update_rack, self.update_slot = entries
        
        ctk.CTkButton(update_content, text="Guardar Cambios", 
                     command=self.update_location,
                     height=45, width=200,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#2ECC71").pack(pady=(20, 0))
        
        # Panel de reporte
        report_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        report_panel.pack(fill="x")
        
        report_content = ctk.CTkFrame(report_panel, fg_color="transparent")
        report_content.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkLabel(report_content, text="Reportar Nodo Mal Ubicado", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        report_grid = ctk.CTkFrame(report_content, fg_color="transparent")
        report_grid.pack(fill="x")
        
        report_labels = ["Número de Serie:", "Área Correcta:", "Rack Correcto:", "Slot Correcto:"]
        report_entries = []
        
        for label_text in report_labels:
            row = ctk.CTkFrame(report_grid, fg_color="transparent")
            row.pack(fill="x", pady=12)
            
            ctk.CTkLabel(row, text=label_text, 
                        font=ctk.CTkFont(size=14), width=150).pack(side="left", padx=(0, 15))
            
            entry = ctk.CTkEntry(row, width=300, height=40)
            entry.pack(side="left")
            report_entries.append(entry)
        
        self.report_serial, self.report_area, self.report_rack, self.report_slot = report_entries
        
        ctk.CTkButton(report_content, text="Enviar Reporte", 
                     command=self.report_misplacement,
                     height=45, width=200,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#E67E22").pack(pady=(20, 0))
    
    def create_simulation_page(self):
        """Crea la página de simulación"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages["simulation"] = page
        
        # Header
        header = ctk.CTkFrame(page, fg_color="white", corner_radius=15, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(header_content, text="Motor de Simulación", 
                    font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        # Panel de parámetros
        params_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        params_panel.pack(fill="x", pady=(0, 20))
        
        params_content = ctk.CTkFrame(params_panel, fg_color="transparent")
        params_content.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkLabel(params_content, text="Parámetros de Simulación", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Grid de parámetros
        params_grid = ctk.CTkFrame(params_content, fg_color="transparent")
        params_grid.pack(fill="x")
        
        params_data = [
            ("Técnicos:", "n_techs", "2"),
            ("λ Órdenes/hora:", "lambda_orders", "0.5"),
            ("Tiempo Movimiento (min):", "t_move", "2.0"),
            ("Tiempo Inspección (min):", "t_inspect", "1.0"),
            ("Prob. Reubicación:", "p_reloc", "0.1"),
            ("Tasa Mal Ubicación:", "misplacement", "0.0"),
            ("Estrategia:", "strategy", "actual", "combo"),
            ("Tiempo Simulación (min):", "sim_time", "480"),
            ("RFID Factor:", "rfid_factor", "0.2"),
            ("Semilla (seed):", "seed", "", "optional"),
            ("Congestión:", "congestion", "True", "checkbox")
        ]
        
        self.sim_params = {}
        for i, (label, key, default, *extra) in enumerate(params_data):
            row = ctk.CTkFrame(params_grid, fg_color="transparent")
            row.grid(row=i//2, column=i%2, padx=15, pady=12, sticky="ew")
            params_grid.grid_columnconfigure(i%2, weight=1)
            
            ctk.CTkLabel(row, text=label, 
                        font=ctk.CTkFont(size=14), width=180).pack(side="left", padx=(0, 10))
            
            if "combo" in extra:
                widget = ctk.CTkComboBox(row, width=200, height=40,
                                        values=["actual", "by_model", "rfid", "statistical", "by_lot"])
                widget.set(default)
            elif "checkbox" in extra:
                widget = ctk.CTkCheckBox(row, text="", width=150, height=40)
                widget.select() if default == "True" else widget.deselect()
            elif "optional" in extra:
                widget = ctk.CTkEntry(row, width=150, height=40, placeholder_text="Opcional")
                if default:
                    widget.insert(0, default)
            else:
                widget = ctk.CTkEntry(row, width=150, height=40)
                widget.insert(0, default)
            
            widget.pack(side="left")
            self.sim_params[key] = widget
        
        # Botones de control
        control_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        control_panel.pack(fill="x", pady=(0, 20))
        
        control_content = ctk.CTkFrame(control_panel, fg_color="transparent")
        control_content.pack(pady=30)
        
        ctk.CTkButton(control_content, text="Ejecutar Simulación", 
                     command=self.run_simulation,
                     width=250, height=50,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     fg_color="#9B59B6").pack(side="left", padx=15)
        
        ctk.CTkButton(control_content, text="Ejecutar Experimento (10 réplicas)", 
                     command=self.run_experiment_gui,
                     width=300, height=50,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     fg_color="#8E44AD").pack(side="left", padx=15)
        
        ctk.CTkButton(control_content, text="Comparar Todas las Estrategias", 
                     command=self.run_all_strategies_comparison,
                     width=280, height=50,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     fg_color="#E67E22").pack(side="left", padx=15)
        
        # Panel de resultados con gráfica
        results_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        results_panel.pack(fill="both", expand=True)
        
        results_content = ctk.CTkFrame(results_panel, fg_color="transparent")
        results_content.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Panel de gráfica comparativa
        chart_label = ctk.CTkFrame(results_content, fg_color="transparent")
        chart_label.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(chart_label, text="Comparación de Estrategias", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        self.sim_comparison_chart_frame = ctk.CTkFrame(results_content, fg_color="transparent", height=300)
        self.sim_comparison_chart_frame.pack(fill="x", pady=(0, 20))
        self.sim_comparison_chart_frame.pack_propagate(False)
        
        # Panel de resultados de texto
        ctk.CTkLabel(results_content, text="Resultados de la Simulación", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        self.sim_results_text = ctk.CTkTextbox(results_content, height=250, 
                                               font=ctk.CTkFont(size=13))
        self.sim_results_text.pack(fill="both", expand=True)
    
    def create_results_page(self):
        """Crea la página de resultados con análisis en vivo"""
        page = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.pages["results"] = page
        
        # Header
        header = ctk.CTkFrame(page, fg_color="white", corner_radius=15, height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(header_content, text="Análisis de Resultados en Vivo", 
                    font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(header_content, text="Actualizar Análisis", 
                                   command=self.update_live_analysis,
                                   width=150, height=35)
        refresh_btn.pack(side="right", padx=(10, 0))
        
        # Panel de comparación de estrategias
        comparison_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        comparison_panel.pack(fill="x", pady=(0, 20))
        
        comp_content = ctk.CTkFrame(comparison_panel, fg_color="transparent")
        comp_content.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkLabel(comp_content, text="Comparación de Estrategias", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Contenedor para gráfico comparativo
        self.comparison_chart_frame = ctk.CTkFrame(comp_content, fg_color="transparent")
        self.comparison_chart_frame.pack(fill="both", expand=True, pady=10)
        
        # Panel de mejoras
        improvements_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        improvements_panel.pack(fill="x", pady=(0, 20))
        
        imp_content = ctk.CTkFrame(improvements_panel, fg_color="transparent")
        imp_content.pack(fill="x", padx=30, pady=30)
        
        ctk.CTkLabel(imp_content, text="Mejoras Detectadas", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        self.improvements_text = ctk.CTkTextbox(imp_content, height=200, 
                                                font=ctk.CTkFont(size=13))
        self.improvements_text.pack(fill="both", expand=True)
        
        # Panel de resultados recientes
        recent_panel = ctk.CTkFrame(page, fg_color="white", corner_radius=15)
        recent_panel.pack(fill="both", expand=True)
        
        recent_content = ctk.CTkFrame(recent_panel, fg_color="transparent")
        recent_content.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(recent_content, text="Resultados Recientes", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        self.recent_results_text = ctk.CTkTextbox(recent_content, height=250, 
                                                  font=ctk.CTkFont(size=12))
        self.recent_results_text.pack(fill="both", expand=True)
        
        # Botón para abrir notebook
        notebook_btn_frame = ctk.CTkFrame(page, fg_color="transparent")
        notebook_btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(notebook_btn_frame, text="Abrir Notebook de Análisis Detallado", 
                     command=self.open_notebook,
                     width=300, height=45,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="#E74C3C").pack()
        
        # Cargar análisis inicial
        self.update_live_analysis()
    
    def update_statistics(self):
        """Actualiza las estadísticas del dashboard"""
        try:
            all_nodes = self.inventory.db.get_all_nodes()
            total_nodes = len(all_nodes)
            models = set(n['model'] for n in all_nodes)
            areas = set(n['area'] for n in all_nodes)
            active_nodes = len([n for n in all_nodes if n['status'] == 'active'])
            
            if hasattr(self, 'stats_labels'):
                self.stats_labels["Total de Nodos"].configure(text=str(total_nodes))
                self.stats_labels["Modelos"].configure(text=str(len(models)))
                self.stats_labels["Áreas"].configure(text=str(len(areas)))
                self.stats_labels["Activos"].configure(text=str(active_nodes))
        except:
            pass
    
    def search_by_serial(self):
        """Busca un nodo por número de serie"""
        serial = self.serial_entry.get().strip()
        if not serial:
            messagebox.showwarning("Advertencia", "Por favor ingrese un número de serie")
            return
        
        node = self.inventory.get_location(serial)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if node:
            self.tree.insert("", "end", values=(
                node['serial'], node['model'], node['area'], 
                node['rack'], node['slot'], node['status']
            ))
            if hasattr(self, 'results_count_label'):
                self.results_count_label.configure(text="1 nodo encontrado")
        else:
            messagebox.showinfo("No encontrado", f"No se encontró el nodo con serie: {serial}")
            if hasattr(self, 'results_count_label'):
                self.results_count_label.configure(text="0 nodos encontrados")
    
    def filter_nodes(self):
        """Filtra nodos por modelo y/o área"""
        model = self.model_filter.get()
        area = self.area_filter.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        model_val = None if model == "Todos" else model
        area_val = None if area == "Todas" else area
        
        nodes = self.inventory.filter_nodes(model=model_val, area=area_val)
        
        for node in nodes:
            self.tree.insert("", "end", values=(
                node['serial'], node['model'], node['area'], 
                node['rack'], node['slot'], node['status']
            ))
        
        if hasattr(self, 'results_count_label'):
            self.results_count_label.configure(text=f"{len(nodes)} nodos encontrados")
    
    def update_location(self):
        """Actualiza la ubicación de un nodo"""
        serial = self.update_serial.get().strip()
        area = self.update_area.get().strip() or None
        rack = self.update_rack.get().strip() or None
        slot = self.update_slot.get().strip() or None
        
        if not serial:
            messagebox.showwarning("Advertencia", "Por favor ingrese un número de serie")
            return
        
        if not any([area, rack, slot]):
            messagebox.showwarning("Advertencia", "Por favor ingrese al menos un campo a actualizar")
            return
        
        try:
            rack = int(rack) if rack else None
            slot = int(slot) if slot else None
        except ValueError:
            messagebox.showerror("Error", "Rack y Slot deben ser números enteros")
            return
        
        success = self.inventory.update_location(serial, area, rack, slot)
        
        if success:
            messagebox.showinfo("Éxito", "Ubicación actualizada correctamente")
            self.update_serial.delete(0, "end")
            self.update_area.delete(0, "end")
            self.update_rack.delete(0, "end")
            self.update_slot.delete(0, "end")
            self.filter_nodes()
            self.update_statistics()
        else:
            messagebox.showerror("Error", "No se pudo actualizar la ubicación. Verifique el número de serie.")
    
    def report_misplacement(self):
        """Reporta un nodo mal ubicado"""
        serial = self.report_serial.get().strip()
        area = self.report_area.get().strip() or None
        rack = self.report_rack.get().strip() or None
        slot = self.report_slot.get().strip() or None
        
        if not serial:
            messagebox.showwarning("Advertencia", "Por favor ingrese un número de serie")
            return
        
        try:
            rack = int(rack) if rack else None
            slot = int(slot) if slot else None
        except ValueError:
            messagebox.showerror("Error", "Rack y Slot deben ser números enteros")
            return
        
        success = self.inventory.report_misplacement(serial, area, rack, slot)
        
        if success:
            messagebox.showinfo("Éxito", "Mal ubicación reportada y corregida")
            self.report_serial.delete(0, "end")
            self.report_area.delete(0, "end")
            self.report_rack.delete(0, "end")
            self.report_slot.delete(0, "end")
            self.filter_nodes()
            self.update_statistics()
        else:
            messagebox.showerror("Error", "No se pudo reportar la mal ubicación. Verifique el número de serie.")
    
    def run_simulation(self):
        """Ejecuta una simulación individual"""
        try:
            # Verificar que los parámetros estén inicializados
            if not hasattr(self, 'sim_params') or not self.sim_params:
                messagebox.showerror("Error", "Los parámetros de simulación no están inicializados. Por favor, ve a la pestaña de Simulación primero.")
                return
            
            n_techs = int(self.sim_params['n_techs'].get())
            lambda_orders = float(self.sim_params['lambda_orders'].get())
            t_move_unit = float(self.sim_params['t_move'].get())
            t_inspect = float(self.sim_params['t_inspect'].get())
            p_reloc = float(self.sim_params['p_reloc'].get())
            misplacement_rate = float(self.sim_params['misplacement'].get())
            strategy = self.sim_params['strategy'].get()
            sim_time = float(self.sim_params['sim_time'].get())
            
            # Parámetros adicionales con manejo seguro
            try:
                rfid_factor = float(self.sim_params.get('rfid_factor', ctk.CTkEntry()).get() or "0.2")
            except:
                rfid_factor = 0.2
            
            try:
                seed_str = self.sim_params.get('seed', ctk.CTkEntry()).get() or ""
                seed = int(seed_str) if seed_str.strip() else None
            except:
                seed = None
            
            try:
                congestion_widget = self.sim_params.get('congestion')
                congestion_enabled = congestion_widget.get() if congestion_widget and hasattr(congestion_widget, 'get') else True
            except:
                congestion_enabled = True
            
            def run():
                self.sim_results_text.delete("1.0", "end")
                self.sim_results_text.insert("1.0", "Ejecutando simulación...\n")
                self.update_idletasks()
                
                db = InventoryDB("data/inventory.db")
                sim_engine = SimulationEngine(
                    inventory_db=db,
                    n_techs=n_techs,
                    lambda_orders=lambda_orders,
                    t_move_unit=t_move_unit,
                    t_inspect=t_inspect,
                    p_reloc=p_reloc,
                    misplacement_rate=misplacement_rate,
                    strategy=strategy,
                    simulation_time=sim_time,
                    rfid_factor=rfid_factor,
                    seed=seed,
                    congestion_enabled=congestion_enabled
                )
                
                stats = sim_engine.run()
                
                # Guardar resultado automáticamente
                result_data = {
                    'scenario': f'single_{strategy}',
                    'replica': 1,
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
                    'mean_steps_walked': stats.get('mean_steps_walked', 0.0),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Guardar en CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"results/single_sim_{strategy}_{timestamp}.csv"
                os.makedirs("results", exist_ok=True)
                pd.DataFrame([result_data]).to_csv(filename, index=False)
                
                # Agregar al historial
                self.results_history.append(result_data)
                
                # Actualizar análisis en vivo
                self.after(0, self.update_live_analysis)
                
                results_text = f"""
═══════════════════════════════════════════════════════════
         RESULTADOS DE LA SIMULACIÓN
═══════════════════════════════════════════════════════════

Estrategia: {strategy.upper()}
Tiempo de simulación: {sim_time} minutos
Número de técnicos: {n_techs}

ÓRDENES:
   Procesadas: {stats['orders_processed']}
   Fallidas: {stats['orders_failed']}
   Total: {stats['orders_processed'] + stats['orders_failed']}
   Tasa de error: {stats['error_rate']*100:.2f}%

TIEMPOS DE BÚSQUEDA:
   Tiempo medio (T_mean): {stats['mean_search_time']:.2f} minutos
   Percentil 95 (T_p95): {stats['p95_search_time']:.2f} minutos

UTILIZACIÓN DE TÉCNICOS:
   Utilización promedio: {stats['avg_utilization']:.2f}%

KPIs ADICIONALES:
   Longitud media de cola: {stats.get('mean_queue_length', 0.0):.2f}
   Longitud máxima de cola: {stats.get('max_queue_length', 0)}
   Pasos totales recorridos: {stats.get('total_steps_walked', 0.0):.1f}
   Pasos promedio por orden: {stats.get('mean_steps_walked', 0.0):.2f}

Resultado guardado automáticamente en: {filename}
"""
                self.sim_results_text.delete("1.0", "end")
                self.sim_results_text.insert("1.0", results_text)
            
            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            
        except KeyError as e:
            messagebox.showerror("Error", f"Parámetro faltante: {str(e)}\nPor favor, verifica que todos los campos estén completos.")
        except ValueError as e:
            messagebox.showerror("Error", f"Error en los parámetros: {str(e)}\nVerifica que todos los valores numéricos sean válidos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}\n\nDetalles técnicos:\n{type(e).__name__}")
            import traceback
            print(traceback.format_exc())
    
    def run_experiment_gui(self):
        """Ejecuta un experimento con múltiples réplicas"""
        try:
            # Verificar que los parámetros estén inicializados
            if not hasattr(self, 'sim_params') or not self.sim_params:
                messagebox.showerror("Error", "Los parámetros de simulación no están inicializados. Por favor, ve a la pestaña de Simulación primero.")
                return
            
            n_techs = int(self.sim_params['n_techs'].get())
            lambda_orders = float(self.sim_params['lambda_orders'].get())
            t_move_unit = float(self.sim_params['t_move'].get())
            t_inspect = float(self.sim_params['t_inspect'].get())
            p_reloc = float(self.sim_params['p_reloc'].get())
            misplacement_rate = float(self.sim_params['misplacement'].get())
            strategy = self.sim_params['strategy'].get()
            sim_time = float(self.sim_params['sim_time'].get())
            
            # Parámetros adicionales con manejo seguro
            try:
                rfid_factor = float(self.sim_params.get('rfid_factor', ctk.CTkEntry()).get() or "0.2")
            except:
                rfid_factor = 0.2
            
            try:
                seed_str = self.sim_params.get('seed', ctk.CTkEntry()).get() or ""
                seed = int(seed_str) if seed_str.strip() else None
            except:
                seed = None
            
            try:
                congestion_widget = self.sim_params.get('congestion')
                congestion_enabled = congestion_widget.get() if congestion_widget and hasattr(congestion_widget, 'get') else True
            except:
                congestion_enabled = True
            
            def run():
                self.sim_results_text.delete("1.0", "end")
                self.sim_results_text.insert("1.0", "Ejecutando experimento con 10 réplicas...\nEsto puede tomar varios minutos.\n")
                self.update_idletasks()
                
                results = run_experiment(
                    scenario_name=f"gui_{strategy}",
                    n_replicas=10,
                    n_techs=n_techs,
                    lambda_orders=lambda_orders,
                    t_move_unit=t_move_unit,
                    t_inspect=t_inspect,
                    p_reloc=p_reloc,
                    misplacement_rate=misplacement_rate,
                    strategy=strategy,
                    simulation_time=sim_time,
                    rfid_factor=rfid_factor,
                    seed=seed,
                    congestion_enabled=congestion_enabled
                )
                
                save_results(results, f"results/gui_experiment_{strategy}.csv")
                
                avg_mean = sum(r['mean_search_time'] for r in results) / len(results)
                avg_p95 = sum(r['p95_search_time'] for r in results) / len(results)
                avg_error = sum(r['error_rate'] for r in results) / len(results)
                avg_util = sum(r['avg_utilization'] for r in results) / len(results)
                
                # Guardar resultado promedio para comparación
                result_data = {
                    'scenario': f'experiment_{strategy}',
                    'replica': 'average',
                    'strategy': strategy,
                    'n_techs': n_techs,
                    'lambda_orders': lambda_orders,
                    'misplacement_rate': misplacement_rate,
                    'mean_search_time': avg_mean,
                    'p95_search_time': avg_p95,
                    'error_rate': avg_error,
                    'orders_processed': sum(r['orders_processed'] for r in results),
                    'orders_failed': sum(r['orders_failed'] for r in results),
                    'avg_utilization': avg_util,
                    'total_orders': sum(r['total_orders'] for r in results),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.results_history.append(result_data)
                
                # Actualizar análisis en vivo
                self.after(0, self.update_live_analysis)
                
                results_text = f"""
═══════════════════════════════════════════════════════════
         EXPERIMENTO COMPLETADO
═══════════════════════════════════════════════════════════

Estrategia: {strategy.upper()}
Réplicas: 10
Tiempo de simulación: {sim_time} minutos

RESULTADOS PROMEDIO:
   Tiempo medio (T_mean): {avg_mean:.2f} minutos
   Percentil 95 (T_p95): {avg_p95:.2f} minutos
   Tasa de error: {avg_error*100:.2f}%
   Utilización promedio: {avg_util:.2f}%

Resultados guardados en: results/gui_experiment_{strategy}.csv
Análisis actualizado automáticamente en la pestaña Resultados.
"""
                self.sim_results_text.delete("1.0", "end")
                self.sim_results_text.insert("1.0", results_text)
                messagebox.showinfo("Éxito", "Experimento completado. Resultados guardados y análisis actualizado.")
            
            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            
        except KeyError as e:
            messagebox.showerror("Error", f"Parámetro faltante: {str(e)}\nPor favor, verifica que todos los campos estén completos.")
        except ValueError as e:
            messagebox.showerror("Error", f"Error en los parámetros: {str(e)}\nVerifica que todos los valores numéricos sean válidos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}\n\nDetalles técnicos:\n{type(e).__name__}")
            import traceback
            print(traceback.format_exc())
    
    def run_all_strategies_comparison(self):
        """Ejecuta simulaciones para todas las estrategias y muestra comparación"""
        try:
            # Verificar que los parámetros estén inicializados
            if not hasattr(self, 'sim_params') or not self.sim_params:
                messagebox.showerror("Error", "Los parámetros de simulación no están inicializados.")
                return
            
            # Leer parámetros de la GUI
            n_techs = int(self.sim_params['n_techs'].get())
            lambda_orders = float(self.sim_params['lambda_orders'].get())
            t_move_unit = float(self.sim_params['t_move'].get())
            t_inspect = float(self.sim_params['t_inspect'].get())
            p_reloc = float(self.sim_params['p_reloc'].get())
            misplacement_rate = float(self.sim_params['misplacement'].get())
            sim_time = float(self.sim_params['sim_time'].get())
            
            # Parámetros adicionales
            try:
                rfid_factor = float(self.sim_params.get('rfid_factor', ctk.CTkEntry()).get() or "0.2")
            except:
                rfid_factor = 0.2
            
            try:
                seed_str = self.sim_params.get('seed', ctk.CTkEntry()).get() or ""
                seed = int(seed_str) if seed_str.strip() else None
            except:
                seed = None
            
            try:
                congestion_widget = self.sim_params.get('congestion')
                congestion_enabled = congestion_widget.get() if congestion_widget and hasattr(congestion_widget, 'get') else True
            except:
                congestion_enabled = True
            
            strategies = ["actual", "by_model", "rfid", "statistical", "by_lot"]
            
            def run():
                self.sim_results_text.delete("1.0", "end")
                self.sim_results_text.insert("1.0", "Ejecutando comparación de todas las estrategias...\n\n")
                self.sim_results_text.insert("end", f"Parámetros:\n")
                self.sim_results_text.insert("end", f"  Técnicos: {n_techs}\n")
                self.sim_results_text.insert("end", f"  λ Órdenes/hora: {lambda_orders}\n")
                self.sim_results_text.insert("end", f"  Tiempo Movimiento: {t_move_unit} min\n")
                self.sim_results_text.insert("end", f"  Prob. Reubicación: {p_reloc}\n")
                self.sim_results_text.insert("end", f"  RFID Factor: {rfid_factor}\n")
                self.sim_results_text.insert("end", f"  Congestión: {'Habilitada' if congestion_enabled else 'Deshabilitada'}\n\n")
                self.update_idletasks()
                
                all_results = []
                db = InventoryDB("data/inventory.db")
                
                for i, strategy in enumerate(strategies, 1):
                    self.sim_results_text.insert("end", f"[{i}/{len(strategies)}] Ejecutando estrategia: {strategy.upper()}...\n")
                    self.sim_results_text.see("end")
                    self.update_idletasks()
                    
                    sim_engine = SimulationEngine(
                        inventory_db=db,
                        n_techs=n_techs,
                        lambda_orders=lambda_orders,
                        t_move_unit=t_move_unit,
                        t_inspect=t_inspect,
                        p_reloc=p_reloc,
                        misplacement_rate=misplacement_rate,
                        strategy=strategy,
                        simulation_time=sim_time,
                        rfid_factor=rfid_factor,
                        seed=seed + i if seed is not None else None,
                        congestion_enabled=congestion_enabled
                    )
                    
                    stats = sim_engine.run()
                    
                    result_data = {
                        'scenario': f'comparison_{strategy}',
                        'replica': 1,
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
                        'mean_steps_walked': stats.get('mean_steps_walked', 0.0),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    all_results.append(result_data)
                    
                    # Guardar individual
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"results/comparison_{strategy}_{timestamp}.csv"
                    os.makedirs("results", exist_ok=True)
                    pd.DataFrame([result_data]).to_csv(filename, index=False)
                    
                    self.sim_results_text.insert("end", f"  ✓ Completada: T_mean={stats['mean_search_time']:.2f} min\n\n")
                    self.sim_results_text.see("end")
                    self.update_idletasks()
                
                # Crear DataFrame con todos los resultados
                df_comparison = pd.DataFrame(all_results)
                
                # Guardar comparación completa
                comparison_filename = f"results/comparison_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df_comparison.to_csv(comparison_filename, index=False)
                
                # Actualizar gráfica comparativa en el panel de simulación
                self.after(0, lambda: self.update_sim_comparison_chart(df_comparison))
                
                # Obtener baseline (actual) para comparación
                baseline_result = next((r for r in all_results if r['strategy'] == 'actual'), None)
                baseline_mean = baseline_result['mean_search_time'] if baseline_result else None
                baseline_p95 = baseline_result['p95_search_time'] if baseline_result else None
                
                # Mostrar resumen de resultados
                summary_text = "\n" + "="*60 + "\n"
                summary_text += "         RESUMEN DE COMPARACIÓN\n"
                summary_text += "="*60 + "\n\n"
                
                if baseline_result:
                    summary_text += f"BASELINE (ACTUAL):\n"
                    summary_text += f"  Tiempo medio: {baseline_mean:.2f} min\n"
                    summary_text += f"  P95: {baseline_p95:.2f} min\n"
                    summary_text += f"  Tasa de error: {baseline_result['error_rate']*100:.2f}%\n"
                    summary_text += f"  Utilización: {baseline_result['avg_utilization']:.2f}%\n\n"
                    summary_text += "─" * 60 + "\n\n"
                
                for result in all_results:
                    if result['strategy'] == 'actual' and baseline_result:
                        continue  # Ya se mostró como baseline
                    
                    summary_text += f"{result['strategy'].upper()}:\n"
                    summary_text += f"  Tiempo medio: {result['mean_search_time']:.2f} min"
                    
                    # Calcular porcentaje de mejora/degradación
                    if baseline_mean:
                        pct_change = ((baseline_mean - result['mean_search_time']) / baseline_mean) * 100
                        if pct_change > 0:
                            summary_text += f" → {pct_change:.1f}% MÁS RÁPIDO ✓\n"
                        elif pct_change < 0:
                            summary_text += f" → {abs(pct_change):.1f}% MÁS LENTO ✗\n"
                        else:
                            summary_text += " → IGUAL\n"
                    else:
                        summary_text += "\n"
                    
                    summary_text += f"  P95: {result['p95_search_time']:.2f} min"
                    if baseline_p95:
                        pct_p95 = ((baseline_p95 - result['p95_search_time']) / baseline_p95) * 100
                        if pct_p95 > 0:
                            summary_text += f" → {pct_p95:.1f}% MÁS RÁPIDO ✓\n"
                        elif pct_p95 < 0:
                            summary_text += f" → {abs(pct_p95):.1f}% MÁS LENTO ✗\n"
                        else:
                            summary_text += " → IGUAL\n"
                    else:
                        summary_text += "\n"
                    
                    summary_text += f"  Tasa de error: {result['error_rate']*100:.2f}%\n"
                    summary_text += f"  Utilización: {result['avg_utilization']:.2f}%\n\n"
                
                # Encontrar mejor estrategia
                best = min(all_results, key=lambda x: x['mean_search_time'])
                summary_text += "═" * 60 + "\n"
                summary_text += f"🏆 MEJOR ESTRATEGIA: {best['strategy'].upper()}\n"
                summary_text += f"   Tiempo medio: {best['mean_search_time']:.2f} min\n"
                
                if baseline_mean and best['strategy'] != 'actual':
                    best_improvement = ((baseline_mean - best['mean_search_time']) / baseline_mean) * 100
                    summary_text += f"   → {best_improvement:.1f}% MÁS RÁPIDO que Actual\n"
                
                summary_text += "\n" + "─" * 60 + "\n"
                summary_text += f"Resultados guardados en: {comparison_filename}\n"
                
                self.sim_results_text.insert("end", summary_text)
                self.sim_results_text.see("end")
                
                # Agregar al historial
                for result in all_results:
                    self.results_history.append(result)
                
                # Actualizar análisis en vivo en pestaña Resultados
                self.after(0, self.update_live_analysis)
                
                messagebox.showinfo("Éxito", f"Comparación completada.\n\nMejor estrategia: {best['strategy'].upper()}\nTiempo medio: {best['mean_search_time']:.2f} min")
            
            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            
        except KeyError as e:
            messagebox.showerror("Error", f"Parámetro faltante: {str(e)}\nPor favor, verifica que todos los campos estén completos.")
        except ValueError as e:
            messagebox.showerror("Error", f"Error en los parámetros: {str(e)}\nVerifica que todos los valores numéricos sean válidos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def update_sim_comparison_chart(self, df_comparison):
        """Actualiza la gráfica comparativa en el panel de simulación"""
        try:
            # Limpiar frame anterior
            for widget in self.sim_comparison_chart_frame.winfo_children():
                widget.destroy()
            
            if df_comparison.empty:
                ctk.CTkLabel(self.sim_comparison_chart_frame, 
                           text="No hay datos para comparar").pack()
                return
            
            # Obtener baseline (actual) si existe
            baseline_mean = None
            baseline_p95 = None
            if 'actual' in df_comparison['strategy'].values:
                baseline_row = df_comparison[df_comparison['strategy'] == 'actual'].iloc[0]
                baseline_mean = baseline_row['mean_search_time']
                baseline_p95 = baseline_row['p95_search_time']
            
            # Ordenar por tiempo medio
            df_sorted = df_comparison.sort_values('mean_search_time')
            strategies = df_sorted['strategy'].tolist()
            mean_times = df_sorted['mean_search_time'].tolist()
            p95_times = df_sorted['p95_search_time'].tolist()
            
            # Crear gráfico comparativo con múltiples métricas
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor='white')
            
            # Gráfico 1: Tiempo medio
            colors = ['#3498DB', '#2ECC71', '#E67E22', '#9B59B6', '#E74C3C']
            bars1 = ax1.bar(strategies, mean_times, color=colors[:len(strategies)])
            ax1.set_ylabel('Tiempo Medio (minutos)', fontsize=11, color='#555')
            ax1.set_title('Tiempo Medio de Búsqueda', 
                         fontsize=12, fontweight='bold', color='#2C3E50', pad=10)
            ax1.set_facecolor('white')
            ax1.tick_params(colors='#555', labelsize=9)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color('#E0E0E0')
            ax1.spines['bottom'].set_color('#E0E0E0')
            
            # Agregar valores y porcentajes en las barras
            for i, (bar, strategy, time) in enumerate(zip(bars1, strategies, mean_times)):
                height = bar.get_height()
                # Valor del tiempo
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(mean_times)*0.02,
                        f'{time:.2f} min',
                        ha='center', va='bottom', fontsize=8, color='#555', fontweight='bold')
                
                # Porcentaje de mejora/degradación si hay baseline
                if baseline_mean and strategy != 'actual':
                    pct_change = ((baseline_mean - time) / baseline_mean) * 100
                    if pct_change > 0:
                        pct_text = f'{pct_change:.1f}% más rápido'
                        color_text = '#2ECC71'  # Verde para mejor
                    elif pct_change < 0:
                        pct_text = f'{abs(pct_change):.1f}% más lento'
                        color_text = '#E74C3C'  # Rojo para peor
                    else:
                        pct_text = 'igual'
                        color_text = '#555'
                    
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(mean_times)*0.08,
                            pct_text,
                            ha='center', va='bottom', fontsize=8, color=color_text, 
                            fontweight='bold', style='italic')
            
            # Gráfico 2: Percentil 95
            bars2 = ax2.bar(strategies, p95_times, color=colors[:len(strategies)])
            ax2.set_ylabel('Tiempo P95 (minutos)', fontsize=11, color='#555')
            ax2.set_title('Percentil 95 de Búsqueda', 
                         fontsize=12, fontweight='bold', color='#2C3E50', pad=10)
            ax2.set_facecolor('white')
            ax2.tick_params(colors='#555', labelsize=9)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#E0E0E0')
            ax2.spines['bottom'].set_color('#E0E0E0')
            
            # Agregar valores y porcentajes en las barras
            for i, (bar, strategy, time) in enumerate(zip(bars2, strategies, p95_times)):
                height = bar.get_height()
                # Valor del tiempo
                ax2.text(bar.get_x() + bar.get_width()/2., height + max(p95_times)*0.02,
                        f'{time:.2f} min',
                        ha='center', va='bottom', fontsize=8, color='#555', fontweight='bold')
                
                # Porcentaje de mejora/degradación si hay baseline
                if baseline_p95 and strategy != 'actual':
                    pct_change = ((baseline_p95 - time) / baseline_p95) * 100
                    if pct_change > 0:
                        pct_text = f'{pct_change:.1f}% más rápido'
                        color_text = '#2ECC71'  # Verde para mejor
                    elif pct_change < 0:
                        pct_text = f'{abs(pct_change):.1f}% más lento'
                        color_text = '#E74C3C'  # Rojo para peor
                    else:
                        pct_text = 'igual'
                        color_text = '#555'
                    
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(p95_times)*0.08,
                            pct_text,
                            ha='center', va='bottom', fontsize=8, color=color_text,
                            fontweight='bold', style='italic')
            
            fig.patch.set_facecolor('white')
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.sim_comparison_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            ctk.CTkLabel(self.sim_comparison_chart_frame, 
                        text=f"Error al generar gráfico: {str(e)}").pack()
    
    def set_strategy(self, strategy):
        """Establece la estrategia de simulación"""
        if hasattr(self, 'sim_params') and 'strategy' in self.sim_params:
            self.sim_params['strategy'].set(strategy)
            self.show_page("simulation")
            messagebox.showinfo("Estrategia", f"Estrategia cambiada a: {strategy}")
    
    def generate_test_data(self):
        """Genera datos de prueba"""
        response = messagebox.askyesno("Generar Datos", 
                                       "¿Desea generar 1000 nodos de prueba?")
        if response:
            try:
                from generate_data import generate_synthetic_data
                generate_synthetic_data(1000)
                messagebox.showinfo("Éxito", "Datos de prueba generados correctamente")
                self.update_statistics()
                self.filter_nodes()
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar datos: {str(e)}")
    
    def export_results(self):
        """Exporta resultados"""
        messagebox.showinfo("Exportar", "Los resultados se encuentran en la carpeta 'results/'")
    
    def show_about(self):
        """Muestra información acerca de la aplicación"""
        messagebox.showinfo("Acerca de", 
                           "Sistema de Inventario y Simulación\n\n"
                           "Versión 1.0\n\n"
                           "Desarrollado para UANL-FIME")
    
    def update_live_analysis(self):
        """Actualiza el análisis en vivo cargando resultados y mostrando comparaciones"""
        try:
            # Cargar todos los resultados CSV
            csv_files = glob.glob("results/*.csv")
            all_results = []
            
            for file in csv_files:
                try:
                    df = pd.read_csv(file)
                    all_results.append(df)
                except:
                    continue
            
            if not all_results:
                self.improvements_text.delete("1.0", "end")
                self.improvements_text.insert("1.0", "No hay resultados disponibles aún.\nEjecuta una simulación o experimento para ver el análisis.")
                self.recent_results_text.delete("1.0", "end")
                self.recent_results_text.insert("1.0", "No hay resultados recientes.")
                return
            
            # Combinar todos los resultados
            df_all = pd.concat(all_results, ignore_index=True)
            
            # Agrupar por estrategia y calcular promedios
            strategy_stats = df_all.groupby('strategy').agg({
                'mean_search_time': 'mean',
                'p95_search_time': 'mean',
                'error_rate': 'mean',
                'avg_utilization': 'mean'
            }).round(2)
            
            # Crear gráfico comparativo
            self.update_comparison_chart(strategy_stats)
            
            # Calcular mejoras
            improvements_text = self.calculate_improvements(strategy_stats)
            self.improvements_text.delete("1.0", "end")
            self.improvements_text.insert("1.0", improvements_text)
            
            # Mostrar resultados recientes
            recent_text = self.format_recent_results(df_all)
            self.recent_results_text.delete("1.0", "end")
            self.recent_results_text.insert("1.0", recent_text)
            
        except Exception as e:
            self.improvements_text.delete("1.0", "end")
            self.improvements_text.insert("1.0", f"Error al cargar análisis: {str(e)}")
    
    def update_comparison_chart(self, strategy_stats):
        """Actualiza el gráfico comparativo de estrategias"""
        try:
            # Limpiar frame anterior
            for widget in self.comparison_chart_frame.winfo_children():
                widget.destroy()
            
            strategies = strategy_stats.index.tolist()
            mean_times = strategy_stats['mean_search_time'].tolist()
            
            fig, ax = plt.subplots(figsize=(10, 5), facecolor='white')
            colors = ['#3498DB', '#2ECC71', '#E67E22', '#9B59B6', '#E74C3C']
            bars = ax.bar(strategies, mean_times, color=colors[:len(strategies)])
            ax.set_ylabel('Tiempo Medio (minutos)', fontsize=12, color='#555')
            ax.set_title('Comparación de Tiempo Medio por Estrategia', 
                        fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')
            ax.tick_params(colors='#555', labelsize=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#E0E0E0')
            ax.spines['bottom'].set_color('#E0E0E0')
            
            # Agregar valores en las barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}',
                       ha='center', va='bottom', fontsize=10, color='#555')
            
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.comparison_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            ctk.CTkLabel(self.comparison_chart_frame, 
                        text=f"Error al generar gráfico: {str(e)}").pack()
    
    def calculate_improvements(self, strategy_stats):
        """Calcula y formatea las mejoras detectadas"""
        if len(strategy_stats) < 2:
            return "Se necesitan al menos 2 estrategias para comparar mejoras."
        
        text = "═══════════════════════════════════════════════════════════\n"
        text += "         MEJORAS DETECTADAS\n"
        text += "═══════════════════════════════════════════════════════════\n\n"
        
        # Encontrar baseline (actual)
        if 'actual' in strategy_stats.index:
            baseline_mean = strategy_stats.loc['actual', 'mean_search_time']
            baseline_p95 = strategy_stats.loc['actual', 'p95_search_time']
            baseline_error = strategy_stats.loc['actual', 'error_rate']
            
            text += f"Baseline (Actual):\n"
            text += f"  Tiempo medio: {baseline_mean:.2f} min\n"
            text += f"  P95: {baseline_p95:.2f} min\n"
            text += f"  Tasa de error: {baseline_error*100:.2f}%\n\n"
            
            text += "Comparación con otras estrategias:\n"
            text += "─" * 55 + "\n"
            
            for strategy in strategy_stats.index:
                if strategy != 'actual':
                    mean_time = strategy_stats.loc[strategy, 'mean_search_time']
                    p95_time = strategy_stats.loc[strategy, 'p95_search_time']
                    error_rate = strategy_stats.loc[strategy, 'error_rate']
                    
                    reduction_mean = ((baseline_mean - mean_time) / baseline_mean) * 100
                    reduction_p95 = ((baseline_p95 - p95_time) / baseline_p95) * 100
                    error_change = ((error_rate - baseline_error) / baseline_error) * 100
                    
                    text += f"\n{strategy.upper()}:\n"
                    text += f"  Tiempo medio: {mean_time:.2f} min"
                    if reduction_mean > 0:
                        text += f" (↓ {reduction_mean:.1f}% MEJOR)\n"
                    elif reduction_mean < 0:
                        text += f" (↑ {abs(reduction_mean):.1f}% PEOR)\n"
                    else:
                        text += " (igual)\n"
                    
                    text += f"  P95: {p95_time:.2f} min"
                    if reduction_p95 > 0:
                        text += f" (↓ {reduction_p95:.1f}% MEJOR)\n"
                    elif reduction_p95 < 0:
                        text += f" (↑ {abs(reduction_p95):.1f}% PEOR)\n"
                    else:
                        text += " (igual)\n"
                    
                    text += f"  Tasa de error: {error_rate*100:.2f}%"
                    if error_change < 0:
                        text += f" (↓ {abs(error_change):.1f}% MEJOR)\n"
                    elif error_change > 0:
                        text += f" (↑ {error_change:.1f}% PEOR)\n"
                    else:
                        text += " (igual)\n"
            
            # Encontrar mejor estrategia
            best_strategy = strategy_stats['mean_search_time'].idxmin()
            if best_strategy != 'actual':
                best_improvement = ((baseline_mean - strategy_stats.loc[best_strategy, 'mean_search_time']) / baseline_mean) * 100
                text += f"\n{'═' * 55}\n"
                text += f"MEJOR ESTRATEGIA: {best_strategy.upper()}\n"
                text += f"Reducción de tiempo: {best_improvement:.1f}%\n"
        else:
            text += "No se encontró estrategia 'actual' como baseline.\n"
            text += "Comparando todas las estrategias disponibles:\n\n"
            
            best_strategy = strategy_stats['mean_search_time'].idxmin()
            worst_strategy = strategy_stats['mean_search_time'].idxmax()
            
            text += f"Mejor: {best_strategy.upper()} ({strategy_stats.loc[best_strategy, 'mean_search_time']:.2f} min)\n"
            text += f"Peor: {worst_strategy.upper()} ({strategy_stats.loc[worst_strategy, 'mean_search_time']:.2f} min)\n"
        
        return text
    
    def format_recent_results(self, df_all):
        """Formatea los resultados recientes para mostrar"""
        if df_all.empty:
            return "No hay resultados disponibles."
        
        # Ordenar por timestamp si existe, sino por índice
        if 'timestamp' in df_all.columns:
            df_all = df_all.sort_values('timestamp', ascending=False)
        else:
            df_all = df_all.tail(10)
        
        text = "═══════════════════════════════════════════════════════════\n"
        text += "         ÚLTIMOS RESULTADOS\n"
        text += "═══════════════════════════════════════════════════════════\n\n"
        
        for idx, row in df_all.head(10).iterrows():
            text += f"Estrategia: {row.get('strategy', 'N/A').upper()}\n"
            text += f"  Tiempo medio: {row.get('mean_search_time', 0):.2f} min\n"
            text += f"  P95: {row.get('p95_search_time', 0):.2f} min\n"
            text += f"  Tasa de error: {row.get('error_rate', 0)*100:.2f}%\n"
            text += f"  Utilización: {row.get('avg_utilization', 0):.2f}%\n"
            if 'timestamp' in row:
                text += f"  Fecha: {row['timestamp'][:19]}\n"
            text += "─" * 55 + "\n\n"
        
        return text
    
    def open_notebook(self):
        """Abre el notebook de análisis"""
        notebook_path = "notebooks/analysis.ipynb"
        if os.path.exists(notebook_path):
            messagebox.showinfo("Notebook", 
                              f"El notebook está en: {os.path.abspath(notebook_path)}\n"
                              "Ábrelo con Jupyter Notebook o JupyterLab")
        else:
            messagebox.showwarning("No encontrado", 
                                 "El notebook no existe.")


if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
