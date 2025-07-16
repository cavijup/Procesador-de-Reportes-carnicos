"""
pdf_generator.py - Generador de PDFs para Guías de Transporte por Ruta
Utiliza los datos procesados y la plantilla para crear PDFs individuales
"""

import pandas as pd
from reportlab.platypus import SimpleDocTemplate, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO
import zipfile
from datetime import datetime
from template import PlantillaGuiaTransporte

class GeneradorPDFsRutas:
    def __init__(self):
        self.plantilla = PlantillaGuiaTransporte()
        
    def procesar_datos_para_pdf(self, df_procesado):
        """
        Convierte los datos procesados del formato de comedores
        al formato necesario para las guías de transporte
        """
        # Agrupar por ruta
        rutas_data = {}
        
        for _, row in df_procesado.iterrows():
            ruta = row['RUTA']
            if ruta not in rutas_data:
                rutas_data[ruta] = {
                    'comedores': [],
                    'programa_info': {
                        'programa': row['PROGRAMA'],
                        'fecha_entrega': row['FECHA_ENTREGA'],
                        'dia': row['DIA']
                    }
                }
            
            # Convertir datos del comedor al formato de la guía
            comedor_data = {
                'MUNICIPIO': row['MUNICIPIO'],
                'DEPARTAMENTO': 'VALLE',  # Valor por defecto
                'COMEDOR/ESCUELA': row['COMEDOR/ESCUELA'],
                'COBER': row['COBER'],
                'DIRECCIÓN': row['DIRECCIÓN'],
                'CARNE_DE_RES': 0,  # No disponible en formato original, se puede calcular
                'CARNE_DE_CERDO': row['CARNE_DE_CERDO'],
                'POLLO_PESO': row['POLLO_PESO']
            }
            
            rutas_data[ruta]['comedores'].append(comedor_data)
        
        return rutas_data
    
    def generar_pdf_individual(self, ruta_nombre, datos_ruta):
        """
        Genera un PDF individual para una ruta específica
        """
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=0.5*inch, 
            leftMargin=0.5*inch,
            topMargin=0.5*inch, 
            bottomMargin=0.5*inch,
            title=f"Guía de Transporte - {ruta_nombre}"
        )
        
        # Elementos del documento
        elementos = []
        
        # 1. Encabezado
        programa_info = datos_ruta['programa_info']
        
        # Generar número de guía único basado en ruta
        numero_guia = self.generar_numero_guia(ruta_nombre)
        
        elementos.extend(self.plantilla.crear_encabezado(programa_info, numero_guia))
        
        # 2. Tabla de encabezados de productos
        elementos.append(self.plantilla.crear_tabla_encabezados())
        
        # 3. Sección de ruta
        elementos.extend(self.plantilla.crear_seccion_ruta(ruta_nombre))
        
        # 4. Tabla principal de comedores
        elementos.append(self.plantilla.crear_tabla_comedores(datos_ruta['comedores']))
        
        # 5. Sección adicional
        elementos.extend(self.plantilla.crear_seccion_adicional())
        
        # 6. Pie de página
        elementos.extend(self.plantilla.crear_pie_pagina())
        
        # Construir PDF
        doc.build(elementos)
        buffer.seek(0)
        
        return buffer
    
    def generar_numero_guia(self, ruta_nombre):
        """
        Genera un número de guía único basado en el nombre de la ruta
        """
        # Extraer número de la ruta si existe
        import re
        match = re.search(r'(\d+)', ruta_nombre)
        if match:
            numero_ruta = match.group(1).zfill(3)
        else:
            # Si no hay número, usar hash de la ruta
            numero_ruta = str(abs(hash(ruta_nombre)) % 1000).zfill(3)
        
        fecha_actual = datetime.now().strftime('%m%d')
        return f"{fecha_actual}-{numero_ruta}"
    
    def generar_todos_los_pdfs(self, df_procesado):
        """
        Genera PDFs para todas las rutas y los comprime en un ZIP
        """
        # Procesar datos
        rutas_data = self.procesar_datos_para_pdf(df_procesado)
        
        # Crear ZIP en memoria
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for ruta_nombre, datos_ruta in rutas_data.items():
                # Generar PDF para esta ruta
                pdf_buffer = self.generar_pdf_individual(ruta_nombre, datos_ruta)
                
                # Limpiar nombre de archivo
                nombre_archivo = self.limpiar_nombre_archivo(ruta_nombre)
                nombre_pdf = f"Guia_Transporte_{nombre_archivo}.pdf"
                
                # Añadir al ZIP
                zip_file.writestr(nombre_pdf, pdf_buffer.getvalue())
                pdf_buffer.close()
        
        zip_buffer.seek(0)
        return zip_buffer, len(rutas_data)
    
    def limpiar_nombre_archivo(self, nombre):
        """
        Limpia el nombre para que sea válido como nombre de archivo
        """
        import re
        # Remover caracteres especiales y reemplazar espacios
        nombre_limpio = re.sub(r'[^\w\s-]', '', nombre)
        nombre_limpio = re.sub(r'[-\s]+', '_', nombre_limpio)
        return nombre_limpio[:50]  # Limitar longitud
    
    def crear_reporte_generacion(self, rutas_data):
        """
        Crea un reporte de los PDFs generados
        """
        reporte = []
        
        for ruta_nombre, datos_ruta in rutas_data.items():
            comedores_count = len(datos_ruta['comedores'])
            total_cobertura = sum(c['COBER'] for c in datos_ruta['comedores'])
            total_cerdo = sum(c['CARNE_DE_CERDO'] for c in datos_ruta['comedores'])
            total_pollo = sum(c['POLLO_PESO'] for c in datos_ruta['comedores'])
            
            reporte.append({
                'Ruta': ruta_nombre,
                'Comedores': comedores_count,
                'Total_Beneficiarios': total_cobertura,
                'Total_Cerdo_kg': total_cerdo,
                'Total_Pollo_kg': total_pollo,
                'Numero_Guia': self.generar_numero_guia(ruta_nombre)
            })
        
        return pd.DataFrame(reporte)

