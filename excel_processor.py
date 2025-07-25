"""
📊 EXCEL_PROCESSOR.PY
Módulo principal para el procesamiento de archivos Excel
Maneja la lógica de extracción de comedores, rutas y productos
"""

import pandas as pd
import re
from datetime import datetime
from data_extractor import DataExtractor

class ExcelProcessor:
    """
    Clase principal para procesar archivos Excel de comedores/programas alimentarios
    """
    
    def __init__(self):
        self.extractor = DataExtractor()
        self.patrones_productos = {
            'carne_cerdo': {
                'palabras_clave': ['CERDO'],
                'unidades_validas': ['B X 1000', 'B X', 'KG', 'KILO'],
                'variaciones_texto': [
                    'CARNE DE CERDO MAGRA',
                    'CARNE DE CERDO',
                    'CERDO MAGRA',
                    'CERDO'
                ]
            },
            'carne_res': {
                'palabras_clave': ['RES'],
                'unidades_validas': ['KG', 'KILO'],
                'variaciones_texto': [
                    'CARNE DE RES, MAGRA',
                    'CARNE DE RES MAGRA', 
                    'CARNE DE RES',
                    'RES MAGRA',
                    'RES'
                ]
            },
            'MUSLO_CONTRAMUSLO': {
                'palabras_clave': ['MUSLO', 'CONTRAMUSLO', 'POLLO'],
                'unidades_validas': ['UND', 'UNIDADES', 'UNIDAD'],
                'variaciones_texto': [
                    'MUSLO / CONTRAMUSLO DE POLLO',
                    'MUSLO CONTRAMUSLO DE POLLO',
                    'MUSLO/CONTRAMUSLO DE POLLO',
                    'MUSLO DE POLLO',
                    'CONTRAMUSLO DE POLLO',
                    'POLLO ENTERO'
                ]
            },
            'pollo_peso': {
                'palabras_clave': ['PECHUGA', 'POLLO'],
                'unidades_validas': ['KG', 'KILO'],
                'variaciones_texto': [
                    'PECHUGA POLLO',
                    'PECHUGA DE POLLO',
                    'PECHUGA POLLO DESHUESADA',
                    'POLLO PECHUGA'
                ]
            }
        }
    
    def procesar_archivo_completo(self, archivo_excel):
        """
        🎯 FUNCIÓN PRINCIPAL: Procesa completamente un archivo Excel
        
        Args:
            archivo_excel: Archivo subido en Streamlit
            
        Returns:
            tuple: (df_procesado, num_registros, tipo_archivo, info_extraida)
        """
        try:
            # 1. LEER ARCHIVO EXCEL
            df_raw = pd.read_excel(archivo_excel, header=None)
            print(f"📊 Archivo leído: {len(df_raw)} filas, {len(df_raw.columns)} columnas")
            
            # 2. DETECTAR TIPO DE ARCHIVO
            tipo_archivo, programa_detectado = self.extractor.detectar_tipo_archivo(df_raw)
            print(f"🔍 Tipo detectado: {tipo_archivo}")
            
            # 3. EXTRAER INFORMACIÓN ESTRUCTURADA (NUEVA FUNCIONALIDAD)
            info_extraida = self.extractor.extraer_informacion_estructurada(df_raw)
            print(f"📋 Info extraída: {info_extraida}")
            
            # 4. VALIDAR INFORMACIÓN EXTRAÍDA
            es_valida, errores = self.extractor.validar_informacion_extraida(info_extraida)
            if not es_valida:
                print(f"⚠️ Advertencias en extracción: {errores}")
            
            # 5. OBTENER PATRÓN DE RUTAS
            patron_rutas = self.extractor.detectar_patron_rutas(tipo_archivo)
            print(f"🛣️ Patrón de rutas: {patron_rutas}")
            
            # 6. PROCESAR DATOS DE COMEDORES
            registros_consolidados = self._extraer_registros_comedores(
                df_raw, 
                patron_rutas, 
                tipo_archivo, 
                info_extraida
            )
            
            print(f"🏪 Registros encontrados: {len(registros_consolidados)}")
            
            # 7. CREAR DATAFRAME FINAL
            if registros_consolidados:
                df_final = self._crear_dataframe_final(registros_consolidados)
                return df_final, len(registros_consolidados), tipo_archivo, info_extraida
            else:
                print(f"❌ No se encontraron registros válidos para tipo: {tipo_archivo}")
                return None, 0, tipo_archivo, info_extraida
                
        except Exception as e:
            print(f"Error procesando archivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0, "ERROR", {}
    
    def _extraer_registros_comedores(self, df_raw, patron_rutas, tipo_archivo, info_extraida):
        """
        🏪 Extrae registros de comedores organizados por rutas
        """
        registros_consolidados = []
        
        print(f"🔍 Buscando rutas con patrón: {patron_rutas}")
        
        i = 0
        rutas_encontradas = 0
        while i < len(df_raw):
            try:
                celda = str(df_raw.iloc[i, 0]).strip()
                
                # Detectar inicio de ruta usando el patrón correspondiente
                if re.search(patron_rutas, celda, re.IGNORECASE):
                    rutas_encontradas += 1
                    print(f"🛣️ Ruta encontrada en fila {i}: {celda}")
                    
                    ruta_completa = celda
                    
                    # Extraer día y ruta según el tipo
                    dia, ruta = self._parsear_informacion_ruta(ruta_completa, tipo_archivo)
                    
                    # Buscar encabezados de la tabla
                    registros_ruta = self._procesar_ruta(
                        df_raw, i, dia, ruta, info_extraida
                    )
                    
                    print(f"📊 Comedores encontrados en esta ruta: {len(registros_ruta)}")
                    registros_consolidados.extend(registros_ruta)
                    
            except Exception as e:
                print(f"Error procesando fila {i}: {e}")
                pass
                
            i += 1
        
        print(f"📈 Resumen: {rutas_encontradas} rutas encontradas, {len(registros_consolidados)} comedores totales")
        
        # 🆘 FALLBACK: Si no encuentra rutas con el patrón, buscar patrones alternativos
        if len(registros_consolidados) == 0:
            print("🔄 No se encontraron rutas con patrón principal. Intentando patrones alternativos...")
            registros_consolidados = self._buscar_patrones_alternativos(df_raw, tipo_archivo, info_extraida)
        
        return registros_consolidados
    
    def _buscar_patrones_alternativos(self, df_raw, tipo_archivo, info_extraida):
        """
        🆘 FALLBACK: Busca patrones alternativos cuando el patrón principal falla
        """
        registros_alternativos = []
        
        print("🔍 Buscando patrones alternativos...")
        
        # Patrones alternativos para Valle Solidario
        patrones_fallback = [
            r"RUTA\s+\d+",           # "RUTA 1", "RUTA 2", etc.
            r"DIA\s+\d+",            # "DIA 1", "DIA 2", etc.
            r"ENTREGA\s+\d+",        # "ENTREGA 1", etc.
            r"GRUPO\s+\d+",          # "GRUPO 1", etc.
            r"LOTE\s+\d+",           # "LOTE 1", etc.
        ]
        
        for patron in patrones_fallback:
            print(f"🔍 Probando patrón: {patron}")
            
            for i in range(len(df_raw)):
                try:
                    celda = str(df_raw.iloc[i, 0]).strip()
                    
                    if re.search(patron, celda, re.IGNORECASE):
                        print(f"✅ Patrón encontrado en fila {i}: {celda}")
                        
                        # Usar la celda como ruta
                        ruta_completa = celda
                        dia = "DIA 1"
                        ruta = ruta_completa
                        
                        # Procesar esta "ruta"
                        registros_ruta = self._procesar_ruta(
                            df_raw, i, dia, ruta, info_extraida
                        )
                        
                        if registros_ruta:
                            print(f"📊 Comedores encontrados con patrón alternativo: {len(registros_ruta)}")
                            registros_alternativos.extend(registros_ruta)
                            break  # Si encontró datos, no seguir buscando con este patrón
                        
                except Exception as e:
                    continue
            
            # Si ya encontró datos con algún patrón, no seguir probando
            if registros_alternativos:
                break
        
        # 🆘 ÚLTIMO RECURSO: Buscar directamente tablas sin patrón de ruta
        if not registros_alternativos:
            print("🚨 Último recurso: Buscar tablas sin patrón de ruta específico")
            registros_alternativos = self._buscar_tablas_directamente(df_raw, info_extraida)
        
        return registros_alternativos
    
    def _buscar_tablas_directamente(self, df_raw, info_extraida):
        """
        🚨 ÚLTIMO RECURSO: Busca tablas de comedores directamente sin patrón de ruta
        """
        registros_directos = []
        
        print("🔍 Buscando tablas directamente...")
        
        # Buscar celdas con "N°" que indican inicio de tabla
        for i in range(len(df_raw)):
            try:
                celda = str(df_raw.iloc[i, 0]).strip()
                
                if celda == "N°" and not pd.isna(df_raw.iloc[i, 1]):
                    print(f"📋 Tabla encontrada en fila {i}")
                    
                    # Detectar columnas de productos
                    columnas_productos, fila_encabezado = self._detectar_columnas_productos(df_raw, i)
                    print(f"🔍 Columnas detectadas: {columnas_productos}")
                    
                    # Extraer datos sin ruta específica
                    comedores_datos = self._extraer_datos_comedores(
                        df_raw, i, columnas_productos, "DIA 1", "RUTA GENERAL", info_extraida
                    )
                    
                    if comedores_datos:
                        print(f"📊 Comedores extraídos directamente: {len(comedores_datos)}")
                        registros_directos.extend(comedores_datos)
                        break  # Solo procesar la primera tabla encontrada
                        
            except Exception as e:
                continue
        
        return registros_directos
    
    def _parsear_informacion_ruta(self, ruta_completa, tipo_archivo):
        """
        🛣️ Parsea información de ruta según el tipo de archivo
        """
        if tipo_archivo == "COMEDORES_COMUNITARIOS":
            if ' - ' in ruta_completa:
                dia = ruta_completa.split(' - ')[0]
                ruta = ruta_completa.split(' - ')[1]
            else:
                dia = "DIA 1"
                ruta = ruta_completa
        else:
            dia = "DIA 1"
            ruta = ruta_completa
            
        return dia, ruta
    
    def _procesar_ruta(self, df_raw, inicio_ruta, dia, ruta, info_extraida):
        """
        🏪 Procesa una ruta específica y extrae sus comedores
        """
        registros_ruta = []
        
        print(f"🔍 Procesando ruta: {ruta}")
        
        # Buscar encabezados de la tabla en las siguientes 15 filas
        for j in range(inicio_ruta + 1, min(inicio_ruta + 15, len(df_raw))):
            try:
                celda_a = str(df_raw.iloc[j, 0]).strip() if not pd.isna(df_raw.iloc[j, 0]) else ""
                celda_b = str(df_raw.iloc[j, 1]).strip() if not pd.isna(df_raw.iloc[j, 1]) else ""
                
                # Buscar diferentes indicadores de tabla
                es_inicio_tabla = (
                    celda_a == "N°" or
                    celda_a == "No." or
                    celda_a == "NUM" or
                    (celda_a.isdigit() and "MUNICIPIO" in celda_b.upper()) or
                    ("COMEDOR" in celda_b.upper() or "ESCUELA" in celda_b.upper())
                )
                
                if es_inicio_tabla and not pd.isna(df_raw.iloc[j, 1]):
                    print(f"📋 Tabla encontrada en fila {j}")
                    
                    # Detectar columnas de productos
                    columnas_productos, fila_encabezado = self._detectar_columnas_productos(df_raw, j)
                    print(f"🔍 Columnas productos: {columnas_productos}")
                    
                    # Extraer datos de comedores
                    comedores_datos = self._extraer_datos_comedores(
                        df_raw, j, columnas_productos, dia, ruta, info_extraida
                    )
                    
                    if comedores_datos:
                        print(f"📊 Comedores extraídos: {len(comedores_datos)}")
                        registros_ruta.extend(comedores_datos)
                        break
                    
            except Exception as e:
                print(f"Error en fila {j}: {e}")
                continue
        
        return registros_ruta
    
    def _detectar_columnas_productos(self, df_raw, fila_inicio):
        """
        🔍 Detecta las columnas de productos (F, G, H) con patrones específicos
        """
        # Buscar fila de encabezados en rango limitado
        for fila in range(fila_inicio, min(fila_inicio + 10, len(df_raw))):
            columnas_productos_encontradas = False
            
            # Verificar solo columnas F, G, H si existen (índices 5, 6, 7)
            for col in range(5, min(len(df_raw.columns), 8)):  # Hasta donde existan columnas
                celda = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
                
                # Verificar si contiene indicadores de productos
                if any(unidad in celda for unidades in [p['unidades_validas'] for p in self.patrones_productos.values()] for unidad in unidades):
                    columnas_productos_encontradas = True
                    break
            
            if columnas_productos_encontradas:
                # Mapear cada columna F, G, H
                columnas_detectadas = {}
                
                for col in range(5, min(8, len(df_raw.columns))):
                    encabezado_actual = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
                    
                    if encabezado_actual.strip():
                        producto_detectado = self._clasificar_producto_por_patron(encabezado_actual)
                        
                        if producto_detectado:
                            columnas_detectadas[producto_detectado] = col
                
                if columnas_detectadas:
                    return columnas_detectadas, fila
        
        # Si no encuentra patrones específicos, usar detección por contexto
        return self._detectar_por_contexto(df_raw, fila_inicio)
    
    def _clasificar_producto_por_patron(self, encabezado):
        """
        🏷️ Clasifica un encabezado de columna según los patrones específicos
        """
        encabezado_limpio = self._limpiar_texto_para_comparacion(encabezado)
        
        for producto, config in self.patrones_productos.items():
            # Verificar si contiene las palabras clave Y las unidades válidas
            tiene_palabra_clave = any(palabra in encabezado_limpio for palabra in config['palabras_clave'])
            tiene_unidad_valida = any(unidad in encabezado_limpio for unidad in config['unidades_validas'])
            
            if tiene_palabra_clave and tiene_unidad_valida:
                # Verificación adicional con variaciones específicas
                for variacion in config['variaciones_texto']:
                    variacion_limpia = self._limpiar_texto_para_comparacion(variacion)
                    if variacion_limpia in encabezado_limpio:
                        return producto
                
                # Si tiene palabra clave y unidad, pero no coincide exactamente con variaciones
                return producto
        
        return None
    
    def _limpiar_texto_para_comparacion(self, texto):
        """
        🧹 Limpia el texto para hacer comparaciones más robustas
        """
        import re
        
        # Convertir a mayúsculas
        texto_limpio = texto.upper()
        
        # Remover caracteres especiales y normalizar espacios
        texto_limpio = re.sub(r'[^\w\s]', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
        texto_limpio = texto_limpio.strip()
        
        return texto_limpio
    
    def _detectar_por_contexto(self, df_raw, fila_inicio):
        """
        🎯 Detección alternativa cuando no encuentra patrones específicos
        """
        mapeo_defecto = {}
        
        # Analizar las columnas F, G, H (si existen) y asignar por probabilidad
        for col in range(5, min(len(df_raw.columns), 8)):
            pistas_columna = []
            
            for fila in range(max(0, fila_inicio - 3), min(fila_inicio + 8, len(df_raw))):
                celda = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
                if celda.strip():
                    pistas_columna.append(celda)
            
            # Clasificar la columna basándose en todas las pistas
            producto_mas_probable = None
            for pista in pistas_columna:
                producto = self._clasificar_producto_por_patron(pista)
                if producto:
                    producto_mas_probable = producto
                    break
            
            if producto_mas_probable:
                mapeo_defecto[producto_mas_probable] = col
        
        # Si aún está vacío, aplicar reglas heurísticas (ajustado para mínimo 6 columnas)
        if not mapeo_defecto:
            mapeo_defecto['carne_cerdo'] = 5  # Columna F siempre existe
            if len(df_raw.columns) >= 7:  # Si tiene columna G
                mapeo_defecto['MUSLO_CONTRAMUSLO'] = 6
            if len(df_raw.columns) >= 8:  # Si tiene columna H
                mapeo_defecto['pollo_peso'] = 7
            elif len(df_raw.columns) >= 7 and 'MUSLO_CONTRAMUSLO' not in mapeo_defecto:
                mapeo_defecto['carne_res'] = 6  # Alternativa si solo hay 2 columnas de productos
        
        return mapeo_defecto, fila_inicio + 2
    
    def _extraer_datos_comedores(self, df_raw, inicio_tabla, columnas_productos, dia, ruta, info_extraida):
        """
        🏪 Extrae los datos de comedores de una tabla específica
        """
        comedores_datos = []
        patron_rutas = self.extractor.detectar_patron_rutas("GENERAL")
        
        # Extraer datos de comedores
        for k in range(inicio_tabla + 1, len(df_raw)):
            try:
                primera_celda = df_raw.iloc[k, 0]
                
                # Si es un número, es un comedor
                if (not pd.isna(primera_celda) and 
                    isinstance(primera_celda, (int, float)) and
                    not pd.isna(df_raw.iloc[k, 1]) and
                    not pd.isna(df_raw.iloc[k, 2])):
                    
                    # ✅ CREAR REGISTRO CON NUEVA ESTRUCTURA
                    registro = {
                        'PROGRAMA': info_extraida.get('programa', 'PROGRAMA NO DETECTADO'),
                        'EMPRESA': info_extraida.get('empresa', 'EMPRESA NO DETECTADA'),
                        'MODALIDAD': info_extraida.get('modalidad', 'MODALIDAD NO DETECTADA'),
                        'SOLICITUD_REMESA': info_extraida.get('solicitud_remesa', 'NO ESPECIFICADO'),
                        'DIAS_CONSUMO': info_extraida.get('dias_consumo', 'NO ESPECIFICADO'),
                        'FECHA_ENTREGA': info_extraida.get('fecha_entrega', datetime.now().strftime('%Y-%m-%d')),
                        'DIA': dia,
                        'RUTA': ruta,
                        'N°': int(primera_celda),
                        'MUNICIPIO': str(df_raw.iloc[k, 1]).strip(),
                        'COMEDOR/ESCUELA': str(df_raw.iloc[k, 2]).strip(),
                        'COBER': df_raw.iloc[k, 3] if not pd.isna(df_raw.iloc[k, 3]) else 0,
                        'DIRECCIÓN': str(df_raw.iloc[k, 4]).strip() if not pd.isna(df_raw.iloc[k, 4]) else "",
                    }
                    
                    # Mapear productos según las columnas detectadas
                    registro.update(self._mapear_productos(df_raw, k, columnas_productos))
                    
                    comedores_datos.append(registro)
                    
                # Si encontramos "TOTAL" o nueva "RUTA", salir del bucle
                elif (not pd.isna(primera_celda) and 
                      ("TOTAL" in str(primera_celda).upper() or 
                       re.search(patron_rutas, str(primera_celda), re.IGNORECASE))):
                    break
                    
            except Exception as e:
                continue
        
        return comedores_datos
    
    def _mapear_productos(self, df_raw, fila, columnas_productos):
        """
        🥩 Mapea los productos según las columnas detectadas
        """
        productos = {}
        
        # Mapear cada tipo de producto
        for producto_tipo in ['carne_cerdo', 'carne_res', 'MUSLO_CONTRAMUSLO', 'pollo_peso']:
            if producto_tipo in columnas_productos:
                col = columnas_productos[producto_tipo]
                valor = df_raw.iloc[fila, col] if not pd.isna(df_raw.iloc[fila, col]) else 0
                
                # Mapear al nombre de columna final
                if producto_tipo == 'carne_cerdo':
                    productos['CARNE_DE_CERDO'] = valor
                elif producto_tipo == 'carne_res':
                    productos['CARNE_DE_RES'] = valor
                elif producto_tipo == 'MUSLO_CONTRAMUSLO':
                    productos['MUSLO_CONTRAMUSLO'] = valor
                elif producto_tipo == 'pollo_peso':
                    productos['POLLO_PESO'] = valor
            else:
                # Valores por defecto
                if producto_tipo == 'carne_cerdo':
                    productos['CARNE_DE_CERDO'] = 0
                elif producto_tipo == 'carne_res':
                    productos['CARNE_DE_RES'] = 0
                elif producto_tipo == 'MUSLO_CONTRAMUSLO':
                    productos['MUSLO_CONTRAMUSLO'] = 0
                elif producto_tipo == 'pollo_peso':
                    productos['POLLO_PESO'] = 0
        
        return productos
    
    def _crear_dataframe_final(self, registros_consolidados):
        """
        📊 Crea el DataFrame final con validación y limpieza de datos
        """
        df_final = pd.DataFrame(registros_consolidados)
        
        # Limpiar y validar datos numéricos
        df_final['COBER'] = pd.to_numeric(df_final['COBER'], errors='coerce').fillna(0).astype(int)
        df_final['CARNE_DE_CERDO'] = pd.to_numeric(df_final['CARNE_DE_CERDO'], errors='coerce').fillna(0).astype(float)
        df_final['CARNE_DE_RES'] = pd.to_numeric(df_final['CARNE_DE_RES'], errors='coerce').fillna(0).astype(float)
        df_final['MUSLO_CONTRAMUSLO'] = pd.to_numeric(df_final['MUSLO_CONTRAMUSLO'], errors='coerce').fillna(0).astype(int)
        df_final['POLLO_PESO'] = pd.to_numeric(df_final['POLLO_PESO'], errors='coerce').fillna(0).astype(float)
        
        # Validar campos de texto
        for col in ['PROGRAMA', 'EMPRESA', 'MODALIDAD', 'SOLICITUD_REMESA', 'DIAS_CONSUMO']:
            df_final[col] = df_final[col].astype(str)
        
        return df_final
    
    def get_estadisticas_procesamiento(self, df_procesado):
        """
        📈 Genera estadísticas del procesamiento
        """
        if df_procesado is None or len(df_procesado) == 0:
            return {}
        
        return {
            'total_comedores': len(df_procesado),
            'total_beneficiarios': int(df_procesado['COBER'].sum()),
            'total_rutas': df_procesado['RUTA'].nunique(),
            'total_cerdo_kg': float(df_procesado['CARNE_DE_CERDO'].sum()),
            'total_res_kg': float(df_procesado['CARNE_DE_RES'].sum()),
            'total_muslo_contramuslo': int(df_procesado['MUSLO_CONTRAMUSLO'].sum()),
            'total_pollo_kg': float(df_procesado['POLLO_PESO'].sum()),
            'programa_principal': df_procesado['PROGRAMA'].iloc[0] if len(df_procesado) > 0 else "N/A",
            'empresa_principal': df_procesado['EMPRESA'].iloc[0] if len(df_procesado) > 0 else "N/A",
            'modalidad_principal': df_procesado['MODALIDAD'].iloc[0] if len(df_procesado) > 0 else "N/A"
        }