"""
📊 EXCEL_PROCESSOR.PY
Módulo principal para el procesamiento de archivos Excel
Maneja la lógica de extracción de comedores, rutas y productos
"""

import pandas as pd
import re
from datetime import datetime
from data_extractor import DataExtractor
from logger_config import logger

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
                'variaciones_texto': ['CARNE DE CERDO']  # Más estricto
            },
            'carne_res': {
                'palabras_clave': ['RES'],
                'unidades_validas': ['KG', 'KILO'],
                'variaciones_texto': ['CARNE DE RES']
            },
            'MUSLO_CONTRAMUSLO': {
                'palabras_clave': ['MUSLO', 'CONTRAMUSLO'],
                'unidades_validas': ['UND', 'UNIDADES', 'UNIDAD'],
                'variaciones_texto': ['MUSLO / CONTRAMUSLO DE POLLO', 'MUSLO CONTRAMUSLO']
            },
            'pollo_peso': {
                'palabras_clave': ['PECHUGA', 'POLLO'],  # Ambas son importantes
                'unidades_validas': ['KG', 'KILO', 'B X 1000', 'B X'],  # Añadir B X 1000
                'variaciones_texto': ['PECHUGA POLLO', 'PECHUGA DE POLLO']
            },
            'tilapia': {
                'palabras_clave': ['TILAPIA', 'PESCADO'],
                'unidades_validas': ['KG', 'KILO', 'B X 1000', 'B X'],
                'variaciones_texto': ['TILAPIA', 'FILETE DE TILAPIA']
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
        🏪 Estrategia de extracción generalizada: busca tablas directamente.
        Cualquier texto previo a una tabla se considera la "ruta".
        """
        registros_consolidados = []
        ruta_actual = "RUTA GENERAL"  # Valor por defecto si no se encuentra texto antes

        # Iteramos por cada fila para encontrar el inicio de las tablas
        for i in range(len(df_raw)):
            try:
                celda_A_str = str(df_raw.iloc[i, 0]).strip()
                celda_B_str = str(df_raw.iloc[i, 1]).strip()

                # Condición de inicio de tabla: "N°" en Col A y texto en Col B
                if celda_A_str in ["N°", "No."] and celda_B_str not in ["nan", ""]:
                    
                    # --- Lógica para encontrar el nombre de la ruta ---
                    # Buscamos hacia arriba desde la tabla para encontrar el último texto no numérico
                    for j in range(i - 1, -1, -1):
                        celda_ruta = df_raw.iloc[j, 0]
                        if not pd.isna(celda_ruta) and isinstance(celda_ruta, str) and celda_ruta.strip():
                            # Asegurarnos de que no sea parte de la información del programa
                            if "PROGRAMA:" not in celda_ruta.upper() and "EMPRESA:" not in celda_ruta.upper():
                                ruta_actual = celda_ruta.strip()
                                break  # Encontramos el título, salimos del bucle de búsqueda
                    
                    # Procesar la tabla encontrada
                    columnas_productos, _ = self._detectar_columnas_productos(df_raw, i)
                    
                    comedores_datos = self._extraer_datos_de_tabla(df_raw, i, columnas_productos, "DIA 1", ruta_actual, info_extraida)
                    
                    if comedores_datos:
                        registros_consolidados.extend(comedores_datos)
            
            except IndexError:  # Si una fila no tiene suficientes columnas
                continue
                
        return registros_consolidados
    
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
        🏷️ Clasifica un encabezado de columna con sistema de puntuación mejorado
        """
        encabezado_limpio = self._limpiar_texto_para_comparacion(encabezado)
        
        posibles_coincidencias = []

        for producto, config in self.patrones_productos.items():
            tiene_palabra_clave = any(palabra in encabezado_limpio for palabra in config['palabras_clave'])
            tiene_unidad_valida = any(unidad in encabezado_limpio for unidad in config['unidades_validas'])
            
            if tiene_palabra_clave and tiene_unidad_valida:
                # Puntuación basada en cuántas palabras clave y variaciones de texto coinciden
                score = sum(1 for palabra in config['palabras_clave'] if palabra in encabezado_limpio)
                score += sum(1 for variacion in config['variaciones_texto'] if self._limpiar_texto_para_comparacion(variacion) in encabezado_limpio)
                posibles_coincidencias.append((score, producto))
        
        if not posibles_coincidencias:
            return None

        # Ordenar por puntuación para encontrar la mejor coincidencia
        posibles_coincidencias.sort(key=lambda x: x[0], reverse=True)
        
        # Lógica de desempate: si dos productos tienen la misma puntuación,
        # preferimos el que tiene una coincidencia de 'variaciones_texto' más larga.
        if len(posibles_coincidencias) > 1 and posibles_coincidencias[0][0] == posibles_coincidencias[1][0]:
            # Implementar desempate si es necesario, o simplemente tomar el primero
            pass

        return posibles_coincidencias[0][1]
    
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
    
    def _extraer_datos_de_tabla(self, df_raw, inicio_tabla, columnas_productos, dia, ruta, info_extraida):
        """
        Lee una tabla de datos desde su inicio hasta que la estructura se rompe.
        Se detiene en filas vacías, al encontrar la palabra "TOTAL", o si los datos dejan de ser válidos.
        """
        comedores_datos = []
        for k in range(inicio_tabla + 1, len(df_raw)):
            try:
                primera_celda = df_raw.iloc[k, 0]
                
                # --- CONDICIÓN DE PARADA ROBUSTA ---
                # 1. Si la primera celda está vacía o es texto que no es un número.
                if pd.isna(primera_celda) or not isinstance(primera_celda, (int, float)):
                    # 2. Permitimos la palabra "TOTAL" como señal de fin.
                    if "TOTAL" in str(primera_celda).upper():
                        break
                    # Si es otro texto, y ya hemos leído datos, es el fin de la tabla.
                    elif len(comedores_datos) > 0:
                        break
                    # Si no, simplemente es una línea de texto que ignoramos.
                    else:
                        continue
                
                # Si es una fila de datos válida (número en col A y datos en B y C)
                if not pd.isna(df_raw.iloc[k, 1]) and not pd.isna(df_raw.iloc[k, 2]):
                    registro = {
                        'PROGRAMA': info_extraida.get('programa', 'N/A'), 'EMPRESA': info_extraida.get('empresa', 'N/A'),
                        'MODALIDAD': info_extraida.get('modalidad', 'N/A'), 'SOLICITUD_REMESA': info_extraida.get('solicitud_remesa', 'N/A'),
                        'DIAS_CONSUMO': info_extraida.get('dias_consumo', 'N/A'), 'FECHA_ENTREGA': info_extraida.get('fecha_entrega', 'N/A'),
                        'DIA': dia, 'RUTA': ruta, 'N°': int(primera_celda), 'MUNICIPIO': str(df_raw.iloc[k, 1]).strip(),
                        'COMEDOR/ESCUELA': str(df_raw.iloc[k, 2]).strip(), 'COBER': df_raw.iloc[k, 3] if not pd.isna(df_raw.iloc[k, 3]) else 0,
                        'DIRECCIÓN': str(df_raw.iloc[k, 4]).strip() if not pd.isna(df_raw.iloc[k, 4]) else "",
                    }
                    registro.update(self._mapear_productos(df_raw, k, columnas_productos))
                    comedores_datos.append(registro)
                else:
                    # Si las columnas B o C están vacías, la tabla terminó.
                    if len(comedores_datos) > 0:
                        break

            except (IndexError, ValueError):
                continue
                
        return comedores_datos
    
    def _mapear_productos(self, df_raw, fila, columnas_productos):
        """
        🥩 Mapea los productos según las columnas detectadas
        """
        productos = {}
        
        # Mapear cada tipo de producto
        for producto_tipo in ['carne_cerdo', 'carne_res', 'MUSLO_CONTRAMUSLO', 'pollo_peso', 'tilapia']:
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
                elif producto_tipo == 'tilapia':
                    productos['TILAPIA'] = valor
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
                elif producto_tipo == 'tilapia':
                    productos['TILAPIA'] = 0
        
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
        df_final['TILAPIA'] = pd.to_numeric(df_final['TILAPIA'], errors='coerce').fillna(0).astype(float)
        
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
            'total_tilapia_kg': float(df_procesado['TILAPIA'].sum()),
            'programa_principal': df_procesado['PROGRAMA'].iloc[0] if len(df_procesado) > 0 else "N/A",
            'empresa_principal': df_procesado['EMPRESA'].iloc[0] if len(df_procesado) > 0 else "N/A",
            'modalidad_principal': df_procesado['MODALIDAD'].iloc[0] if len(df_procesado) > 0 else "N/A"
        }