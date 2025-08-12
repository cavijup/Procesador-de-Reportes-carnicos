"""
🍽️ APP.PY - INTERFAZ PRINCIPAL SIMPLIFICADA
Aplicación Streamlit para procesamiento de reportes de comedores comunitarios
Versión 2.0 - Arquitectura modular con extracción estructurada
"""

import streamlit as st
from datetime import datetime
from logger_config import logger

# 📦 IMPORTAR MÓDULOS LOCALES
try:
    from excel_processor import ExcelProcessor
    from data_extractor import DataExtractor
    from utils import UtilsHelper, FileValidator
    PROCESAMIENTO_DISPONIBLE = True
except ImportError as e:
    st.error(f"❌ Error importando módulos de procesamiento: {e}")
    PROCESAMIENTO_DISPONIBLE = False

# 📄 IMPORTAR MÓDULOS DE PDF
try:
    from pdf_generator import GeneradorPDFsRutas
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# 📧 IMPORTAR MÓDULOS DE EMAIL
try:
    from email_sender import enviar_correo_con_adjuntos
    EMAIL_DISPONIBLE = True
except ImportError:
    EMAIL_DISPONIBLE = False

# 📊 IMPORTAR MÓDULOS DE GOOGLE SHEETS
try:
    from google_sheets_handler import GoogleSheetsHandler
    GDRIVE_DISPONIBLE = True
except ImportError:
    GDRIVE_DISPONIBLE = False

# 🎨 CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Procesador de Reportes v2.0 - CHVS",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def mostrar_sidebar():
    """
    📋 Muestra información en la barra lateral
    """
    with st.sidebar:
        st.header("📋 Procesador v2.0")
        
        st.markdown("""
        **🎯 Nuevas características:**
        
        ✅ **Extracción estructurada**
        - Programa, Empresa, Modalidad (separados)
        - Solicitud de Remesa (fila 8)
        - Días de Consumo (fila 9)
        
        ✅ **Tipos soportados:**
        - Comedores Comunitarios
        - Consorcio Alimentando a Cali
        - Valle Solidario Buga
        - Valle Solidario Yumbo
        
        ✅ **Productos detectados:**
        - 🐷 Carne de Cerdo (KG/B X 1000)
        - 🐄 Carne de Res (KG)
        - 🍗 Muslo/Contramuslo (UND)
        - 🐔 Pechuga Pollo (KG)
        """)
        
        st.markdown("---")
        
        # Estado de módulos
        st.subheader("🔧 Estado de Módulos")
        if PROCESAMIENTO_DISPONIBLE:
            st.success("✅ Procesamiento habilitado")
        else:
            st.error("❌ Error en procesamiento")
            
        if PDF_DISPONIBLE:
            st.success("✅ Generación de PDFs")
        else:
            st.warning("⚠️ PDFs no disponibles")
            
        if EMAIL_DISPONIBLE:
            st.success("✅ Envío de correos")
        else:
            st.warning("⚠️ Correos no disponibles")
            
        if GDRIVE_DISPONIBLE:
            st.success("✅ Google Sheets")
        else:
            st.warning("⚠️ Google Sheets no disponibles")
        
        st.markdown("---")
        st.markdown("**🚀 Versión 2.0**\nArquitectura modular")

