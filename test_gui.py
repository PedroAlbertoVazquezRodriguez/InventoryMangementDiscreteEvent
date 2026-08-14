"""
Script de prueba para verificar que CustomTkinter funciona
"""
import customtkinter as ctk

print("Probando CustomTkinter...")

try:
    # Configurar tema
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Crear ventana de prueba
    root = ctk.CTk()
    root.title("Prueba GUI")
    root.geometry("400x300")
    
    # Agregar un label
    label = ctk.CTkLabel(root, text="¡CustomTkinter funciona correctamente!", 
                        font=ctk.CTkFont(size=16))
    label.pack(pady=50)
    
    # Botón de salir
    button = ctk.CTkButton(root, text="Cerrar", command=root.destroy)
    button.pack(pady=20)
    
    print("Ventana creada. Deberías ver una ventana ahora.")
    print("Si no ves la ventana, puede haber un problema con el display.")
    
    root.mainloop()
    print("Ventana cerrada.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    input("Presiona Enter para salir...")


