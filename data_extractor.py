"""
📊 DATA_EXTRACTOR.PY
Módulo para extracción estructurada de información de archivos Excel
Maneja el parsing inteligente de encabezados y metadatos
"""

import pandas as pd
import re
from datetime import datetime

class DataExtractor:
    """
    Clase principal para extraer información estructurada de archivos Excel
    """
    
    def __init__(self):
        self.tipos_soportados = [
            "COMEDORES_COMUNITARIOS",
            "CONSORCIO_CONGELADOS", 
            "CONSORCIO_JU",
            "CONSORCIO_GENERAL",
            "VALLE_SOLIDARIO_BUGA",
            "VALLE_SOLIDARIO_YUMBO"
        ]
    
    def detectar_tipo_archivo(self, df_raw):
        """
        ✅ Detecta el tipo de archivo basado en patrones en las primeras 15 filas
        """
        for i in range(min(15, len(df_raw))):
            fila = df_raw.iloc[i, 0] if not pd.isna(df_raw.iloc[i, 0]) else ""
            fila_str = str(fila).upper()
            
            # 1. COMEDORES COMUNITARIOS
            if "COMEDORES COMUNITARIOS" in fila_str:
                return "COMEDORES_COMUNITARIOS", fila_str
                
            # 2. CONSORCIO ALIMENTANDO A CALI (con subtipos)
            elif "CONSORCIO ALIMENTANDO A CALI" in fila_str:
                for j in range(i, min(30, len(df_raw))):
                    fila_j = str(df_raw.iloc[j, 0]).upper() if not pd.isna(df_raw.iloc[j, 0]) else ""
                    if "CONGELADOS RUTA" in fila_j:
                        return "CONSORCIO_CONGELADOS", fila_str
                    elif "JU CALI" in fila_j or "JORNADA UNICA" in fila_j:
                        return "CONSORCIO_JU", fila_str
                return "CONSORCIO_GENERAL", fila_str
                
            # 3. VALLE SOLIDARIO BUGA
            elif "UNION TEMPORAL VALLE SOLIDARIO BUGA" in fila_str or "VALLE SOLIDARIO BUGA 2025" in fila_str:
                return "VALLE_SOLIDARIO_BUGA", fila_str
                
            # 4. VALLE SOLIDARIO YUMBO  
            elif "UNION TEMPORAL VALLE SOLIDARIO YUMBO" in fila_str or "VALLE SOLIDARIO YUMBO 2025" in fila_str:
                return "VALLE_SOLIDARIO_YUMBO", fila_str
        
        return "DESCONOCIDO", "PROGRAMA NO DETECTADO"
    
    def extraer_informacion_estructurada(self, df_raw):
        """
        🎯 NUEVA FUNCIÓN: Extrae información de manera estructurada según las especificaciones
        
        Returns:
            dict: {
                'programa': str,
                'empresa': str, 
                'modalidad': str,
                'solicitud_remesa': str,
                'dias_consumo': str,
                'fecha_entrega': str
            }
        """
        resultado = {
            'programa': 'PROGRAMA NO DETECTADO',
            'empresa': 'EMPRESA NO DETECTADA',
            'modalidad': 'MODALIDAD NO DETECTADA',
            'solicitud_remesa': 'NO ESPECIFICADO',
            'dias_consumo': 'NO ESPECIFICADO',
            'fecha_entrega': datetime.now().strftime('%Y-%m-%d')
        }
        
        # ✅ EXTRAER INFORMACIÓN DE LA FILA 4
        if len(df_raw) > 3:  # Verificar que existe la fila 4 (índice 3)
            fila_4 = str(df_raw.iloc[3, 0]).strip() if not pd.isna(df_raw.iloc[3, 0]) else ""
            if fila_4:
                programa_info = self._parsear_fila_programa(fila_4)
                resultado.update(programa_info)
        
        # ✅ EXTRAER SOLICITUD REMESA DE LA FILA 8
        if len(df_raw) > 7:  # Verificar que existe la fila 8 (índice 7)
            fila_8 = str(df_raw.iloc[7, 0]).strip() if not pd.isna(df_raw.iloc[7, 0]) else ""
            if fila_8:
                solicitud = self._parsear_solicitud_remesa(fila_8)
                if solicitud:
                    resultado['solicitud_remesa'] = solicitud
        
        # ✅ EXTRAER DÍAS DE CONSUMO DE LA FILA 9
        if len(df_raw) > 8:  # Verificar que existe la fila 9 (índice 8)
            fila_9 = str(df_raw.iloc[8, 0]).strip() if not pd.isna(df_raw.iloc[8, 0]) else ""
            if fila_9:
                dias = self._parsear_dias_consumo(fila_9)
                if dias:
                    resultado['dias_consumo'] = dias
                    # Intentar extraer fecha de entrega del primer día
                    fecha_entrega = self._extraer_primera_fecha(dias)
                    if fecha_entrega:
                        resultado['fecha_entrega'] = fecha_entrega
        
        return resultado
    
    def _parsear_fila_programa(self, fila_4):
        """
        🔍 Parsea la fila 4 con formato: PROGRAMA:X - EMPRESA / MODALIDAD
        
        Ejemplos:
        "PROGRAMA:CONSORCIO ALIMENTANDO A CALI 2025 - CONSORCIO ALIMENTANDO A CALI 2025 / ALMUERZO JORNADA UNICA"
        
        Returns:
            dict: {'programa': str, 'empresa': str, 'modalidad': str}
        """
        resultado = {
            'programa': 'PROGRAMA NO DETECTADO',
            'empresa': 'EMPRESA NO DETECTADA', 
            'modalidad': 'MODALIDAD NO DETECTADA'
        }
        
        try:
            # Limpiar texto inicial
            texto = fila_4.strip()
            
            # ✅ PATRÓN PRINCIPAL: PROGRAMA:X - Y / Z
            patron_completo = r'PROGRAMA:\s*(.+?)\s*-\s*(.+?)\s*/\s*(.+?)$'
            match = re.search(patron_completo, texto, re.IGNORECASE)
            
            if match:
                resultado['programa'] = match.group(1).strip()
                resultado['empresa'] = match.group(2).strip()  
                resultado['modalidad'] = match.group(3).strip()
                return resultado
            
            # ✅ PATRÓN ALTERNATIVO 1: Solo PROGRAMA: - EMPRESA / MODALIDAD (sin "PROGRAMA:")
            patron_sin_prefijo = r'^(.+?)\s*-\s*(.+?)\s*/\s*(.+?)$'
            match = re.search(patron_sin_prefijo, texto)
            
            if match:
                resultado['programa'] = match.group(1).strip()
                resultado['empresa'] = match.group(2).strip()
                resultado['modalidad'] = match.group(3).strip()
                return resultado
            
            # ✅ PATRÓN ALTERNATIVO 2: Solo tiene "-" pero no "/"
            if ' - ' in texto and ' / ' not in texto:
                partes = texto.split(' - ', 1)
                if len(partes) == 2:
                    # Limpiar "PROGRAMA:" del inicio si existe
                    programa = re.sub(r'^PROGRAMA:\s*', '', partes[0], flags=re.IGNORECASE).strip()
                    resultado['programa'] = programa
                    resultado['empresa'] = partes[1].strip()
                    resultado['modalidad'] = 'NO ESPECIFICADA'
                    return resultado
            
            # ✅ PATRÓN ALTERNATIVO 3: Solo tiene "/" pero no "-"
            if ' / ' in texto and ' - ' not in texto:
                partes = texto.split(' / ', 1)
                if len(partes) == 2:
                    # Limpiar "PROGRAMA:" del inicio si existe
                    programa = re.sub(r'^PROGRAMA:\s*', '', partes[0], flags=re.IGNORECASE).strip()
                    resultado['programa'] = programa
                    resultado['empresa'] = 'NO ESPECIFICADA'
                    resultado['modalidad'] = partes[1].strip()
                    return resultado
            
            # ✅ FALLBACK: Usar todo el texto como programa
            if texto:
                # Limpiar "PROGRAMA:" del inicio si existe
                programa_limpio = re.sub(r'^PROGRAMA:\s*', '', texto, flags=re.IGNORECASE).strip()
                if programa_limpio:
                    resultado['programa'] = programa_limpio
                    # Intentar detectar empresa por palabras clave
                    if 'CONSORCIO' in programa_limpio.upper():
                        resultado['empresa'] = 'CONSORCIO ALIMENTANDO A CALI 2025'
                    elif 'VALLE SOLIDARIO' in programa_limpio.upper():
                        if 'BUGA' in programa_limpio.upper():
                            resultado['empresa'] = 'UNION TEMPORAL VALLE SOLIDARIO BUGA 2025'
                        elif 'YUMBO' in programa_limpio.upper():
                            resultado['empresa'] = 'UNION TEMPORAL VALLE SOLIDARIO YUMBO 2025'
                        else:
                            resultado['empresa'] = 'VALLE SOLIDARIO'
            
        except Exception as e:
            print(f"Error parseando fila programa: {e}")
            # Mantener valores por defecto
        
        return resultado
    
    def _parsear_solicitud_remesa(self, fila_8):
        """
        🔍 Parsea la fila 8 con formato: Solicitud Remesa: VALOR
        
        Ejemplo: "Solicitud Remesa:  MENU 6 - MENU 7 - MENU 8"
        """
        try:
            # Buscar patrón "Solicitud Remesa:" seguido del valor
            patron = r'Solicitud\s+Remesa:\s*(.+)$'
            match = re.search(patron, fila_8, re.IGNORECASE)
            
            if match:
                valor = match.group(1).strip()
                return valor if valor else None
            
            # Fallback: Si no encuentra el patrón pero contiene "solicitud"
            if 'solicitud' in fila_8.lower():
                # Intentar extraer todo después de ":"
                if ':' in fila_8:
                    valor = fila_8.split(':', 1)[1].strip()
                    return valor if valor else None
                    
        except Exception as e:
            print(f"Error parseando solicitud remesa: {e}")
        
        return None
    
    def _parsear_dias_consumo(self, fila_9):
        """
        🔍 Parsea la fila 9 con formato: Dias de consumo: VALOR
        
        Ejemplo: "Dias de consumo:  2025-07-21 - 2025-07-22 - 2025-07-23"
        """
        try:
            # Buscar patrón "Dias de consumo:" seguido del valor
            patron = r'Dias\s+de\s+consumo:\s*(.+)$'
            match = re.search(patron, fila_9, re.IGNORECASE)
            
            if match:
                valor = match.group(1).strip()
                return valor if valor else None
            
            # Fallback: Si no encuentra el patrón pero contiene "dias" o "consumo"
            if any(palabra in fila_9.lower() for palabra in ['dias', 'consumo']):
                # Intentar extraer todo después de ":"
                if ':' in fila_9:
                    valor = fila_9.split(':', 1)[1].strip()
                    return valor if valor else None
                    
        except Exception as e:
            print(f"Error parseando días de consumo: {e}")
        
        return None
    
    def _extraer_primera_fecha(self, dias_consumo_texto):
        """
        🗓️ Extrae la primera fecha del texto de días de consumo
        
        Ejemplo: "2025-07-21 - 2025-07-22 - 2025-07-23" → "2025-07-21"
        """
        try:
            # Buscar patrones de fecha YYYY-MM-DD
            patron_fecha = r'(\d{4}-\d{1,2}-\d{1,2})'
            match = re.search(patron_fecha, dias_consumo_texto)
            
            if match:
                fecha_str = match.group(1)
                # Validar que sea una fecha válida
                try:
                    datetime.strptime(fecha_str, '%Y-%m-%d')
                    return fecha_str
                except ValueError:
                    pass
            
            # Buscar otros formatos de fecha
            # Patrón DD/MM/YYYY
            patron_fecha_alt = r'(\d{1,2}/\d{1,2}/\d{4})'
            match = re.search(patron_fecha_alt, dias_consumo_texto)
            
            if match:
                fecha_str = match.group(1)
                try:
                    # Convertir a formato YYYY-MM-DD
                    fecha_obj = datetime.strptime(fecha_str, '%d/%m/%Y')
                    return fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass
                    
        except Exception as e:
            print(f"Error extrayendo primera fecha: {e}")
        
        return None
    
    def detectar_patron_rutas(self, tipo_archivo):
        """
        🛣️ Detecta el patrón de rutas según el tipo de archivo
        """
        patrones = {
            "COMEDORES_COMUNITARIOS": r"DIA\s+\d+\s*-\s*RUTA\s+\d+",
            "CONSORCIO_CONGELADOS": r"CONGELADOS\s+RUTA\s+\d+",
            "CONSORCIO_JU": r"CONGELADOS\s+RUTA\s+\d+",
            "CONSORCIO_GENERAL": r"CONGELADOS\s+RUTA\s+\d+",
            "VALLE_SOLIDARIO_BUGA": r"(DIA|CONGELADOS).*RUTA.*\d+",
            "VALLE_SOLIDARIO_YUMBO": r"(DIA|CONGELADOS).*RUTA.*\d+"
        }
        
        return patrones.get(tipo_archivo, r"(DIA|CONGELADOS).*RUTA.*\d+")
    
    def validar_informacion_extraida(self, info_extraida):
        """
        ✅ Valida que la información extraída sea coherente
        
        Returns:
            tuple: (es_valida, mensajes_error)
        """
        errores = []
        
        # Validar campos obligatorios
        if info_extraida['programa'] == 'PROGRAMA NO DETECTADO':
            errores.append("No se pudo detectar el programa en la fila 4")
        
        if info_extraida['empresa'] == 'EMPRESA NO DETECTADA':
            errores.append("No se pudo detectar la empresa en la fila 4")
        
        # Validar formato de fecha si está presente
        if info_extraida['fecha_entrega'] != datetime.now().strftime('%Y-%m-%d'):
            try:
                datetime.strptime(info_extraida['fecha_entrega'], '%Y-%m-%d')
            except ValueError:
                errores.append(f"Formato de fecha inválido: {info_extraida['fecha_entrega']}")
        
        return len(errores) == 0, errores
    
    def get_resumen_extraccion(self, info_extraida):
        """
        📋 Genera un resumen legible de la información extraída
        """
        return f"""
🔍 INFORMACIÓN EXTRAÍDA:
📋 Programa: {info_extraida['programa']}
🏢 Empresa: {info_extraida['empresa']}
🎯 Modalidad: {info_extraida['modalidad']}
📄 Solicitud Remesa: {info_extraida['solicitud_remesa']}
📅 Días de Consumo: {info_extraida['dias_consumo']}
🗓️ Fecha de Entrega: {info_extraida['fecha_entrega']}
        """