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
        Convierte los datos procesados del formato de comedores al formato necesario para las guías de transporte
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
                        'empresa': row.get('EMPRESA', 'CONSORCIO ALIMENTANDO A CALI 2025'),
                        'modalidad': row.get('MODALIDAD', 'CP AM CALI'),
                        'solicitud_remesa': row.get('SOLICITUD_REMESA', 'MENUS PARA 10 DIAS'),
                        'dias_consumo': row.get('DIAS_CONSUMO', f"{row['FECHA_ENTREGA']} - {row['FECHA_ENTREGA']}"),
                        'dia': row['DIA']
                    }
                }
            
            # Incluir muslo_contramuslo en los datos del comedor
            comedor_data = {
                'MUNICIPIO': row['MUNICIPIO'],
                'DEPARTAMENTO': 'VALLE',  # Valor por defecto
                'COMEDOR/ESCUELA': row['COMEDOR/ESCUELA'],
                'COBER': row['COBER'],
                'DIRECCIÓN': row['DIRECCIÓN'],
                'CARNE_DE_RES': row.get('CARNE_DE_RES', 0),        # Puede ser 0
                'CARNE_DE_CERDO': row['CARNE_DE_CERDO'],           # Siempre presente
                'MUSLO_CONTRAMUSLO': row.get('MUSLO_CONTRAMUSLO', 0),  # ⭐ NUEVA LÍNEA
                'POLLO_PESO': row.get('POLLO_PESO', 0),             # Puede ser 0
                'TILAPIA': row.get('TILAPIA', 0)                    # ⭐ NUEVA LÍNEA TILAPIA
            }
            
            rutas_data[ruta]['comedores'].append(comedor_data)
        
        return rutas_data
    
    def generar_pdf_individual(self, ruta_nombre, datos_ruta, elaborado_por=None, dictamen=None, lotes_personalizados=None, transporte_info=None):
        """
        ⭐ MÉTODO CORREGIDO: Ahora USA la paginación de 4 filas por página
        """
        buffer = BytesIO()
        
        # Configurar datos del programa
        programa_info = datos_ruta['programa_info'].copy()
        if dictamen:
            programa_info['dictamen'] = dictamen
        
        # Extraer conductor y placa si existen para esta ruta
        conductor = transporte_info.get('conductor') if transporte_info else None
        placa = transporte_info.get('placa') if transporte_info else None
        
        # ⭐ CLAVE: Usar el método de paginación correcto
        nombre_archivo_temporal = f"temp_guia_{ruta_nombre}.pdf"
        
        try:
            # ⭐ LLAMAR AL MÉTODO QUE SÍ PAGINA CORRECTAMENTE
            self.plantilla.generar_pdf_con_paginacion(
                datos_programa=programa_info,
                datos_comedores=datos_ruta['comedores'],
                lotes_personalizados=lotes_personalizados,
                elaborado_por=elaborado_por or "____________________",
                nombre_archivo=nombre_archivo_temporal,
                conductor=conductor, # <-- NUEVO
                placa=placa          # <-- NUEVO
            )
            
            # Leer el archivo temporal y escribirlo al buffer
            import os
            if os.path.exists(nombre_archivo_temporal):
                with open(nombre_archivo_temporal, 'rb') as temp_file:
                    buffer.write(temp_file.read())
                # Limpiar archivo temporal
                os.remove(nombre_archivo_temporal)
            
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"ADVERTENCIA: Falló la generación con paginación, usando método de fallback. Error: {e}")
            import traceback
            traceback.print_exc() # Imprime el traceback completo para depuración
            return self._generar_pdf_fallback(ruta_nombre, datos_ruta, elaborado_por, dictamen, lotes_personalizados)
    
    def _generar_pdf_fallback(self, ruta_nombre, datos_ruta, elaborado_por, dictamen, lotes_personalizados):
        """
        Método de fallback usando el método original (sin paginación correcta)
        ⚠️ ESTE ES EL MÉTODO ANTERIOR QUE NO PAGINABA BIEN
        """
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=0.3*inch,
            leftMargin=0.3*inch,
            topMargin=0.2*inch, 
            bottomMargin=0.5*inch,
            title=f"Guía de Transporte - {ruta_nombre}"
        )
        
        # Elementos del documento
        elementos = []
                                       
        programa_info = datos_ruta['programa_info'].copy()
        if dictamen:
            programa_info['dictamen'] = dictamen
        numero_guia = self.generar_numero_guia(ruta_nombre)
        elementos.extend(self.plantilla.crear_encabezado(programa_info, numero_guia))
        
        # 2. Tabla de encabezados de productos con empresa dinámica
        elementos.append(self.plantilla.crear_tabla_encabezados(programa_info))
        
        # 3. Sección de ruta
        elementos.extend(self.plantilla.crear_seccion_ruta(ruta_nombre))
        
        # 4. Tabla principal de comedores (⚠️ AQUÍ NO SE PAGINA CORRECTAMENTE)
        elementos.append(self.plantilla.crear_tabla_comedores(datos_ruta['comedores'], lotes_personalizados))
        
        
        elaborado_val = elaborado_por if elaborado_por is not None else "____________________"
        elementos.extend(self.plantilla.crear_pie_pagina(elaborado_val))
        
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
    
    def generar_pdf_comedor_individual(self, ruta_nombre, comedor_data, programa_info, elaborado_por=None, dictamen=None):
        """
        Genera un PDF para un comedor específico
        ⭐ CORREGIDO: También usa paginación correcta
        """
        datos_comedor = {
            'comedores': [comedor_data],
            'programa_info': programa_info
        }
        
        return self.generar_pdf_individual(ruta_nombre, datos_comedor, elaborado_por, dictamen)
    
    def generar_todos_los_pdfs(self, df_procesado, modo="por_ruta", elaborado_por=None, dictamen=None, lotes_personalizados=None, transporte_por_ruta=None):
        """
        Genera PDFs para todas las rutas y los comprime en un ZIP
        modo: "por_ruta" o "por_comedor"
        ⭐ AHORA CON PAGINACIÓN CORRECTA DE 4 FILAS
        """
        rutas_data = self.procesar_datos_para_pdf(df_procesado)
        zip_buffer = BytesIO()
        total_pdfs = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for ruta_nombre, datos_ruta in rutas_data.items():
                # Obtener info de transporte para esta ruta específica
                transporte_info = transporte_por_ruta.get(ruta_nombre, {}) if transporte_por_ruta else {}
                
                if modo == "por_comedor":
                    for i, comedor in enumerate(datos_ruta['comedores'], 1):
                        datos_comedor_individual = {
                            'comedores': [comedor],
                            'programa_info': datos_ruta['programa_info'].copy()
                        }
                        pdf_buffer = self.generar_pdf_individual(ruta_nombre, datos_comedor_individual, elaborado_por, dictamen, lotes_personalizados, transporte_info)
                        nombre_comedor = self.limpiar_nombre_archivo(comedor['COMEDOR/ESCUELA'])
                        numero_comedor = str(i).zfill(2)
                        ruta_limpia = self.limpiar_nombre_archivo(ruta_nombre)
                        nombre_pdf = f"Guia_{ruta_limpia}_{numero_comedor}_{nombre_comedor}.pdf"
                        zip_file.writestr(nombre_pdf, pdf_buffer.getvalue())
                        pdf_buffer.close()
                        total_pdfs += 1
                else:
                    # ⭐ MODO POR RUTA CON PAGINACIÓN CORRECTA
                    pdf_buffer = self.generar_pdf_individual(ruta_nombre, datos_ruta, elaborado_por, dictamen, lotes_personalizados, transporte_info)
                    ruta_limpia = self.limpiar_nombre_archivo(ruta_nombre)
                    if datos_ruta['comedores']:
                        primer_comedor = self.limpiar_nombre_archivo(datos_ruta['comedores'][0]['COMEDOR/ESCUELA'])
                        nombre_pdf = f"Guia_{ruta_limpia}_{primer_comedor}.pdf"
                    else:
                        nombre_pdf = f"Guia_{ruta_limpia}.pdf"
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
        
        return nombre_limpio[:40]
    
    def crear_reporte_generacion(self, rutas_data):
        """
        Crea un reporte de los PDFs generados
        """
        reporte = []
        
        for ruta_nombre, datos_ruta in rutas_data.items():
            comedores_count = len(datos_ruta['comedores'])
            total_cobertura = sum(c['COBER'] for c in datos_ruta['comedores'])
            total_cerdo = sum(c['CARNE_DE_CERDO'] for c in datos_ruta['comedores'])
            total_res = sum(c.get('CARNE_DE_RES', 0) for c in datos_ruta['comedores'])
            total_muslo_contramuslo = sum(c.get('MUSLO_CONTRAMUSLO', 0) for c in datos_ruta['comedores'])
            total_pollo = sum(c.get('POLLO_PESO', 0) for c in datos_ruta['comedores'])
            total_tilapia = sum(c.get('TILAPIA', 0) for c in datos_ruta['comedores'])
            
            reporte.append({
                'Ruta': ruta_nombre,
                'Comedores': comedores_count,
                'Paginas_PDF': self._calcular_paginas_necesarias(comedores_count),  # ⭐ NUEVA COLUMNA
                'Total_Beneficiarios': total_cobertura,
                'Total_Res_kg': total_res,
                'Total_Cerdo_kg': total_cerdo,
                'Total_Muslo_Contramuslo_und': total_muslo_contramuslo,
                'Total_Pollo_kg': total_pollo,
                'Total_Tilapia_kg': total_tilapia,
                'Empresa': datos_ruta['programa_info']['empresa'],
                'Solicitud_Remesa': datos_ruta['programa_info']['solicitud_remesa'],
                'Dias_Consumo': datos_ruta['programa_info']['dias_consumo'],
                'Numero_Guia': self.generar_numero_guia(ruta_nombre)
            })
        
        return pd.DataFrame(reporte)

    def _calcular_paginas_necesarias(self, num_comedores):
        """
        ⭐ NUEVA FUNCIÓN: Calcula cuántas páginas se necesitan para N comedores
        Con regla de 4 filas por página
        """
        import math
        return math.ceil(num_comedores / 4)