# Funciones de integración con Streamlit

def integrar_generador_pdf_streamlit():
    """
    Función para integrar el generador de PDF en la aplicación Streamlit
    """
    import streamlit as st
    
    st.header("📄 Generar PDFs de Guías de Transporte")
    
    # Verificar si hay datos procesados en session_state
    if 'df_procesado' not in st.session_state or st.session_state.df_procesado is None:
        st.warning("⚠️ Primero debes procesar un archivo de comedores para generar los PDFs.")
        return
    
    df_procesado = st.session_state.df_procesado
    
    # Mostrar información previa
    rutas_disponibles = df_procesado['RUTA'].unique()
    
    st.info(f"📊 Se generarán PDFs para **{len(rutas_disponibles)} rutas** encontradas:")
    for i, ruta in enumerate(rutas_disponibles, 1):
        comedores_en_ruta = len(df_procesado[df_procesado['RUTA'] == ruta])
        st.write(f"{i}. **{ruta}** - {comedores_en_ruta} comedores")
    
    # Opciones de generación
    col1, col2 = st.columns(2)
    
    with col1:
        generar_individual = st.selectbox(
            "Generar PDF individual:",
            ["Seleccionar ruta..."] + list(rutas_disponibles)
        )
    
    with col2:
        generar_todos = st.button(
            "🗂️ Generar TODOS los PDFs (ZIP)",
            type="primary",
            help="Genera un archivo ZIP con PDFs de todas las rutas"
        )
    
    # Generar PDF individual
    if generar_individual != "Seleccionar ruta...":
        if st.button(f"📄 Generar PDF para {generar_individual}"):
            with st.spinner(f"Generando PDF para {generar_individual}..."):
                generador = GeneradorPDFsRutas()
                rutas_data = generador.procesar_datos_para_pdf(df_procesado)
                
                if generar_individual in rutas_data:
                    pdf_buffer = generador.generar_pdf_individual(
                        generar_individual, 
                        rutas_data[generar_individual]
                    )
                    
                    nombre_archivo = generador.limpiar_nombre_archivo(generar_individual)
                    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label=f"📥 Descargar PDF - {generar_individual}",
                        data=pdf_buffer,
                        file_name=f"Guia_Transporte_{nombre_archivo}_{fecha_actual}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success(f"✅ PDF generado para {generar_individual}")
    
    # Generar todos los PDFs
    if generar_todos:
        with st.spinner("🔄 Generando PDFs para todas las rutas..."):
            generador = GeneradorPDFsRutas()
            zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(df_procesado)
            
            fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_zip = f"Guias_Transporte_Todas_Rutas_{fecha_actual}.zip"
            
            st.download_button(
                label=f"📦 Descargar ZIP con {num_pdfs} PDFs",
                data=zip_buffer,
                file_name=nombre_zip,
                mime="application/zip"
            )
            
            st.success(f"✅ {num_pdfs} PDFs generados y comprimidos en ZIP")
            
            # Mostrar reporte
            rutas_data = generador.procesar_datos_para_pdf(df_procesado)
            reporte = generador.crear_reporte_generacion(rutas_data)
            
            with st.expander("📋 Ver reporte detallado"):
                st.dataframe(reporte, use_container_width=True)

# Función para añadir al requirements.txt
def obtener_dependencias_adicionales():
    """
    Devuelve las dependencias adicionales necesarias para el generador de PDFs
    """
    return [
        "reportlab>=3.6.0"
    ]