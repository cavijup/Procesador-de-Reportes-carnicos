"""
pdf_generator.py - Generador de PDFs para Guías de Transporte por Ruta
Utiliza los datos procesados y la plantilla para crear PDFs individuales
Versión actualizada con nombres de comedores en archivos
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
    
    def generar_pdf_comedor_individual(self, ruta_nombre, comedor_data, programa_info):
        """
        Genera un PDF para un comedor específico
        """
        datos_comedor = {
            'comedores': [comedor_data],
            'programa_info': programa_info
        }
        
        return self.generar_pdf_individual(ruta_nombre, datos_comedor)
    
    def generar_todos_los_pdfs(self, df_procesado, modo="por_ruta"):
        """
        Genera PDFs para todas las rutas y los comprime en un ZIP
        modo: "por_ruta" o "por_comedor"
        """
        # Procesar datos
        rutas_data = self.procesar_datos_para_pdf(df_procesado)
        
        # Crear ZIP en memoria
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            total_pdfs = 0
            
            for ruta_nombre, datos_ruta in rutas_data.items():
                if modo == "por_comedor":
                    # NUEVO: Generar un PDF por cada comedor
                    for i, comedor in enumerate(datos_ruta['comedores'], 1):
                        # Crear datos de ruta con un solo comedor
                        datos_comedor_individual = {
                            'comedores': [comedor],
                            'programa_info': datos_ruta['programa_info']
                        }
                        
                        # Generar PDF para este comedor
                        pdf_buffer = self.generar_pdf_individual(ruta_nombre, datos_comedor_individual)
                        
                        # Crear nombre con comedor
                        nombre_comedor = self.limpiar_nombre_archivo(comedor['COMEDOR/ESCUELA'])
                        numero_comedor = str(i).zfill(2)  # 01, 02, 03...
                        ruta_limpia = self.limpiar_nombre_archivo(ruta_nombre)
                        nombre_pdf = f"Guia_{ruta_limpia}_{numero_comedor}_{nombre_comedor}.pdf"
                        
                        # Añadir al ZIP
                        zip_file.writestr(nombre_pdf, pdf_buffer.getvalue())
                        pdf_buffer.close()
                        total_pdfs += 1
                        
                else:
                    # Modo original: Un PDF por ruta completa
                    pdf_buffer = self.generar_pdf_individual(ruta_nombre, datos_ruta)
                    
                    # Limpiar nombre de archivo e incluir primer comedor
                    ruta_limpia = self.limpiar_nombre_archivo(ruta_nombre)
                    if datos_ruta['comedores']:
                        primer_comedor = self.limpiar_nombre_archivo(datos_ruta['comedores'][0]['COMEDOR/ESCUELA'])
                        nombre_pdf = f"Guia_{ruta_limpia}_{primer_comedor}.pdf"
                    else:
                        nombre_pdf = f"Guia_{ruta_limpia}.pdf"
                    
                    # Añadir al ZIP
                    zip_file.writestr(nombre_pdf, pdf_buffer.getvalue())
                    pdf_buffer.close()
                    total_pdfs += 1
        
        zip_buffer.seek(0)
        return zip_buffer, total_pdfs
    
    def limpiar_nombre_archivo(self, nombre):
        """
        Limpia el nombre para que sea válido como nombre de archivo
        """
        import re
        
        # Convertir a string si no lo es
        nombre = str(nombre)
        
        # Remover códigos de comedor (ej: "63/02") del inicio
        nombre = re.sub(r'^\d+\/\d+\s*', '', nombre)
        
        # Remover caracteres especiales y reemplazar espacios
        nombre_limpio = re.sub(r'[^\w\s-]', '', nombre)
        nombre_limpio = re.sub(r'[-\s]+', '_', nombre_limpio)
        
        # Remover guiones bajos al inicio y final
        nombre_limpio = nombre_limpio.strip('_')
        
        return nombre_limpio[:40]  # Limitar longitud
    
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
    
    st.info(f"📊 Se pueden generar PDFs para **{len(rutas_disponibles)} rutas** encontradas:")
    for i, ruta in enumerate(rutas_disponibles, 1):
        comedores_en_ruta = len(df_procesado[df_procesado['RUTA'] == ruta])
        st.write(f"{i}. **{ruta}** - {comedores_en_ruta} comedores")
    
    # Opciones de generación
    st.subheader("🎯 Opciones de Generación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Generación Individual**")
        generar_individual = st.selectbox(
            "Seleccionar ruta:",
            ["Seleccionar ruta..."] + list(rutas_disponibles)
        )
        
        # Si se selecciona una ruta, mostrar opciones de comedor
        if generar_individual != "Seleccionar ruta...":
            df_ruta = df_procesado[df_procesado['RUTA'] == generar_individual]
            comedores_ruta = df_ruta['COMEDOR/ESCUELA'].tolist()
            
            tipo_pdf = st.radio(
                "Tipo de PDF:",
                ["📋 Ruta completa (todos los comedores)", "🏪 Comedor individual"]
            )
            
            if tipo_pdf == "🏪 Comedor individual":
                comedor_seleccionado = st.selectbox(
                    "Seleccionar comedor:",
                    comedores_ruta
                )
            else:
                comedor_seleccionado = None
    
    with col2:
        st.markdown("**🗂️ Generación Masiva**")
        modo_masivo = st.radio(
            "Modo de generación masiva:",
            ["📋 Un PDF por ruta", "🏪 Un PDF por comedor"],
            help="Elige cómo quieres organizar los PDFs en el ZIP"
        )
        
        generar_todos = st.button(
            "🗂️ Generar TODOS los PDFs (ZIP)",
            type="primary",
            help="Genera un archivo ZIP con PDFs según el modo seleccionado"
        )
    
    # Generar PDF individual
    if generar_individual != "Seleccionar ruta...":
        if st.button(f"📄 Generar PDF"):
            with st.spinner("Generando PDF..."):
                generador = GeneradorPDFsRutas()
                rutas_data = generador.procesar_datos_para_pdf(df_procesado)
                
                if generar_individual in rutas_data:
                    if comedor_seleccionado:
                        # PDF para comedor específico
                        comedor_data = df_ruta[df_ruta['COMEDOR/ESCUELA'] == comedor_seleccionado].iloc[0].to_dict()
                        datos_comedor = {
                            'comedores': [comedor_data],
                            'programa_info': rutas_data[generar_individual]['programa_info']
                        }
                        pdf_buffer = generador.generar_pdf_individual(generar_individual, datos_comedor)
                        
                        # Nombre específico para comedor
                        ruta_limpia = generador.limpiar_nombre_archivo(generar_individual)
                        nombre_comedor = generador.limpiar_nombre_archivo(comedor_seleccionado)
                        nombre_archivo = f"Guia_{ruta_limpia}_{nombre_comedor}"
                    else:
                        # PDF para ruta completa
                        pdf_buffer = generador.generar_pdf_individual(
                            generar_individual, 
                            rutas_data[generar_individual]
                        )
                        
                        # Nombre con primer comedor
                        ruta_limpia = generador.limpiar_nombre_archivo(generar_individual)
                        primer_comedor = generador.limpiar_nombre_archivo(
                            rutas_data[generar_individual]['comedores'][0]['COMEDOR/ESCUELA']
                        )
                        nombre_archivo = f"Guia_{ruta_limpia}_{primer_comedor}"
                    
                    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label=f"📥 Descargar PDF",
                        data=pdf_buffer,
                        file_name=f"{nombre_archivo}_{fecha_actual}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success(f"✅ PDF generado exitosamente")
    
    # Generar todos los PDFs
    if generar_todos:
        with st.spinner("🔄 Generando PDFs para todas las rutas..."):
            generador = GeneradorPDFsRutas()
            
            # Determinar modo basado en selección
            modo = "por_comedor" if modo_masivo == "🏪 Un PDF por comedor" else "por_ruta"
            
            zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(df_procesado, modo=modo)
            
            fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if modo == "por_comedor":
                nombre_zip = f"Guias_Por_Comedor_{fecha_actual}.zip"
                descripcion = f"{num_pdfs} PDFs (uno por comedor)"
            else:
                nombre_zip = f"Guias_Por_Ruta_{fecha_actual}.zip"
                descripcion = f"{num_pdfs} PDFs (uno por ruta)"
            
            st.download_button(
                label=f"📦 Descargar ZIP con {descripcion}",
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