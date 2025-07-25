"""
🍽️ APP.PY - INTERFAZ PRINCIPAL SIMPLIFICADA
Aplicación Streamlit para procesamiento de reportes de comedores comunitarios
Versión 2.0 - Arquitectura modular con extracción estructurada
"""

import streamlit as st
from datetime import datetime

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
        - 🐔 Muslo/Contramuslo (UND)
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
        
        st.markdown("---")
        st.markdown("**🚀 Versión 2.0**\nArquitectura modular")

def mostrar_tab_procesamiento():
    """
    📊 Tab principal de procesamiento de datos
    """
    st.header("📁 Procesamiento de Archivos Excel")
    
    if not PROCESAMIENTO_DISPONIBLE:
        st.error("❌ **Módulos de procesamiento no disponibles**")
        st.info("Verifica que todos los archivos .py estén en la carpeta correcta")
        return
    
    # 📁 SECCIÓN DE CARGA DE ARCHIVO
    col1, col2 = st.columns([2, 1])
    
    with col1:
        archivo_subido = st.file_uploader(
            "🔄 Selecciona archivo Excel (.xlsx, .xls)",
            type=['xlsx', 'xls'],
            help="Soporta todos los tipos: Comedores, Consorcio, Valle Solidario"
        )
    
    with col2:
        if archivo_subido:
            st.success("✅ Archivo cargado")
            
            # Validación previa del archivo
            es_valido, mensaje = FileValidator.validar_archivo_excel(archivo_subido)
            if es_valido:
                st.success(f"✅ {mensaje}")
            else:
                st.error(f"❌ {mensaje}")
                return
        else:
            st.info("⏳ Esperando archivo...")
    
    # 🔄 PROCESAR ARCHIVO
    if archivo_subido and PROCESAMIENTO_DISPONIBLE:
        # Checkbox para modo debug
        modo_debug = st.checkbox("🐛 Modo Debug (mostrar logs detallados)", value=False)
        
        with st.spinner("🔄 Procesando archivo con nueva arquitectura..."):
            # Inicializar procesador
            processor = ExcelProcessor()
            
            # Capturar logs si está en modo debug
            if modo_debug:
                import io
                import sys
                
                # Redirigir prints a un buffer
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
            
            # Procesar archivo completo
            resultado = processor.procesar_archivo_completo(archivo_subido)
            df_procesado, num_registros, tipo_archivo, info_extraida = resultado
            
            # Mostrar logs si está en modo debug
            if modo_debug:
                sys.stdout = old_stdout
                logs = buffer.getvalue()
                if logs:
                    st.subheader("🐛 Logs de Debug")
                    st.code(logs, language="text")
        
        if df_procesado is not None and num_registros > 0:
            # Guardar en session_state
            st.session_state.df_procesado = df_procesado
            st.session_state.tipo_archivo = tipo_archivo
            st.session_state.info_extraida = info_extraida
            
            # ✅ MOSTRAR INFORMACIÓN EXTRAÍDA
            mostrar_informacion_extraida(tipo_archivo, info_extraida, num_registros)
            
            # 📊 MOSTRAR MÉTRICAS
            mostrar_metricas_principales(df_procesado)
            
            # 📋 MOSTRAR DATOS
            mostrar_tabla_datos(df_procesado)
            
            # 📈 MOSTRAR ANÁLISIS
            mostrar_analisis_por_ruta(df_procesado)
            
            # 💾 SECCIÓN DE DESCARGA
            mostrar_seccion_descarga(df_procesado, tipo_archivo, info_extraida)
            
        else:
            st.error(f"❌ No se pudieron procesar los datos del archivo tipo '{tipo_archivo}'")
            mostrar_ayuda_troubleshooting()