def mostrar_tab_procesamiento():
    """
    📊 Tab principal de procesamiento de múltiples archivos
    """
    st.header("📁 Procesamiento de Archivos Excel")
    
    if not PROCESAMIENTO_DISPONIBLE:
        st.error("❌ **Módulos de procesamiento no disponibles**")
        st.info("Verifica que todos los archivos .py estén en la carpeta correcta")
        return
    
    # 📁 SECCIÓN DE CARGA MÚLTIPLE DE ARCHIVOS
    col1, col2 = st.columns([2, 1])
    
    with col1:
        archivos_subidos = st.file_uploader(
            "🔄 Selecciona uno o más archivos Excel (.xlsx, .xls)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Puedes arrastrar y soltar varios archivos a la vez."
        )
    
    with col2:
        if archivos_subidos:
            st.success(f"✅ {len(archivos_subidos)} archivo(s) cargado(s)")
        else:
            st.info("⏳ Esperando archivos...")
    
    # 🔄 PROCESAR ARCHIVOS
    if archivos_subidos and PROCESAMIENTO_DISPONIBLE:
        
        lista_de_resultados = []
        all_dataframes = []
        
        # Procesar cada archivo
        for i, archivo in enumerate(archivos_subidos):
            # Validación previa del archivo
            es_valido, mensaje = FileValidator.validar_archivo_excel(archivo)
            if not es_valido:
                st.error(f"❌ {archivo.name}: {mensaje}")
                continue
            
            with st.spinner(f"🔄 Procesando {archivo.name} ({i+1}/{len(archivos_subidos)})..."):
                # Inicializar procesador
                processor = ExcelProcessor()
                
                
                # Procesar archivo completo
                resultado = processor.procesar_archivo_completo(archivo)
                df_procesado, num_registros, tipo_archivo, info_extraida = resultado
                
            
            if df_procesado is not None and num_registros > 0:
                # Almacenar resultado
                lista_de_resultados.append({
                    'nombre_archivo': archivo.name,
                    'df': df_procesado,
                    'info_extraida': info_extraida,
                    'num_registros': num_registros
                })
                all_dataframes.append(df_procesado)
            else:
                st.error(f"❌ No se pudieron procesar los datos del archivo {archivo.name}")
        
        # Mostrar resultados por archivo
        if lista_de_resultados:
            st.header("📊 Resumen por Archivo")
            
            for resultado in lista_de_resultados:
                st.subheader(f"📄 {resultado['nombre_archivo']}")
                
                # Mostrar resumen básico
                df = resultado['df']
                info = resultado['info_extraida']
                
                # Métricas clave
                col1, col2, col3, col4, col5, col6 = st.columns(6)  # <-- CAMBIO A 6 COLUMNAS
                with col1:
                    st.metric("Programa", info.get('programa', 'N/A')[:20] + "..." if len(str(info.get('programa', 'N/A'))) > 20 else info.get('programa', 'N/A'))
                with col2:
                    st.metric("👥 Beneficiarios", int(df['COBER'].sum()) if 'COBER' in df.columns else 0)
                with col3:
                    st.metric("🐷 Cerdo (kg)", f"{df['CARNE_DE_CERDO'].sum():.1f}" if 'CARNE_DE_CERDO' in df.columns else "0.0")
                with col4:
                    st.metric("🐄 Res (kg)", f"{df['CARNE_DE_RES'].sum():.1f}" if 'CARNE_DE_RES' in df.columns else "0.0")
                with col5:
                    st.metric("🍗 Muslo (und)", int(df['MUSLO_CONTRAMUSLO'].sum()) if 'MUSLO_CONTRAMUSLO' in df.columns else 0)  # <-- ICONO ACTUALIZADO
                with col6:  # <-- NUEVA COLUMNA
                    st.metric("🐔 Pechuga (kg)", f"{df['POLLO_PESO'].sum():.1f}" if 'POLLO_PESO' in df.columns else "0.0")
                
                # Vista previa del DataFrame
                st.caption("Vista previa (10 primeras filas):")
                st.dataframe(df.head(10), use_container_width=True)
                
                st.markdown("---")
            
            # Consolidar todos los DataFrames
            if all_dataframes:
                import pandas as pd
                df_combinado = pd.concat(all_dataframes, ignore_index=True)
                st.session_state.df_procesado = df_combinado
                st.session_state.info_extraida = lista_de_resultados[0]['info_extraida']  # Usar info del primer archivo
                st.session_state.tipo_archivo = 'MULTIPROCESADO'
                
                # --- AÑADIR ESTA LÍNEA ---
                st.session_state.nombres_archivos = [res['nombre_archivo'] for res in lista_de_resultados]
                
                st.success(f"✅ {len(archivos_subidos)} archivos procesados exitosamente. {len(df_combinado)} registros totales consolidados.")
                
            
        else:
            st.error("❌ No se pudo procesar ningún archivo")
            mostrar_ayuda_troubleshooting()


