import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
import re
from datetime import datetime

# Importar los nuevos módulos para PDFs
try:
    from pdf_generator import integrar_generador_pdf_streamlit
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# Configuración de la página
st.set_page_config(
    page_title="Procesador de Reportes carnicos - programas chvs",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def extraer_informacion_encabezado(df_raw):
    """
    Extrae información del programa y fecha del encabezado del archivo
    """
    programa = "COMEDORES COMUNITARIOS CALI 2025"  # Valor por defecto
    fecha_entrega = None
    
    # Buscar información en las primeras filas
    for i in range(min(10, len(df_raw))):
        fila = df_raw.iloc[i, 0] if not pd.isna(df_raw.iloc[i, 0]) else ""
        fila_str = str(fila).upper()
        
        # Buscar programa
        if "COMEDORES COMUNITARIOS" in fila_str:
            programa = fila_str
            
        # Buscar fecha de entrega
        if "ENTREGA" in fila_str:
            # Buscar patrón de fecha
            fecha_match = re.search(r'(\d{1,2})\s+(\w+)', fila_str)
            if fecha_match:
                dia = fecha_match.group(1)
                mes = fecha_match.group(2)
                
                # Convertir mes a número
                meses = {
                    'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04',
                    'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08',
                    'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'
                }
                
                if mes in meses:
                    fecha_entrega = f"2025-{meses[mes]}-{dia.zfill(2)}"
                    
    return programa, fecha_entrega

def procesar_archivo_comedores(archivo):
    """
    Procesa el archivo Excel y lo convierte en DataFrame normalizado
    """
    try:
        # Leer archivo Excel
        df_raw = pd.read_excel(archivo, header=None)
        
        # Extraer información del encabezado
        programa, fecha_entrega = extraer_informacion_encabezado(df_raw)
        
        # Lista para almacenar todos los registros
        registros_consolidados = []
        
        # Buscar bloques de rutas
        i = 0
        while i < len(df_raw):
            try:
                celda = str(df_raw.iloc[i, 0]).strip()
                
                # Detectar inicio de ruta
                if "DIA" in celda and "RUTA" in celda and "TOTAL" not in celda:
                    ruta_completa = celda
                    dia = ruta_completa.split(' - ')[0] if ' - ' in ruta_completa else "DIA 7"
                    ruta = ruta_completa.split(' - ')[1] if ' - ' in ruta_completa else celda
                    
                    # Buscar encabezados de la tabla
                    for j in range(i + 1, min(i + 10, len(df_raw))):
                        try:
                            if (not pd.isna(df_raw.iloc[j, 0]) and 
                                str(df_raw.iloc[j, 0]).strip() == "N°" and
                                not pd.isna(df_raw.iloc[j, 1]) and 
                                "MUNICIPIO" in str(df_raw.iloc[j, 1]).upper()):
                                
                                # Extraer datos de comedores
                                for k in range(j + 1, len(df_raw)):
                                    try:
                                        primera_celda = df_raw.iloc[k, 0]
                                        
                                        # Si es un número, es un comedor
                                        if (not pd.isna(primera_celda) and 
                                            isinstance(primera_celda, (int, float)) and
                                            not pd.isna(df_raw.iloc[k, 1]) and
                                            not pd.isna(df_raw.iloc[k, 2])):
                                            
                                            registro = {
                                                'PROGRAMA': programa,
                                                'FECHA_ENTREGA': fecha_entrega or "2025-07-15",
                                                'DIA': dia,
                                                'RUTA': ruta,
                                                'N°': int(primera_celda),
                                                'MUNICIPIO': str(df_raw.iloc[k, 1]).strip(),
                                                'COMEDOR/ESCUELA': str(df_raw.iloc[k, 2]).strip(),
                                                'COBER': df_raw.iloc[k, 3] if not pd.isna(df_raw.iloc[k, 3]) else 0,
                                                'DIRECCIÓN': str(df_raw.iloc[k, 4]).strip() if not pd.isna(df_raw.iloc[k, 4]) else "",
                                                'CARNE_DE_CERDO': df_raw.iloc[k, 5] if not pd.isna(df_raw.iloc[k, 5]) else 0,
                                                'POLLO_UNIDADES': df_raw.iloc[k, 6] if not pd.isna(df_raw.iloc[k, 6]) else 0,
                                                'POLLO_PESO': df_raw.iloc[k, 7] if not pd.isna(df_raw.iloc[k, 7]) else 0
                                            }
                                            
                                            registros_consolidados.append(registro)
                                            
                                        # Si encontramos "TOTAL" o nueva "RUTA", salir del bucle
                                        elif (not pd.isna(primera_celda) and 
                                              ("TOTAL" in str(primera_celda).upper() or 
                                               "RUTA" in str(primera_celda).upper())):
                                            i = k - 1
                                            break
                                            
                                    except Exception as e:
                                        continue
                                        
                                break
                                
                        except Exception as e:
                            continue
                            
            except Exception as e:
                pass
                
            i += 1
            
        # Crear DataFrame
        if registros_consolidados:
            df_final = pd.DataFrame(registros_consolidados)
            
            # Limpiar y validar datos
            df_final['COBER'] = pd.to_numeric(df_final['COBER'], errors='coerce').fillna(0).astype(int)
            df_final['CARNE_DE_CERDO'] = pd.to_numeric(df_final['CARNE_DE_CERDO'], errors='coerce').fillna(0).astype(int)
            df_final['POLLO_UNIDADES'] = pd.to_numeric(df_final['POLLO_UNIDADES'], errors='coerce').fillna(0).astype(int)
            df_final['POLLO_PESO'] = pd.to_numeric(df_final['POLLO_PESO'], errors='coerce').fillna(0).astype(int)
            
            return df_final, len(registros_consolidados)
        else:
            return None, 0
            
    except Exception as e:
        st.error(f"Error procesando el archivo: {str(e)}")
        return None, 0

def crear_excel_descarga(df):
    """
    Crea un archivo Excel optimizado para descarga
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja principal con datos
        df.to_excel(writer, sheet_name='Comedores_Procesados', index=False)
        
        # Hoja de resumen
        resumen_data = {
            'Métrica': [
                'Total Comedores',
                'Total Beneficiarios', 
                'Total Carne de Cerdo (kg)',
                'Total Pollo Unidades',
                'Total Pollo Peso (kg)',
                'Total Rutas',
                'Fecha de Procesamiento'
            ],
            'Valor': [
                len(df),
                df['COBER'].sum(),
                df['CARNE_DE_CERDO'].sum(),
                df['POLLO_UNIDADES'].sum(),
                df['POLLO_PESO'].sum(),
                df['RUTA'].nunique(),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Hoja de análisis por ruta
        df_por_ruta = df.groupby('RUTA').agg({
            'COMEDOR/ESCUELA': 'count',
            'COBER': 'sum',
            'CARNE_DE_CERDO': 'sum',
            'POLLO_UNIDADES': 'sum',
            'POLLO_PESO': 'sum'
        }).round(2)
        
        df_por_ruta.columns = ['Comedores', 'Total_Beneficiarios', 'Total_Cerdo_kg', 'Total_Pollo_Und', 'Total_Pollo_kg']
        df_por_ruta.to_excel(writer, sheet_name='Analisis_Por_Ruta')
        
    output.seek(0)
    return output

def main():
    # Título principal
    st.title("🍽️ Procesador de Reportes - Comedores Comunitarios")
    st.markdown("---")
    
    # Sidebar con información
    with st.sidebar:
        st.header("📋 Información")
        st.markdown("""
        **¿Qué hace esta aplicación?**
        
        1. **Carga** archivos Excel de reportes de comedores
        2. **Procesa** y normaliza los datos automáticamente  
        3. **Genera** un DataFrame estructurado
        4. **Permite descargar** el resultado en Excel
        5. **🆕 Genera PDFs** de guías de transporte por ruta
        
        **Formatos soportados:**
        - Archivos .xlsx con estructura de rutas
        - Reportes de comedores comunitarios
        """)
        
        # Mostrar estado de PDFs
        if PDF_DISPONIBLE:
            st.success("✅ Generación de PDFs habilitada")
        else:
            st.warning("⚠️ PDFs no disponibles\n\nInstala: `pip install reportlab`")
        
        st.markdown("---")
        st.markdown("**Desarrollado para:**  \nComedores Comunitarios Cali 2025")
    
    # Crear tabs para organizar la funcionalidad
    tab1, tab2 = st.tabs(["📊 Procesar Datos", "📄 Generar PDFs"])
    
    with tab1:
        # Área principal de procesamiento
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("📁 Cargar Archivo")
            archivo_subido = st.file_uploader(
                "Selecciona el archivo Excel del reporte de comedores",
                type=['xlsx', 'xls'],
                help="Archivo descargado del programa de comedores comunitarios"
            )
            
        with col2:
            st.header("📊 Estado")
            if archivo_subido is None:
                st.info("Esperando archivo...")
            else:
                st.success("Archivo cargado ✅")
        
        # Procesar archivo si se ha subido
        if archivo_subido is not None:
            with st.spinner("🔄 Procesando archivo..."):
                df_procesado, num_registros = procesar_archivo_comedores(archivo_subido)
                
            if df_procesado is not None and num_registros > 0:
                # Guardar en session_state para uso en tab de PDFs
                st.session_state.df_procesado = df_procesado
                
                st.success(f"✅ Archivo procesado exitosamente! {num_registros} comedores encontrados")
                
                # Mostrar métricas principales
                st.header("📊 Resumen del Procesamiento")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Comedores", len(df_procesado))
                with col2:
                    st.metric("Beneficiarios", f"{df_procesado['COBER'].sum():,}")
                with col3:
                    st.metric("Rutas", df_procesado['RUTA'].nunique())
                with col4:
                    st.metric("Carne Cerdo (kg)", f"{df_procesado['CARNE_DE_CERDO'].sum():,}")
                with col5:
                    st.metric("Pollo Total (kg)", f"{df_procesado['POLLO_PESO'].sum():,}")
                
                # Mostrar DataFrame
                st.header("📋 Datos Procesados")
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    rutas_seleccionadas = st.multiselect(
                        "Filtrar por rutas:",
                        options=sorted(df_procesado['RUTA'].unique()),
                        default=sorted(df_procesado['RUTA'].unique())[:5]  # Mostrar solo las primeras 5
                    )
                
                with col2:
                    mostrar_todos = st.checkbox("Mostrar todas las rutas", value=False)
                    
                if mostrar_todos:
                    df_mostrar = df_procesado
                else:
                    df_mostrar = df_procesado[df_procesado['RUTA'].isin(rutas_seleccionadas)]
                
                # Mostrar tabla
                st.dataframe(
                    df_mostrar, 
                    use_container_width=True,
                    height=400
                )
                
                # Análisis por ruta
                st.header("📈 Análisis por Ruta")
                df_analisis = df_procesado.groupby('RUTA').agg({
                    'COMEDOR/ESCUELA': 'count',
                    'COBER': 'sum',
                    'CARNE_DE_CERDO': 'sum',
                    'POLLO_UNIDADES': 'sum',
                    'POLLO_PESO': 'sum'
                }).round(2)
                
                df_analisis.columns = ['Comedores', 'Beneficiarios', 'Cerdo_kg', 'Pollo_Und', 'Pollo_kg']
                
                st.dataframe(df_analisis, use_container_width=True)
                
                # Botón de descarga
                st.header("💾 Descargar Resultado")
                
                archivo_excel = crear_excel_descarga(df_procesado)
                fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f"comedores_procesados_{fecha_actual}.xlsx"
                
                st.download_button(
                    label="📥 Descargar Excel Procesado",
                    data=archivo_excel,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descarga el archivo Excel con los datos normalizados y análisis"
                )
                
                # Información adicional
                with st.expander("ℹ️ Información del archivo descargado"):
                    st.markdown("""
                    **El archivo Excel contiene 3 hojas:**
                    
                    1. **Comedores_Procesados**: Datos principales normalizados
                    2. **Resumen**: Estadísticas generales 
                    3. **Analisis_Por_Ruta**: Agregaciones por ruta
                    
                    **Estructura de la base de datos:**
                    - Cada fila = 1 comedor único
                    - Columnas normalizadas con nombres descriptivos
                    - Datos listos para análisis o integración
                    """)
                    
            else:
                st.error("❌ No se pudieron procesar los datos del archivo. Verifica que sea un reporte válido de comedores comunitarios.")
                
                with st.expander("🔧 Ayuda para resolución de problemas"):
                    st.markdown("""
                    **Posibles causas del error:**
                    
                    1. **Formato incorrecto**: El archivo debe ser un reporte de comedores con estructura de rutas
                    2. **Archivo dañado**: Intenta descargar nuevamente el archivo del programa original
                    3. **Estructura diferente**: El archivo debe contener bloques de "DIA X - RUTA Y"
                    
                    **Verifica que el archivo contenga:**
                    - Información del programa en el encabezado
                    - Bloques organizados por rutas
                    - Tablas con comedores y sus datos
                    """)
    
    with tab2:
        # Tab para generación de PDFs
        if PDF_DISPONIBLE:
            integrar_generador_pdf_streamlit()
        else:
            st.error("🚫 **Funcionalidad de PDFs no disponible**")
            st.markdown("""
            Para habilitar la generación de PDFs, instala las dependencias necesarias:
            
            ```bash
            pip install reportlab
            ```
            
            Luego reinicia la aplicación.
            """)
            
            st.info("💡 Los PDFs generarán guías de transporte individuales por ruta, basadas en el formato oficial.")

if __name__ == "__main__":
    main()