def mostrar_informacion_extraida(tipo_archivo, info_extraida, num_registros):
    """
    🔍 Muestra la información extraída del archivo
    """
    st.success(f"✅ **Archivo procesado exitosamente:** {num_registros} comedores encontrados")
    
    # Información en columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"🔍 **Tipo detectado:** {tipo_archivo}")
        st.info(f"📋 **Programa:** {info_extraida.get('programa', 'N/A')[:50]}...")
    
    with col2:
        st.info(f"🏢 **Empresa:** {info_extraida.get('empresa', 'N/A')[:50]}...")
        st.info(f"🎯 **Modalidad:** {info_extraida.get('modalidad', 'N/A')}")
    
    with col3:
        st.info(f"📄 **Solicitud Remesa:** {info_extraida.get('solicitud_remesa', 'N/A')[:30]}...")
        st.info(f"📅 **Días de Consumo:** {info_extraida.get('dias_consumo', 'N/A')[:30]}...")
    
    # Validación de datos
    es_valido, errores, advertencias = UtilsHelper.validar_dataframe(st.session_state.df_procesado)
    
    if not es_valido:
        st.error(f"⚠️ **Errores detectados:** {', '.join(errores)}")
    
    if advertencias:
        st.warning(f"⚠️ **Advertencias:** {', '.join(advertencias)}")

def mostrar_metricas_principales(df_procesado):
    """
    📊 Muestra métricas principales en formato visual
    """
    st.header("📊 Métricas Principales")
    
    stats = UtilsHelper.extraer_estadisticas_rapidas(df_procesado)
    
    # Fila 1: Métricas básicas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏪 Comedores", UtilsHelper.formatear_numero(stats['comedores'], 0))
    with col2:
        st.metric("👥 Beneficiarios", UtilsHelper.formatear_numero(stats['beneficiarios'], 0))
    with col3:
        st.metric("🛣️ Rutas", UtilsHelper.formatear_numero(stats['rutas'], 0))
    with col4:
        promedio = stats['beneficiarios'] / stats['comedores'] if stats['comedores'] > 0 else 0
        st.metric("📈 Promedio/Comedor", UtilsHelper.formatear_numero(promedio, 1))
    
    # Fila 2: Productos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🐷 Cerdo (kg)", UtilsHelper.formatear_numero(stats['cerdo_kg'], 1))
    with col2:
        st.metric("🐄 Res (kg)", UtilsHelper.formatear_numero(stats['res_kg'], 1))
    with col3:
        st.metric("🐔 Muslo/Contramuslo", UtilsHelper.formatear_numero(stats['muslo_und'], 0))
    with col4:
        st.metric("🐔 Pechuga (kg)", UtilsHelper.formatear_numero(stats['pollo_kg'], 1))

def mostrar_tabla_datos(df_procesado):
    """
    📋 Muestra la tabla de datos con filtros
    """
    st.header("📋 Datos Procesados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rutas_disponibles = sorted(df_procesado['RUTA'].unique()) if 'RUTA' in df_procesado.columns else []
        rutas_seleccionadas = st.multiselect(
            "🛣️ Filtrar por rutas:",
            options=rutas_disponibles,
            default=rutas_disponibles[:3] if len(rutas_disponibles) > 3 else rutas_disponibles
        )
    
    with col2:
        empresas_disponibles = sorted(df_procesado['EMPRESA'].unique()) if 'EMPRESA' in df_procesado.columns else []
        if len(empresas_disponibles) > 1:
            empresas_seleccionadas = st.multiselect(
                "🏢 Filtrar por empresa:",
                options=empresas_disponibles,
                default=empresas_disponibles
            )
        else:
            empresas_seleccionadas = empresas_disponibles
    
    with col3:
        mostrar_todos = st.checkbox("👁️ Mostrar todas las filas", value=False)
    
    # Aplicar filtros
    df_filtrado = df_procesado.copy()
    
    if rutas_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['RUTA'].isin(rutas_seleccionadas)]
    
    if empresas_seleccionadas and 'EMPRESA' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['EMPRESA'].isin(empresas_seleccionadas)]
    
    # Mostrar tabla
    if len(df_filtrado) > 0:
        altura = 600 if mostrar_todos else 400
        st.dataframe(df_filtrado, use_container_width=True, height=altura)
        st.caption(f"📊 Mostrando {len(df_filtrado)} de {len(df_procesado)} comedores")
    else:
        st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")