def enviar_correo_completo(destinatarios, asunto, incluir_excel, incluir_pdfs, config_pdfs):
    """
    📤 Envía correo con adjuntos configurados
    """
    with st.spinner("📤 Preparando y enviando correo..."):
        try:
            archivos_adjuntos = []
            df_procesado = st.session_state.df_procesado
            info_extraida = st.session_state.get('info_extraida', {})
            tipo_archivo = st.session_state.get('tipo_archivo', 'PROCESADO')
            # --- AÑADIR ESTA LÍNEA ---
            nombres_archivos = st.session_state.get('nombres_archivos', [])
            
            # Generar Excel si se solicita
            if incluir_excel:
                excel_buffer = UtilsHelper.crear_excel_descarga_universal(df_procesado, tipo_archivo, info_extraida)
                nombre_excel = UtilsHelper.generar_nombre_archivo_unico("reporte_correo")
                archivos_adjuntos.append({
                    'buffer': excel_buffer,
                    'nombre': nombre_excel
                })
            
            # Generar PDFs si se solicita
            if incluir_pdfs and PDF_DISPONIBLE:
                from pdf_generator import GeneradorPDFsRutas
                generador = GeneradorPDFsRutas()
                modo = "por_comedor" if config_pdfs.get('modo_pdf') == "Un PDF por comedor" else "por_ruta"
                
                zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(
                    df_procesado,
                    modo=modo,
                    elaborado_por=config_pdfs.get('elaborado_por', "Supervisor"),
                    dictamen=config_pdfs.get('dictamen', "APROBADO"),
                    lotes_personalizados=config_pdfs.get('lotes_personalizados', {})
                )
                
                nombre_zip = UtilsHelper.generar_nombre_archivo_unico("guias_correo", "zip")
                archivos_adjuntos.append({
                    'buffer': zip_buffer,
                    'nombre': nombre_zip
                })
            
            # Crear mensaje HTML
            estadisticas = UtilsHelper.extraer_estadisticas_rapidas(df_procesado)
            # --- MODIFICAR ESTA LLAMADA ---
            mensaje_html = UtilsHelper.crear_mensaje_html_correo(estadisticas, info_extraida, nombres_archivos)
            
            # Enviar correo
            exito = enviar_correo_con_adjuntos(
                destinatarios=destinatarios,
                asunto=asunto,
                cuerpo_mensaje=mensaje_html,
                adjuntos=archivos_adjuntos
            )
            
            if exito:
                st.success(f"✅ Correo enviado a {len(destinatarios)} destinatarios")
                st.info(f"📎 Adjuntos: {len(archivos_adjuntos)} archivos")
            else:
                st.error("❌ Error enviando el correo")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def mostrar_tab_generar_y_enviar():
    """
    📄 Tab unificado para generación de PDFs y envío de correos
    """
    if 'df_procesado' not in st.session_state:
        st.warning("⚠️ Primero procesa archivos en la pestaña de datos.")
        return
    
    # SECCIÓN 1: GENERACIÓN DE PDFs
    st.header("📄 Generación de Guías de Transporte (PDFs)")
    
    if not PDF_DISPONIBLE:
        st.error("🚫 **Funcionalidad de PDFs no disponible**")
        st.info("Para habilitar: `pip install reportlab`")
        pdf_config_disponible = False
    else:
        pdf_config_disponible = True
        
        # Configuración de PDFs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            modo_pdf = st.radio(
                "📋 Modo de generación:",
                ["Un PDF por ruta", "Un PDF por comedor"],
                key="modo_generacion_pdf"
            )
        
        with col2:
            nombres = [
                "Shirley Paola Ibarra", "Jeferson Soto", "Alexandra Luna", "Alexander Molina",
                "Leidy Guzman", "Andres Montenegro", "Isabela Pantoja", "Luis Rodriguez","Estefania Loaiza Castro"
            ]
            elaborado_por = st.selectbox(
                "👤 Elaborado por:", nombres,
                key="elaborado_por_pdf"
            )
        
        with col3:
            dictamen = st.selectbox(
                "✅ Dictamen:", 
                ["APROBADO", "APROBADO CONDICIONADO"],
                key="dictamen_pdf"
            )
        
        # Configuración de lotes
        with st.expander("🏷️ Configuración de Lotes (Opcional)"):
            col1, col2 = st.columns(2)
            with col1:
                lote_cerdo = st.text_input("🐷 Lote Cerdo:", placeholder="CERDO-2025-001")
                lote_muslo = st.text_input("🍗 Lote Muslo/Contramuslo:", placeholder="MC-2025-A1")
            with col2:
                lote_pechuga = st.text_input("🐔 Lote Pechuga:", placeholder="POLLO-240122")
                lote_res = st.text_input("🐄 Lote Res:", placeholder="RES-010225")
        
        lotes_personalizados = {
            'cerdo': lote_cerdo.strip() if lote_cerdo.strip() else None,
            'pechuga': lote_pechuga.strip() if lote_pechuga.strip() else None,
            'muslo': lote_muslo.strip() if lote_muslo.strip() else None,
            'res': lote_res.strip() if lote_res.strip() else None
        }
        
        # Botón de generación de PDFs
        if st.button("📄 Generar ZIP de PDFs", type="primary"):
            with st.spinner("📄 Generando PDFs con paginación de 4 filas..."):
                generador = GeneradorPDFsRutas()
                modo = "por_comedor" if modo_pdf == "Un PDF por comedor" else "por_ruta"
                
                zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(
                    st.session_state.df_procesado,
                    modo=modo,
                    elaborado_por=elaborado_por,
                    dictamen=dictamen,
                    lotes_personalizados=lotes_personalizados
                )
                
                nombre_zip = UtilsHelper.generar_nombre_archivo_unico(f"guias_{modo}", "zip")
                
                st.download_button(
                    label=f"📦 Descargar ZIP ({num_pdfs} PDFs)",
                    data=zip_buffer,
                    file_name=nombre_zip,
                    mime="application/zip"
                )
                
                st.success(f"✅ {num_pdfs} PDFs generados correctamente")
    
    # SEPARADOR
    st.markdown("---")
    
    # SECCIÓN 2: GUARDADO EN GOOGLE SHEETS
    st.header("💾 Guardado en Base de Datos")
    
    if GDRIVE_DISPONIBLE:
        if 'df_procesado' not in st.session_state:
            st.warning("⚠️ Primero procesa archivos en la pestaña de datos.")
        else:
            if st.button("💾 Guardar Datos con Lotes en Google Sheets"):
                logger.info("El usuario ha presionado el botón para guardar en Google Sheets.")
                with st.spinner("Conectando con Google Sheets y guardando datos..."):
                    try:
                        # Obtener el DataFrame combinado del estado de la sesión
                        df_a_guardar = st.session_state.df_procesado.copy()
                        
                        # --- INICIO DE LA LÓGICA DE ENRIQUECIMIENTO ---
                        logger.info(f"Añadiendo lotes al DataFrame: Cerdo='{lote_cerdo}', Res='{lote_res}', Muslo='{lote_muslo}', Pechuga='{lote_pechuga}'")
                        
                        # Añadir las nuevas columnas de lotes al DataFrame
                        df_a_guardar['LOTECARNE_DE_CERDO'] = lote_cerdo if lote_cerdo else ''
                        df_a_guardar['LOTECARNE_DE_RES'] = lote_res if lote_res else ''
                        df_a_guardar['LOTEMUSLO_CONTRAMUSLO'] = lote_muslo if lote_muslo else ''
                        df_a_guardar['LOTEPOLLO_PESO'] = lote_pechuga if lote_pechuga else ''
                        # --- FIN DE LA LÓGICA DE ENRIQUECIMIENTO ---
                        
                        # Inicializar el handler con los secretos
                        handler = GoogleSheetsHandler(st.secrets["google_sheets"])
                        
                        worksheet_name = "reporte_congelados"
                        
                        # Llamar al método para añadir los datos (ahora con las columnas de lotes)
                        exito, mensaje = handler.append_to_sheet(
                            df=df_a_guardar,
                            worksheet_name=worksheet_name
                        )
                        
                        if exito:
                            st.success(mensaje)
                        else:
                            st.error(mensaje)
                    
                    except Exception as e:
                        error_msg = f"Error al guardar en Google Sheets: {e}"
                        logger.error(error_msg, exc_info=True)
                        st.error(error_msg)
    else:
        st.error("🚫 **Funcionalidad de Google Sheets no disponible**")
        st.info("Verifica la configuración del archivo `secrets.toml`")
    
    # SEPARADOR
    st.markdown("---")
    
    # SECCIÓN 3: ENVÍO DE CORREOS
    st.header("📧 Envío de Reportes por Correo")
    
    if not EMAIL_DISPONIBLE:
        st.error("🚫 **Funcionalidad de correo no disponible**")
        st.info("Configura el archivo `secrets.toml` correctamente")
        return
    
    # 📧 CORREOS PREDEFINIDOS
    correos_predefinidos = [
        "supervisorcalidad1@vallesolidario.com",
        "supervisorcalidad2@vallesolidario.com", 
        "supervisorcalidad3@vallesolidario.com",
        "supervisorcalidad4@vallesolidario.com",
        "supervisorcalidad5@vallesolidario.com",
        "jefedecalidad@vallesolidario.com",
        "despachos.chvs@gmail.com"
    ]
    
    # Configuración básica
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📧 Configuración de Destinatarios**")
        
        # ✅ CHECKBOX PARA USAR CORREOS PREDEFINIDOS
        usar_predefinidos = st.checkbox(
            "📋 Usar lista predefinida de correos", 
            value=True,
            key="usar_correos_predefinidos",
            help="Lista de correos de Valle Solidario y supervisores de calidad"
        )
        
        if usar_predefinidos:
            st.success(f"✅ **{len(correos_predefinidos)} correos predefinidos seleccionados:**")
            for email in correos_predefinidos:
                st.write(f"• {email}")
            
            correos_adicionales = st.text_area(
                "📎 Correos adicionales (opcional):",
                placeholder="correo1@ejemplo.com\ncorreo2@ejemplo.com",
                height=80,
                help="Agrega correos adicionales si necesitas enviar a más personas",
                key="correos_adicionales_area"
            )
            
            destinatarios_list = correos_predefinidos.copy()
            if correos_adicionales.strip():
                adicionales = [email.strip() for email in correos_adicionales.split('\n') if email.strip()]
                destinatarios_list.extend(adicionales)
                st.info(f"📎 Se agregarán {len(adicionales)} correos adicionales")
            
            destinatarios_text = '\n'.join(destinatarios_list)
            
        else:
            destinatarios_text = st.text_area(
                "📧 Destinatarios (uno por línea):",
                placeholder="ejemplo1@correo.com\nejemplo2@correo.com",
                height=120,
                key="destinatarios_manual_area"
            )
    
    with col2:
        st.markdown("**📝 Configuración del Mensaje**")
        asunto = st.text_input(
            "📝 Asunto:",
            value=f"Reporte Comedores Valle Solidario - {datetime.now().strftime('%Y-%m-%d')}",
            key="asunto_correo"
        )
        
        total_destinatarios = len([email for email in destinatarios_text.split('\n') if email.strip()])
        st.metric("👥 Total Destinatarios", total_destinatarios)
    
    # Configuración de adjuntos
    st.markdown("**📎 Configuración de Adjuntos**")
    col1, col2 = st.columns(2)
    with col1:
        incluir_excel = st.checkbox("📊 Incluir Excel", value=True, key="incluir_excel_correos")
    with col2:
        incluir_pdfs = st.checkbox("📄 Incluir PDFs", value=True, key="incluir_pdfs_correos")
    
    # Botón de envío
    if st.button("📤 Enviar Correo", type="primary"):
        destinatarios = [email.strip() for email in destinatarios_text.split('\n') if email.strip()]
        
        if not destinatarios or not asunto.strip():
            st.error("❌ Completa destinatarios y asunto")
            return
        
        if not incluir_excel and not incluir_pdfs:
            st.error("❌ Selecciona al menos un tipo de adjunto")
            return
        
        # Crear configuración para PDFs si se incluyen
        config_pdfs = {}
        if incluir_pdfs and pdf_config_disponible:
            config_pdfs = {
                'modo_pdf': modo_pdf,
                'elaborado_por': elaborado_por,
                'dictamen': dictamen,
                'lotes_personalizados': lotes_personalizados
            }
        
        enviar_correo_completo(destinatarios, asunto, incluir_excel, incluir_pdfs, config_pdfs)

