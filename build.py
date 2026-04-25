import PyInstaller.__main__
import customtkinter
import os

# Encontra automaticamente a pasta onde o CustomTkinter está instalado
ctk_path = os.path.dirname(customtkinter.__file__)

print("Iniciando a criação do arquivo executável...")

PyInstaller.__main__.run([
    'main.py',                           # O seu arquivo principal
    '--name=Buscador de Comentarios',    # O nome do seu aplicativo
    '--noconfirm',                       # Substitui versões antigas sem perguntar
    '--onedir',                          # Cria uma pasta com o app (abre mais rápido que --onefile)
    '--console',                         # MANTÉM o terminal negro aberto (Vital para você ver os avisos de Login)
    f'--add-data={ctk_path};customtkinter/', # Inclui os temas visuais do aplicativo
])

print("\nConcluído! Procure pela pasta 'dist' no seu projeto.")