def mostrar_analisis_por_ruta(df_procesado):
    """
    📈 Muestra análisis detallado por ruta
    """
    st.header("📈 Análisis por Ruta")
    
    if 'RUTA' not in df_procesado.columns:
        st.warning("⚠️ No se encontraron datos de rutas")
        return
    
    # Crear análisis
    df_analisis = UtilsHelper._crear_analisis_por_ruta(df_procesado)
    
    # Mostrar tabla
    st.dataframe(df_analisis, use_container_width=True)
    
    # Estadísticas adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 3 Rutas por Beneficiarios")
        top_rutas = df_analisis.nlargest(3, 'Total_Beneficiarios')[['Total_Beneficiarios', 'Comedores']]
        st.dataframe(top_rutas)
    
    with col2:
        st.subheader("💰 Top 3 Rutas por Valor Estimado")
        if 'Valor_Estimado_COP' in df_analisis.columns:
            top_valor = df_analisis.nlargest(3, 'Valor_Estimado_COP')[['Valor_Estimado_COP', 'Total_Proteina_kg']]
            st.dataframe(top_valor)

def mostrar_seccion_descarga(df_procesado, tipo_archivo, info_extraida):
    """
    💾 Sección de descarga mejorada
    """
    st.header("💾 Descargar Resultados")
    
    # Generar archivo Excel
    with st.spinner("📊 Generando archivo Excel con 6 hojas..."):
        archivo_excel = UtilsHelper.crear_excel_descarga_universal(df_procesado, tipo_archivo, info_extraida)
        nombre_archivo = UtilsHelper.generar_nombre_archivo_unico(f"reporte_{tipo_archivo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Descargar Excel Completo",
            data=archivo_excel,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Incluye 6 hojas: Datos, Resumen, Análisis por Ruta, por Empresa, Temporal y Metadatos"
        )
    
    with col2:
        # Información del archivo
        st.info(f"""
        **📊 El archivo Excel incluye:**
        - 📋 Datos procesados completos
        - 📈 Resumen con nueva estructura  
        - 🛣️ Análisis por ruta con valores estimados
        - 🏢 Análisis por empresa/modalidad
        - 📅 Análisis temporal
        - 🔍 Metadatos técnicos
        """)

def mostrar_tab_pdfs():
    """
    📄 Tab de generación de PDFs
    """
    st.header("📄 Generación de PDFs")
    
    if not PDF_DISPONIBLE:
        st.error("🚫 **Funcionalidad de PDFs no disponible**")
        st.info("Para habilitar: `pip install reportlab`")
        return
    
    if 'df_procesado' not in st.session_state:
        st.warning("⚠️ Primero procesa un archivo en la pestaña de datos.")
        return
    
    # Configuración de PDFs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        modo_pdf = st.radio(
            "📋 Modo de generación:",
            ["Un PDF por ruta", "Un PDF por comedor"],
            key="modo_generacion_pdf"  # <-- KEY AÑADIDO
        )
    
    with col2:
        nombres = [
            "Shirley Paola Ibarra", "Jeferson Soto", "Alexandra Luna", "Alexander Molina",
            "Leidy Guzman", "Andres Montenegro", "Isabela Pantoja", "Luis Rodriguez","Estefania Loaiza Castro"
        ]
        elaborado_por = st.selectbox(
            "👤 Elaborado por:", nombres,
            key="elaborado_por_pdf"  )# <-- KEY AÑADIDO))
    
    with col3:
        dictamen = st.selectbox("✅ Dictamen:", ["APROBADO", "APROBADO CONDICIONADO"],
                                key="dictamen_pdf"
                                )
    
    # Configuración de lotes
    with st.expander("🏷️ Configuración de Lotes (Opcional)"):
        col1, col2 = st.columns(2)
        with col1:
            lote_cerdo = st.text_input("🐷 Lote Cerdo:", placeholder="CERDO-2025-001")
            lote_muslo = st.text_input("🐔 Lote Muslo/Contramuslo:", placeholder="MC-2025-A1")
        with col2:
            lote_pechuga = st.text_input("🐔 Lote Pechuga:", placeholder="POLLO-240122")
            lote_res = st.text_input("🐄 Lote Res:", placeholder="RES-010225")
    
    lotes_personalizados = {
        'cerdo': lote_cerdo.strip() if lote_cerdo.strip() else None,
        'pechuga': lote_pechuga.strip() if lote_pechuga.strip() else None,
        'muslo': lote_muslo.strip() if lote_muslo.strip() else None,
        'res': lote_res.strip() if lote_res.strip() else None
    }
    
    # Botón de generación
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

