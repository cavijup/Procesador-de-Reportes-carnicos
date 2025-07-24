#!/usr/bin/env python3
"""
Script de configuración inicial para la aplicación de Comedores
"""

import os
import sys

def crear_estructura_directorios():
    """Crea la estructura de directorios necesaria"""
    directorios = [
        '.streamlit',
        'imagenes'
    ]
    
    for directorio in directorios:
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            print(f"✅ Directorio creado: {directorio}")
        else:
            print(f"📁 Directorio existe: {directorio}")

def crear_archivo_secrets_template():
    """Crea el archivo template de secrets si no existe"""
    template_path = '.streamlit/secrets.toml.template'
    secrets_path = '.streamlit/secrets.toml'
    
    template_content = """# .streamlit/secrets.toml
# Configuración para envío de correos

[gmail]
email = "tu_email@gmail.com"
app_password = "tu_contraseña_de_aplicacion"

# Para obtener una contraseña de aplicación:
# 1. Ve a https://myaccount.google.com/security
# 2. Activa la verificación en 2 pasos
# 3. Ve a "Contraseñas de aplicaciones"
# 4. Genera una nueva para "Correo"
# 5. Reemplaza "tu_contraseña_de_aplicacion" con la contraseña generada
"""
    
    # Crear template
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    print(f"✅ Template creado: {template_path}")
    
    # Crear archivo secrets si no existe
    if not os.path.exists(secrets_path):
        with open(secrets_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✅ Archivo secrets creado: {secrets_path}")
        print("⚠️  IMPORTANTE: Configura tus credenciales en .streamlit/secrets.toml")
    else:
        print(f"📁 Archivo secrets existe: {secrets_path}")

def crear_gitignore():
    """Crea archivo .gitignore para proteger archivos sensibles"""
    gitignore_content = """# Archivos de configuración sensible
.streamlit/secrets.toml
secrets.toml

# Archivos temporales de PDF
*.pdf
temp_*.pdf

# Imágenes de firmas (privadas)
imagenes/*.png
imagenes/*.jpg
imagenes/*.jpeg

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Excel temporales
~$*.xlsx
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ Archivo .gitignore creado")

def verificar_dependencias():
    """Verifica que las dependencias estén instaladas"""
    required_packages = [
        'streamlit',
        'pandas',
        'openpyxl',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} NO instalado")
    
    if missing_packages:
        print(f"\n⚠️  Instala los paquetes faltantes con:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def crear_imagenes_ejemplo():
    """Crea archivos de ejemplo para las imágenes de firmas"""
    nombres_ejemplo = [
        "Shirley Paola Ibarra",
        "Jeferson Soto", 
        "Alexandra Luna",
        "Alexander Molina",
        "Leidy Guzman",
        "Andres Montenegro",
        "Isabela Pantoja",
        "Luis Rodriguez",
        "SANDRA HENAO TORO"
    ]
    
    readme_imagenes = """# Carpeta de Imágenes de Firmas

Esta carpeta debe contener las imágenes de firmas de los supervisores.

## Formato requerido:
- **Nombre**: Nombre completo de la persona (ej: "Shirley Paola Ibarra.png")
- **Formato**: PNG, JPG, JPEG o GIF
- **Tamaño recomendado**: 200x100 píxeles
- **Fondo**: Transparente (PNG recomendado)

## Archivos necesarios:
"""
    
    for nombre in nombres_ejemplo:
        readme_imagenes += f"- {nombre}.png\n"
    
    readme_imagenes += """
## Nota:
Si no existe la imagen para una persona, se mostrará una línea de firma vacía.
"""
    
    with open('imagenes/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_imagenes)
    
    print("✅ README de imágenes creado")

def main():
    """Función principal de configuración"""
    print("🚀 Configurando aplicación de Comedores Comunitarios...\n")
    
    # 1. Crear estructura de directorios
    print("1️⃣ Creando estructura de directorios...")
    crear_estructura_directorios()
    print()
    
    # 2. Crear archivo de secrets
    print("2️⃣ Configurando archivo de secrets...")
    crear_archivo_secrets_template()
    print()
    
    # 3. Crear .gitignore
    print("3️⃣ Creando .gitignore...")
    crear_gitignore()
    print()
    
    # 4. Verificar dependencias
    print("4️⃣ Verificando dependencias...")
    dependencias_ok = verificar_dependencias()
    print()
    
    # 5. Crear documentación de imágenes
    print("5️⃣ Configurando carpeta de imágenes...")
    crear_imagenes_ejemplo()
    print()
    
    # Resumen final
    print("🏁 Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Configura tus credenciales en .streamlit/secrets.toml")
    print("2. Agrega las imágenes de firmas en la carpeta imagenes/")
    print("3. Ejecuta: streamlit run app.py")
    
    if not dependencias_ok:
        print("\n⚠️  Recuerda instalar las dependencias faltantes antes de ejecutar la aplicación")

if __name__ == "__main__":
    main()