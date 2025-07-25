"""
🔧 UTILS.PY
Módulo de utilidades comunes para la aplicación
Incluye funciones de formato, validación y generación de archivos
"""

import pandas as pd
import re
import unicodedata
from datetime import datetime
from io import BytesIO

class UtilsHelper:
    """
    Clase con utilidades comunes para la aplicación
    """
    
    @staticmethod
    def crear_excel_descarga_universal(df, tipo_archivo, info_extraida=None):
        """
        ✅ Crea un archivo Excel optimizado para descarga - COMPLETAMENTE RENOVADO
        
        Args:
            df (DataFrame): Datos procesados
            tipo_archivo (str): Tipo de archivo detectado
            info_extraida (dict): Información extraída del encabezado
            
        Returns:
            BytesIO: Buffer con archivo Excel
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 📊 HOJA 1: DATOS PROCESADOS
            df.to_excel(writer, sheet_name='Datos_Procesados', index=False)
            
            # 📋 HOJA 2: RESUMEN COMPLETO CON NUEVA ESTRUCTURA
            resumen_data = UtilsHelper._crear_datos_resumen(df, tipo_archivo, info_extraida)
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen_General', index=False)
            
            # 📈 HOJA 3: ANÁLISIS POR RUTA
            df_por_ruta = UtilsHelper._crear_analisis_por_ruta(df)
            df_por_ruta.to_excel(writer, sheet_name='Analisis_Por_Ruta')
            
            # 🏢 HOJA 4: ANÁLISIS POR EMPRESA/MODALIDAD
            if 'EMPRESA' in df.columns and 'MODALIDAD' in df.columns:
                try:
                    df_por_empresa = UtilsHelper._crear_analisis_por_empresa(df)
                    if not df_por_empresa.empty:
                        df_por_empresa.to_excel(writer, sheet_name='Analisis_Por_Empresa')
                except Exception as e:
                    # Si hay error, crear hoja con mensaje de error
                    error_df = pd.DataFrame({'Error': [f'Error creando análisis por empresa: {str(e)}']})
                    error_df.to_excel(writer, sheet_name='Analisis_Por_Empresa', index=False)
            
            # 📅 HOJA 5: ANÁLISIS TEMPORAL (si hay datos de fechas)
            if 'DIAS_CONSUMO' in df.columns:
                try:
                    df_temporal = UtilsHelper._crear_analisis_temporal(df)
                    if not df_temporal.empty:
                        df_temporal.to_excel(writer, sheet_name='Analisis_Temporal')
                except Exception as e:
                    # Si hay error, crear hoja con mensaje de error
                    error_df = pd.DataFrame({'Error': [f'Error creando análisis temporal: {str(e)}']})
                    error_df.to_excel(writer, sheet_name='Analisis_Temporal', index=False)
            
            # 🔍 HOJA 6: METADATOS Y INFORMACIÓN TÉCNICA
            metadatos_dict = UtilsHelper._crear_metadatos(df, tipo_archivo, info_extraida)
            df_metadatos = pd.DataFrame(metadatos_dict)
            df_metadatos.to_excel(writer, sheet_name='Metadatos', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def _crear_datos_resumen(df, tipo_archivo, info_extraida):
        """
        📋 Crea los datos de resumen con la nueva estructura
        """
        info_extraida = info_extraida or {}
        
        return {
            'Métrica': [
                '🔍 Tipo de Archivo Detectado',
                '📋 Programa',
                '🏢 Empresa',
                '🎯 Modalidad',
                '📄 Solicitud de Remesa',
                '📅 Días de Consumo',
                '🗓️ Fecha de Entrega',
                '🏪 Total Comedores/Escuelas',
                '👥 Total Beneficiarios',
                '🛣️ Total Rutas',
                '🐷 Total Carne de Cerdo (kg)',
                '🐄 Total Carne de Res (kg)', 
                '🐔 Total Muslo/Contramuslo (und)',
                '🐔 Total Pollo Peso (kg)',
                '💰 Valor Estimado Cerdo ($)',
                '💰 Valor Estimado Res ($)',
                '💰 Valor Estimado Pollo ($)',
                '📈 Promedio Beneficiarios/Comedor',
                '📊 Cobertura Mayor Ruta',
                '🕒 Fecha de Procesamiento'
            ],
            'Valor': [
                tipo_archivo,
                info_extraida.get('programa', df['PROGRAMA'].iloc[0] if len(df) > 0 and 'PROGRAMA' in df.columns else "N/A"),
                info_extraida.get('empresa', df['EMPRESA'].iloc[0] if len(df) > 0 and 'EMPRESA' in df.columns else "N/A"),
                info_extraida.get('modalidad', df['MODALIDAD'].iloc[0] if len(df) > 0 and 'MODALIDAD' in df.columns else "N/A"),
                info_extraida.get('solicitud_remesa', df['SOLICITUD_REMESA'].iloc[0] if len(df) > 0 and 'SOLICITUD_REMESA' in df.columns else "N/A"),
                info_extraida.get('dias_consumo', df['DIAS_CONSUMO'].iloc[0] if len(df) > 0 and 'DIAS_CONSUMO' in df.columns else "N/A"),
                info_extraida.get('fecha_entrega', df['FECHA_ENTREGA'].iloc[0] if len(df) > 0 and 'FECHA_ENTREGA' in df.columns else "N/A"),
                len(df),
                f"{df['COBER'].sum():,}" if 'COBER' in df.columns else "0",
                df['RUTA'].nunique() if 'RUTA' in df.columns else "0",
                f"{df['CARNE_DE_CERDO'].sum():.2f}" if 'CARNE_DE_CERDO' in df.columns else "0.00",
                f"{df['CARNE_DE_RES'].sum():.2f}" if 'CARNE_DE_RES' in df.columns else "0.00",
                f"{df['MUSLO_CONTRAMUSLO'].sum():,}" if 'MUSLO_CONTRAMUSLO' in df.columns else "0",
                f"{df['POLLO_PESO'].sum():.2f}" if 'POLLO_PESO' in df.columns else "0.00",
                f"${df['CARNE_DE_CERDO'].sum() * 15000:,.0f}" if 'CARNE_DE_CERDO' in df.columns else "$0",  # Precio estimado
                f"${df['CARNE_DE_RES'].sum() * 18000:,.0f}" if 'CARNE_DE_RES' in df.columns else "$0",
                f"${df['POLLO_PESO'].sum() * 12000:,.0f}" if 'POLLO_PESO' in df.columns else "$0",
                f"{df['COBER'].mean():.1f}" if 'COBER' in df.columns and len(df) > 0 else "0.0",
                df.groupby('RUTA')['COBER'].sum().max() if 'RUTA' in df.columns and 'COBER' in df.columns else "0",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
    
    @staticmethod
    def _crear_analisis_por_ruta(df):
        """
        📈 Crea análisis detallado por ruta
        """
        if 'RUTA' not in df.columns:
            return pd.DataFrame({'Error': ['No se encontraron rutas en los datos']})
        
        df_por_ruta = df.groupby('RUTA').agg({
            'COMEDOR/ESCUELA': 'count',
            'COBER': 'sum',
            'CARNE_DE_CERDO': 'sum',
            'CARNE_DE_RES': 'sum',
            'MUSLO_CONTRAMUSLO': 'sum',
            'POLLO_PESO': 'sum'
        }).round(2)
        
        # Renombrar columnas para mayor claridad
        df_por_ruta.columns = [
            'Comedores',
            'Total_Beneficiarios', 
            'Cerdo_kg',
            'Res_kg',
            'Muslo_Contramuslo_und',
            'Pollo_kg'
        ]
        
        # Agregar columnas calculadas
        df_por_ruta['Promedio_Beneficiarios_Comedor'] = (df_por_ruta['Total_Beneficiarios'] / df_por_ruta['Comedores']).round(1)
        df_por_ruta['Total_Proteina_kg'] = (df_por_ruta['Cerdo_kg'] + df_por_ruta['Res_kg'] + df_por_ruta['Pollo_kg']).round(2)
        df_por_ruta['Valor_Estimado_COP'] = (
            df_por_ruta['Cerdo_kg'] * 15000 + 
            df_por_ruta['Res_kg'] * 18000 + 
            df_por_ruta['Pollo_kg'] * 12000
        ).round(0)
        
        return df_por_ruta
    
    @staticmethod
    def _crear_analisis_por_empresa(df):
        """
        🏢 Crea análisis por empresa y modalidad
        """
        if 'EMPRESA' not in df.columns:
            return pd.DataFrame({'Error': ['No se encontró información de empresa']})
        
        # Análisis por empresa
        df_empresa = df.groupby(['EMPRESA', 'MODALIDAD']).agg({
            'COMEDOR/ESCUELA': 'count',
            'COBER': 'sum',
            'RUTA': 'nunique',
            'CARNE_DE_CERDO': 'sum',
            'CARNE_DE_RES': 'sum',
            'MUSLO_CONTRAMUSLO': 'sum',
            'POLLO_PESO': 'sum'
        }).round(2)
        
        df_empresa.columns = [
            'Comedores',
            'Beneficiarios',
            'Rutas',
            'Cerdo_kg',
            'Res_kg', 
            'Muslo_Contramuslo_und',
            'Pollo_kg'
        ]
        
        return df_empresa
    
    @staticmethod
    def _crear_analisis_temporal(df):
        """
        📅 Crea análisis temporal basado en días de consumo
        """
        if 'DIAS_CONSUMO' not in df.columns:
            return pd.DataFrame({'Error': ['No se encontró información temporal']})
        
        # Crear análisis básico por días de consumo
        df_temporal = df.groupby('DIAS_CONSUMO').agg({
            'COMEDOR/ESCUELA': 'count',
            'COBER': 'sum',
            'RUTA': 'nunique'
        })
        
        df_temporal.columns = ['Comedores', 'Beneficiarios', 'Rutas']
        
        return df_temporal
    
    @staticmethod
    def _crear_metadatos(df, tipo_archivo, info_extraida):
        """
        🔍 Crea hoja de metadatos técnicos
        
        Returns:
            dict: Diccionario con estructura para DataFrame
        """
        info_extraida = info_extraida or {}
        
        metadatos = {
            'Propiedad': [
                'Estructura de Archivo',
                'Versión de Procesador',
                'Columnas Totales',
                'Filas Procesadas',
                'Tipos de Datos Detectados',
                'Productos Mapeados',
                'Rutas Únicas',
                'Municipios',
                'Rango de Fechas',
                'Algoritmo de Detección',
                'Tiempo de Procesamiento',
                'Validaciones Aplicadas',
                'Columnas Nuevas (v2.0)',
                'Información Extraída de',
                'Estado de Calidad'
            ],
            'Valor': [
                f"Tipo: {tipo_archivo}",
                "v2.0 - Extracción Estructurada",
                len(df.columns) if df is not None else 0,
                len(df) if df is not None else 0,
                "Numérico, Texto, Fecha",
                "Cerdo, Res, Muslo/Contramuslo, Pechuga",
                df['RUTA'].nunique() if df is not None and 'RUTA' in df.columns else 0,
                df['MUNICIPIO'].nunique() if df is not None and 'MUNICIPIO' in df.columns else 0,
                f"{info_extraida.get('dias_consumo', 'No especificado')}",
                "Patrones regex + contexto",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "Validación numérica, limpieza de texto",
                "PROGRAMA, EMPRESA, MODALIDAD",
                "Fila 4 (estructura), Filas 8-9 (remesa/días)",
                "✅ Procesado correctamente" if df is not None and len(df) > 0 else "❌ Error en procesamiento"
            ]
        }
        
        return metadatos
    
    @staticmethod
    def limpiar_nombre_archivo(nombre):
        """
        🧹 Limpia nombres para que sean válidos como archivos
        """
        if not nombre:
            return "archivo_sin_nombre"
        
        # Convertir a string
        nombre = str(nombre)
        
        # Remover códigos de comedor (ej: "63/02") del inicio
        nombre = re.sub(r'^\d+\/\d+\s*', '', nombre)
        
        # Normalizar caracteres unicode (remover acentos)
        nombre = unicodedata.normalize('NFKD', nombre)
        nombre = nombre.encode('ascii', 'ignore').decode('ascii')
        
        # Remover caracteres especiales y reemplazar espacios
        nombre_limpio = re.sub(r'[^\w\s-]', '', nombre)
        nombre_limpio = re.sub(r'[-\s]+', '_', nombre_limpio)
        
        # Remover guiones bajos al inicio y final
        nombre_limpio = nombre_limpio.strip('_')
        
        # Asegurar que no esté vacío y limitar longitud
        if not nombre_limpio:
            nombre_limpio = "archivo_sin_nombre"
        
        return nombre_limpio[:40]
    
    @staticmethod
    def validar_dataframe(df):
        """
        ✅ Valida la integridad del DataFrame procesado
        
        Returns:
            tuple: (es_valido, lista_errores, lista_advertencias)
        """
        if df is None:
            return False, ["DataFrame es None"], []
        
        errores = []
        advertencias = []
        
        # Validaciones críticas
        if len(df) == 0:
            errores.append("DataFrame está vacío")
            return False, errores, advertencias
        
        # Validar columnas obligatorias
        columnas_obligatorias = ['PROGRAMA', 'EMPRESA', 'RUTA', 'COMEDOR/ESCUELA', 'COBER']
        for col in columnas_obligatorias:
            if col not in df.columns:
                errores.append(f"Falta columna obligatoria: {col}")
        
        # Validaciones de advertencia
        if 'MODALIDAD' not in df.columns:
            advertencias.append("No se encontró información de modalidad")
        
        if 'SOLICITUD_REMESA' not in df.columns:
            advertencias.append("No se encontró información de solicitud de remesa")
        
        if df['COBER'].sum() == 0:
            advertencias.append("La suma total de beneficiarios es 0")
        
        # Validar datos numéricos
        productos = ['CARNE_DE_CERDO', 'CARNE_DE_RES', 'MUSLO_CONTRAMUSLO', 'POLLO_PESO']
        total_productos = 0
        for producto in productos:
            if producto in df.columns:
                total_productos += df[producto].sum()
        
        if total_productos == 0:
            advertencias.append("No se detectaron productos (todos los valores son 0)")
        
        return len(errores) == 0, errores, advertencias
    
    @staticmethod
    def formatear_numero(numero, decimales=2):
        """
        🔢 Formatea números para visualización
        """
        try:
            if isinstance(numero, (int, float)):
                if decimales == 0:
                    return f"{int(numero):,}"
                else:
                    return f"{numero:,.{decimales}f}"
            return str(numero)
        except:
            return "0"
    
    @staticmethod
    def generar_nombre_archivo_unico(prefijo="datos_procesados", extension="xlsx"):
        """
        📁 Genera nombres de archivo únicos con timestamp
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefijo}_{timestamp}.{extension}"
    
    @staticmethod
    def extraer_estadisticas_rapidas(df):
        """
        ⚡ Extrae estadísticas rápidas para mostrar en la interfaz
        """
        if df is None or len(df) == 0:
            return {
                'comedores': 0,
                'beneficiarios': 0,
                'rutas': 0,
                'cerdo_kg': 0,
                'res_kg': 0,
                'pollo_kg': 0,
                'muslo_und': 0
            }
        
        return {
            'comedores': len(df),
            'beneficiarios': int(df['COBER'].sum()) if 'COBER' in df.columns else 0,
            'rutas': df['RUTA'].nunique() if 'RUTA' in df.columns else 0,
            'cerdo_kg': float(df['CARNE_DE_CERDO'].sum()) if 'CARNE_DE_CERDO' in df.columns else 0,
            'res_kg': float(df['CARNE_DE_RES'].sum()) if 'CARNE_DE_RES' in df.columns else 0,
            'pollo_kg': float(df['POLLO_PESO'].sum()) if 'POLLO_PESO' in df.columns else 0,
            'muslo_und': int(df['MUSLO_CONTRAMUSLO'].sum()) if 'MUSLO_CONTRAMUSLO' in df.columns else 0
        }
    
    @staticmethod
    def crear_mensaje_html_correo(estadisticas, info_extraida):
        """
        📧 Crea mensaje HTML personalizado para correos
        """
        info_extraida = info_extraida or {}
        
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
                📊 Reporte de Comedores Procesado
            </h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #495057; margin-top: 0;">📋 Información del Programa</h3>
                <p><strong>🏢 Empresa:</strong> {info_extraida.get('empresa', 'No especificada')}</p>
                <p><strong>📋 Programa:</strong> {info_extraida.get('programa', 'No especificado')}</p>
                <p><strong>🎯 Modalidad:</strong> {info_extraida.get('modalidad', 'No especificada')}</p>
                <p><strong>📄 Solicitud Remesa:</strong> {info_extraida.get('solicitud_remesa', 'No especificada')}</p>
                <p><strong>📅 Días de Consumo:</strong> {info_extraida.get('dias_consumo', 'No especificados')}</p>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #28a745; margin-top: 0;">📊 Estadísticas del Procesamiento</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <p><strong>🏪 Total Comedores:</strong> {estadisticas['comedores']:,}</p>
                    <p><strong>👥 Total Beneficiarios:</strong> {estadisticas['beneficiarios']:,}</p>
                    <p><strong>🛣️ Total Rutas:</strong> {estadisticas['rutas']}</p>
                    <p><strong>🐷 Carne de Cerdo:</strong> {estadisticas['cerdo_kg']:.1f} kg</p>
                    <p><strong>🐄 Carne de Res:</strong> {estadisticas['res_kg']:.1f} kg</p>
                    <p><strong>🐔 Pollo (Peso):</strong> {estadisticas['pollo_kg']:.1f} kg</p>
                </div>
            </div>
            
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #856404; margin-top: 0;">📎 Archivos Adjuntos</h3>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li style="margin: 10px 0;">📊 <strong>Archivo Excel:</strong> Datos normalizados y análisis estadístico completo</li>
                    <li style="margin: 10px 0;">📄 <strong>ZIP de PDFs:</strong> Guías de transporte individuales listas para impresión</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <p style="color: #6c757d; font-size: 12px;">
                    🕒 Generado el {datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')}<br>
                    🤖 Sistema de Procesamiento Automatizado v2.0
                </p>
            </div>
        </div>
        """

class FileValidator:
    """
    🔍 Clase específica para validación de archivos Excel
    """
    
    @staticmethod
    def validar_archivo_excel(archivo):
        """
        ✅ Valida que el archivo Excel tenga el formato esperado
        
        Returns:
            tuple: (es_valido, mensaje_error)
        """
        try:
            # Leer las primeras filas para validación
            df_sample = pd.read_excel(archivo, header=None, nrows=20)
            
            # Validar que tenga al menos 10 filas
            if len(df_sample) < 10:
                return False, "El archivo debe tener al menos 10 filas de datos"
            
            # Validar que tenga al menos 6 columnas
            if len(df_sample.columns) < 6:
                return False, "El archivo debe tener al menos 6 columnas (A-F)"
            
            # Validar que la fila 4 tenga contenido (información del programa)
            if len(df_sample) > 3:
                fila_4 = str(df_sample.iloc[3, 0]).strip()
                if not fila_4 or fila_4.lower() in ['nan', 'none', '']:
                    return False, "La fila 4 debe contener información del programa"
            
            return True, "Archivo válido"
            
        except Exception as e:
            return False, f"Error leyendo el archivo: {str(e)}"
    
    @staticmethod
    def detectar_problemas_comunes(df_raw):
        """
        🔧 Detecta problemas comunes en archivos Excel
        
        Returns:
            list: Lista de problemas detectados
        """
        problemas = []
        
        # Problema 1: Archivo muy pequeño
        if len(df_raw) < 15:
            problemas.append("⚠️ El archivo parece muy pequeño (menos de 15 filas)")
        
        # Problema 2: Muchas celdas vacías en columna A
        celdas_vacias = df_raw.iloc[:, 0].isna().sum()
        if celdas_vacias > len(df_raw) * 0.5:
            problemas.append("⚠️ Muchas celdas vacías en la columna A")
        
        # Problema 3: No hay datos en columnas de productos (F, G, H si existen)
        num_columnas = len(df_raw.columns)
        if num_columnas >= 6:  # Solo validar si tiene al menos 6 columnas
            for col in range(5, min(num_columnas, 8)):  # Validar F, G, H si existen
                if df_raw.iloc[:, col].isna().all():
                    problemas.append(f"⚠️ La columna {chr(65+col)} está completamente vacía")
        
        # Problema 4: Formato de fecha inusual
        fecha_encontrada = False
        for i in range(min(15, len(df_raw))):
            celda = str(df_raw.iloc[i, 0])
            if re.search(r'\d{4}-\d{1,2}-\d{1,2}', celda):
                fecha_encontrada = True
                break
        
        if not fecha_encontrada:
            problemas.append("⚠️ No se detectaron fechas en formato YYYY-MM-DD")
        
        return problemas