def mostrar_tab_correos():
    """
    📧 Tab de envío de correos
    """
    st.header("📧 Envío de Correos")
    
    if not EMAIL_DISPONIBLE:
        st.error("🚫 **Funcionalidad de correo no disponible**")
        st.info("Configura el archivo `secrets.toml` correctamente")
        return
    
    if 'df_procesado' not in st.session_state:
        st.warning("⚠️ Primero procesa un archivo en la pestaña de datos.")
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
    
    # Configuración de PDFs (si se incluyen)
    if incluir_pdfs and PDF_DISPONIBLE:
        st.subheader("🎯 Configuración de PDFs")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            modo_pdf = st.radio("Modo:", ["Por ruta", "Por comedor"], key="modo_pdf_correos")
        with col2:
            nombres = ["Shirley Paola Ibarra", "Jeferson Soto", "Alexandra Luna", "Alexander Molina"]
            elaborado_por = st.selectbox(
                "Elaborado por:", 
                nombres, 
                key="elaborado_por_correos"  # <-- KEY AÑADIDO (y corregido)
            )
        with col3:
            dictamen = st.selectbox(
                "Dictamen:", 
                ["APROBADO", "APROBADO CONDICIONADO"], 
                key="dictamen_correos"  # <-- KEY AÑADIDO (y corregido)
            )
    
    
    # Botón de envío
    if st.button("📤 Enviar Correo", type="primary"):
        destinatarios = [email.strip() for email in destinatarios_text.split('\n') if email.strip()]
        
        if not destinatarios or not asunto.strip():
            st.error("❌ Completa destinatarios y asunto")
            return
        
        if not incluir_excel and not incluir_pdfs:
            st.error("❌ Selecciona al menos un tipo de adjunto")
            return
        
        enviar_correo_completo(destinatarios, asunto, incluir_excel, incluir_pdfs, locals())

def enviar_correo_completo(destinatarios, asunto, incluir_excel, incluir_pdfs, config):
    """
    📤 Envía correo con adjuntos configurados
    """
    with st.spinner("📤 Preparando y enviando correo..."):
        try:
            archivos_adjuntos = []
            df_procesado = st.session_state.df_procesado
            info_extraida = st.session_state.get('info_extraida', {})
            tipo_archivo = st.session_state.get('tipo_archivo', 'PROCESADO')
            
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
                modo = "por_comedor" if config.get('modo_pdf') == "Por comedor" else "por_ruta"
                
                zip_buffer, num_pdfs = generador.generar_todos_los_pdfs(
                    df_procesado,
                    modo=modo,
                    elaborado_por=config.get('elaborado_por', "Supervisor"),
                    dictamen=config.get('dictamen', "APROBADO")
                )
                
                nombre_zip = UtilsHelper.generar_nombre_archivo_unico("guias_correo", "zip")
                archivos_adjuntos.append({
                    'buffer': zip_buffer,
                    'nombre': nombre_zip
                })
            
            # Crear mensaje HTML
            estadisticas = UtilsHelper.extraer_estadisticas_rapidas(df_procesado)
            mensaje_html = UtilsHelper.crear_mensaje_html_correo(estadisticas, info_extraida)
            
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
    tab1, tab2, tab3 = st.tabs(["📊 Procesar Datos", "📄 Generar PDFs", "📧 Enviar Correos"])
    
    with tab1:
        mostrar_tab_procesamiento()
    
    with tab2:
        mostrar_tab_pdfs()
    
    with tab3:
        mostrar_tab_correos()

if __name__ == "__main__":
    main()