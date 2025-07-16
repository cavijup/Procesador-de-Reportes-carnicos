# 🍽️ Procesador de Reportes - Comedores Comunitarios

Aplicación web desarrollada con Streamlit para procesar automáticamente los archivos Excel de reportes de comedores comunitarios y convertirlos en una base de datos estructurada.

## 🚀 Características

- **Carga automática** de archivos Excel de reportes
- **Procesamiento inteligente** que detecta rutas y comedores automáticamente
- **Normalización de datos** en formato de base de datos relacional
- **Visualización interactiva** con métricas y filtros
- **Descarga en Excel** con múltiples hojas de análisis
- **Validación de datos** y manejo de errores

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- Las librerías especificadas en `requirements.txt`

## 🛠️ Instalación

### 1. Clonar o descargar los archivos
Guarda los siguientes archivos en una carpeta:
- `app.py` (código principal)
- `requirements.txt` (dependencias)
- `README.md` (este archivo)

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
```

### 3. Activar el entorno virtual

**En Windows:**
```bash
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### 1. Ejecutar la aplicación
```bash
streamlit run app.py
```

### 2. Abrir en el navegador
La aplicación se abrirá automáticamente en: `http://localhost:8501`

### 3. Usar la aplicación
1. **Cargar archivo**: Sube el archivo Excel descargado del programa de comedores
2. **Procesar datos**: La aplicación detectará automáticamente las rutas y comedores
3. **Revisar resultados**: Visualiza las métricas y datos procesados
4. **Descargar**: Obtén el archivo Excel normalizado con 3 hojas de análisis

## 📊 Estructura del Archivo de Salida

El archivo Excel descargado contiene 3 hojas:

### 1. **Comedores_Procesados**
Datos principales con columnas:
- `PROGRAMA`: Nombre del programa
- `FECHA_ENTREGA`: Fecha de entrega
- `DIA`: Día de la operación  
- `RUTA`: Identificador de la ruta
- `N°`: Número del comedor en la ruta
- `MUNICIPIO`: Municipio (CALI)
- `COMEDOR/ESCUELA`: Nombre del comedor
- `COBER`: Número de beneficiarios
- `DIRECCIÓN`: Dirección física
- `CARNE_DE_CERDO`: Kilogramos de carne de cerdo
- `POLLO_UNIDADES`: Unidades de pollo
- `POLLO_PESO`: Kilogramos de pollo

### 2. **Resumen**
Estadísticas generales del procesamiento

### 3. **Analisis_Por_Ruta**
Agregaciones y totales por cada ruta

## 🔧 Solución de Problemas

### Error: "No se pudieron procesar los datos"
- Verifica que el archivo sea un reporte válido de comedores
- Asegúrate de que contenga la estructura de rutas (DIA X - RUTA Y)
- Intenta descargar nuevamente el archivo del programa original

### Error de librerías
```bash
pip install --upgrade streamlit pandas openpyxl
```

### Puerto ocupado
Si el puerto 8501 está ocupado:
```bash
streamlit run app.py --server.port 8502
```

## 📈 Funcionalidades Avanzadas

### Filtros
- Filtro por rutas específicas
- Opción para mostrar todas las rutas
- Vista de métricas en tiempo real

### Validaciones
- Detección automática de programa y fecha
- Limpieza de datos numéricos
- Manejo de valores faltantes

### Análisis
- Métricas por ruta
- Totales generales
- Distribución de beneficiarios
- Control de materias primas

## 🆘 Soporte

Si encuentras algún problema:

1. **Verifica la estructura del archivo Excel** que debe contener bloques organizados por rutas
2. **Revisa los logs** en la consola donde ejecutas streamlit
3. **Intenta con diferentes archivos** para identificar el patrón del error

## 📝 Notas Importantes

- La aplicación procesa archivos con la estructura específica de comedores comunitarios
- Los datos se validan automáticamente durante el procesamiento  
- El archivo de salida está optimizado para análisis posterior
- La aplicación maneja múltiples rutas y detecta automáticamente la estructura

## 🔄 Versiones

- **v1.0**: Versión inicial con procesamiento básico
- Funcionalidad completa de carga, procesamiento y descarga
- Interfaz web intuitiva con Streamlit
- Validación robusta de datos