def mostrar_ayuda_troubleshooting():
    """
    🔧 Muestra ayuda para resolución de problemas
    """
    with st.expander("🔧 Ayuda para resolución de problemas"):
        st.markdown("""
        ### 🎯 **Tipos de archivos soportados (v2.0):**
        
        1. **Comedores Comunitarios** - Rutas: "DIA X - RUTA Y"
        2. **Consorcio Alimentando a Cali** - Rutas: "CONGELADOS RUTA X"
        3. **Valle Solidario Buga** - Empresas con "BUGA"
        4. **Valle Solidario Yumbo** - Empresas con "YUMBO"
        
        ### 📋 **Estructura requerida:**
        
        - **Fila 4**: `PROGRAMA:X - EMPRESA / MODALIDAD`
        - **Fila 8**: `Solicitud Remesa: VALOR`
        - **Fila 9**: `Dias de consumo: VALOR`
        - **Columnas F, G, H (si existen)**: Productos con unidades (KG, UND, B X 1000)
        
        ### 🔍 **Productos específicos detectados:**
        
        - `CARNE DE CERDO MAGRA / B X 1000` o `/ KG`
        - `MUSLO / CONTRAMUSLO DE POLLO UND / UND`
        - `PECHUGA POLLO / KG`
        - `CARNE DE RES, MAGRA / KG`
        
        ### ⚠️ **Problemas comunes:**
        
        - **Archivo muy pequeño**: Debe tener al menos 15 filas y 6 columnas (A-F)
        - **Fila 4 vacía**: Debe contener información del programa
        - **Columnas vacías**: F (y G, H si existen) deben tener datos de productos
        - **Formato de fecha**: Usar YYYY-MM-DD en días de consumo
        """)

def main():
    """
    🏠 Función principal de la aplicación
    """
    # Título principal
    st.title("🍽️ Procesador de Reportes v2.0 - CHVS")
    st.markdown("---")
    
    # Mostrar sidebar
    mostrar_sidebar()
    
    # Crear tabs principales
    tab1, tab2 = st.tabs(["📊 Procesar Archivos", "📄 Generar y Enviar Reportes"])
    
    with tab1:
        mostrar_tab_procesamiento()
    
    with tab2:
        mostrar_tab_generar_y_enviar()

if __name__ == "__main__":
    main()