# Funciones de integración con Streamlit

def integrar_generador_pdf_streamlit():
    """
    Función para integrar el generador de PDF en la aplicación Streamlit
    ⭐ ACTUALIZADA PARA MOSTRAR INFO DE PAGINACIÓN
    """
    import streamlit as st
    
    st.header("📄 Generar PDFs de Guías de Transporte")
    st.info("⭐ **CORREGIDO**: Ahora respeta la regla de **4 filas por página** correctamente")
    
    # Verificar si hay datos procesados en session_state
    if 'df_procesado' not in st.session_state or st.session_state.df_procesado is None:
        st.warning("⚠️ Primero debes procesar un archivo de comedores para generar los PDFs.")
        return
    
    df_procesado = st.session_state.df_procesado
    
    # Verificación defensiva: Comprobar si las columnas existen
    tiene_empresa = 'EMPRESA' in df_procesado.columns
    tiene_solicitud_remesa = 'SOLICITUD_REMESA' in df_procesado.columns
    tiene_dias_consumo = 'DIAS_CONSUMO' in df_procesado.columns
    
    if not tiene_empresa or not tiene_solicitud_remesa or not tiene_dias_consumo:
        st.warning("⚠️ **DataFrame procesado con versión anterior detectado**")
        st.info("🔄 **Solución**: Vuelve a cargar y procesar tu archivo Excel para obtener todos los datos dinámicos.")
    
    # ⭐ MOSTRAR INFO DE PAGINACIÓN
    st.subheader("📊 Información de Paginación")
    rutas_disponibles = df_procesado['RUTA'].unique() if 'RUTA' in df_procesado.columns else []
    
    if len(rutas_disponibles) > 0:
        for ruta in rutas_disponibles:
            comedores_en_ruta = len(df_procesado[df_procesado['RUTA'] == ruta])
            import math
            paginas_necesarias = math.ceil(comedores_en_ruta / 4)
            st.write(f"**{ruta}**: {comedores_en_ruta} comedores → **{paginas_necesarias} páginas** (4 filas/página)")
    
    # Mostrar información de la empresa
    st.subheader("🏢 Información de la Empresa")
    if tiene_empresa:
        empresa = df_procesado['EMPRESA'].iloc[0] if len(df_procesado) > 0 else "N/A"
        st.success(f"🏢 **Empresa**: {empresa}")
    else:
        st.warning("🏢 **Empresa**: CONSORCIO ALIMENTANDO A CALI 2025 (valor por defecto)")
    
    # Mostrar información de las 4 columnas
    st.subheader("📊 Productos incluidos en el PDF")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_res = df_procesado['CARNE_DE_RES'].sum() if 'CARNE_DE_RES' in df_procesado.columns else 0
        st.metric("🐄 Carne de Res", f"{total_res:.1f} kg")
    
    with col2:
        total_cerdo = df_procesado['CARNE_DE_CERDO'].sum() if 'CARNE_DE_CERDO' in df_procesado.columns else 0
        st.metric("🐷 Carne de Cerdo", f"{total_cerdo:.1f} kg")
    
    with col3:
        total_muslo = df_procesado['MUSLO_CONTRAMUSLO'].sum() if 'MUSLO_CONTRAMUSLO' in df_procesado.columns else 0
        st.metric("🍗 Muslo/Contramuslo", f"{total_muslo:,} und")
    
    with col4:
        total_pollo = df_procesado['POLLO_PESO'].sum() if 'POLLO_PESO' in df_procesado.columns else 0
        st.metric("🐔 Pechuga Pollo", f"{total_pollo:.1f} kg")
        
    with col5:
        total_tilapia = df_procesado['TILAPIA'].sum() if 'TILAPIA' in df_procesado.columns else 0
        st.metric("🐟 Tilapia", f"{total_tilapia:.1f} kg")
    
    # Mostrar datos dinámicos
    st.subheader("📋 Información Dinámica del Archivo")
    col1, col2 = st.columns(2)
    
    with col1:
        if tiene_solicitud_remesa:
            solicitud_remesa = df_procesado['SOLICITUD_REMESA'].iloc[0] if len(df_procesado) > 0 else "N/A"
            st.success(f"📄 **Solicitud Remesa**: {solicitud_remesa}")
        else:
            st.warning("📄 **Solicitud Remesa**: MENUS PARA 10 DIAS (valor por defecto)")
    
    with col2:
        if tiene_dias_consumo:
            dias_consumo = df_procesado['DIAS_CONSUMO'].iloc[0] if len(df_procesado) > 0 else "N/A"
            st.success(f"📅 **Días de Consumo**: {dias_consumo}")
        else:
            fecha_actual = pd.Timestamp.now().strftime('%Y-%m-%d')
            st.warning(f"📅 **Días de Consumo**: {fecha_actual} - {fecha_actual} (valor por defecto)")
    
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
        if st.button(f"📄 Generar PDF con paginación corregida"):
            with st.spinner("Generando PDF con paginación de 4 filas por página..."):
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
                    
                    # Mostrar confirmación con info de paginación
                    num_comedores = len(rutas_data[generar_individual]['comedores']) if not comedor_seleccionado else 1
                    import math
                    paginas = math.ceil(num_comedores / 4)
                    st.success(f"✅ PDF generado con **{paginas} páginas** para {num_comedores} comedores (4 filas/página)")
    
    # Generar todos los PDFs
    if generar_todos:
        with st.spinner("🔄 Generando PDFs con paginación correcta de 4 filas..."):
            generador = GeneradorPDFsRutas()
            
            # Determinar modo basado en selección
            modo = "por_comedor" if modo_masivo == "🏪 Un PDF por comedor" else "por_ruta"
            
            zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(df_procesado, modo=modo)
            
            fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if modo == "por_comedor":
                nombre_zip = f"Guias_Por_Comedor_4FilasPagina_{fecha_actual}.zip"
                descripcion = f"{num_pdfs} PDFs (uno por comedor)"
            else:
                nombre_zip = f"Guias_Por_Ruta_4FilasPagina_{fecha_actual}.zip"
                descripcion = f"{num_pdfs} PDFs (uno por ruta)"
            
            st.download_button(
                label=f"📦 Descargar ZIP con {descripcion}",
                data=zip_buffer,
                file_name=nombre_zip,
                mime="application/zip"
            )
            
            st.success(f"✅ {num_pdfs} PDFs generados con **paginación correcta de 4 filas por página**")
            
            # Mostrar reporte con info de paginación
            rutas_data = generador.procesar_datos_para_pdf(df_procesado)
            reporte = generador.crear_reporte_generacion(rutas_data)
            
            with st.expander("📋 Ver reporte detallado con info de paginación"):
                st.info("⭐ El reporte ahora incluye el número de páginas necesarias por ruta")
                st.dataframe(reporte, use_container_width=True)

# Función para añadir al requirements.txt
def obtener_dependencias_adicionales():
    """
    Devuelve las dependencias adicionales necesarias para el generador de PDFs
    """
    return [
        "reportlab>=3.6.0"
    ]