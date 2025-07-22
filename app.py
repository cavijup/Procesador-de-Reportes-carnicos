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
    page_title="Procesador de Reportes Universales - Programas CHVS",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def limpiar_texto_para_comparacion(texto):
    """
    Limpia el texto para hacer comparaciones más robustas
    """
    import re
    
    # Convertir a mayúsculas
    texto_limpio = texto.upper()
    
    # Remover caracteres especiales y normalizar espacios
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto_limpio)  # Reemplazar puntuación con espacios
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)      # Normalizar espacios múltiples
    texto_limpio = texto_limpio.strip()
    
    return texto_limpio

def clasificar_producto_por_patron(encabezado, patrones_productos):
    """
    Clasifica un encabezado de columna según los patrones específicos definidos
    """
    encabezado_limpio = limpiar_texto_para_comparacion(encabezado)
    
    for producto, config in patrones_productos.items():
        # Verificar si contiene las palabras clave Y las unidades válidas
        tiene_palabra_clave = any(palabra in encabezado_limpio for palabra in config['palabras_clave'])
        tiene_unidad_valida = any(unidad in encabezado_limpio for unidad in config['unidades_validas'])
        
        if tiene_palabra_clave and tiene_unidad_valida:
            # Verificación adicional con variaciones específicas
            for variacion in config['variaciones_texto']:
                variacion_limpia = limpiar_texto_para_comparacion(variacion)
                if variacion_limpia in encabezado_limpio:
                    return producto
            
            # Si tiene palabra clave y unidad, pero no coincide exactamente con variaciones
            return producto
    
    return None

def detectar_por_contexto(df_raw, fila_inicio, patrones_productos):
    """
    Detección alternativa cuando no encuentra patrones específicos
    Busca contexto en filas cercanas
    """
    # Buscar en un rango más amplio de filas
    mapeo_defecto = {}
    
    # Analizar las 3 columnas F, G, H y asignar por probabilidad
    for col in range(5, min(8, len(df_raw.columns))):
        # Buscar pistas en múltiples filas para esta columna
        pistas_columna = []
        
        for fila in range(max(0, fila_inicio - 3), min(fila_inicio + 8, len(df_raw))):
            celda = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
            if celda.strip():
                pistas_columna.append(celda)
        
        # Clasificar la columna basándose en todas las pistas
        producto_mas_probable = None
        for pista in pistas_columna:
            producto = clasificar_producto_por_patron(pista, patrones_productos)
            if producto:
                producto_mas_probable = producto
                break
        
        if producto_mas_probable:
            mapeo_defecto[producto_mas_probable] = col
    
    # Si aún está vacío, aplicar reglas heurísticas
    if not mapeo_defecto:
        # Regla 1: Cerdo usualmente en primera columna de productos (F)
        mapeo_defecto['carne_cerdo'] = 5
        
        # Regla 2: Si hay 3 columnas, probablemente es Cerdo, Pollo(UND), Pollo(KG)
        if len(df_raw.columns) >= 8:
            mapeo_defecto['MUSLO_CONTRAMUSLO'] = 6
            mapeo_defecto['pollo_peso'] = 7
        else:
            # Si hay 2 columnas, probablemente es Cerdo, Res/Pollo
            mapeo_defecto['carne_res'] = 6
    
    return mapeo_defecto, fila_inicio + 2

def detectar_columnas_productos(df_raw, fila_inicio):
    """
    Detección mejorada de columnas de productos con patrones específicos
    Busca únicamente en columnas F (5), G (6), H (7) - máximo 3 columnas de productos
    
    PATRONES ESPECÍFICOS SOPORTADOS:
    - CARNE DE CERDO MAGRA / B X 1000
    - MUSLO / CONTRAMUSLO DE POLLO UND / UND
    - PECHUGA POLLO / KG  
    - CARNE DE RES, MAGRA / KG
    - CARNE DE CERDO MAGRA / KG
    """
    
    # PATRONES DE BÚSQUEDA ESPECÍFICOS CON VARIACIONES
    patrones_productos = {
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
    
    # PASO 1: Buscar fila de encabezados en rango limitado
    for fila in range(fila_inicio, min(fila_inicio + 10, len(df_raw))):
        # Verificar solo columnas F, G, H (índices 5, 6, 7)
        columnas_productos_encontradas = False
        
        for col in range(5, min(8, len(df_raw.columns))):  # Solo columnas 5, 6, 7
            celda = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
            
            # Verificar si contiene indicadores de productos
            if any(unidad in celda for unidades in [p['unidades_validas'] for p in patrones_productos.values()] for unidad in unidades):
                columnas_productos_encontradas = True
                break
        
        if columnas_productos_encontradas:
            # PASO 2: Mapear cada columna F, G, H
            columnas_detectadas = {}
            
            for col in range(5, min(8, len(df_raw.columns))):  # Solo F, G, H
                encabezado_actual = str(df_raw.iloc[fila, col]).upper() if not pd.isna(df_raw.iloc[fila, col]) else ""
                
                if encabezado_actual.strip():  # Solo si la celda no está vacía
                    # PASO 3: Clasificar el producto usando patrones específicos
                    producto_detectado = clasificar_producto_por_patron(encabezado_actual, patrones_productos)
                    
                    if producto_detectado:
                        columnas_detectadas[producto_detectado] = col
            
            if columnas_detectadas:
                return columnas_detectadas, fila
    
    # PASO 4: Si no encuentra patrones específicos, usar detección por contexto
    return detectar_por_contexto(df_raw, fila_inicio, patrones_productos)

def detectar_tipo_archivo(df_raw):
    """
    Detecta automáticamente el tipo de archivo basado en su contenido
    Retorna: tipo_archivo, programa_detectado
    """
    for i in range(min(15, len(df_raw))):
        fila = df_raw.iloc[i, 0] if not pd.isna(df_raw.iloc[i, 0]) else ""
        fila_str = str(fila).upper()
        
        # Detectar tipo por programa
        if "COMEDORES COMUNITARIOS" in fila_str:
            return "COMEDORES_COMUNITARIOS", fila_str
        elif "CONSORCIO ALIMENTANDO A CALI" in fila_str:
            # Buscar más adelante para detectar el subtipo
            for j in range(i, min(30, len(df_raw))):
                fila_j = str(df_raw.iloc[j, 0]).upper() if not pd.isna(df_raw.iloc[j, 0]) else ""
                if "CONGELADOS RUTA" in fila_j:
                    return "CONSORCIO_CONGELADOS", fila_str
                elif "JU CALI" in fila_j or "JORNADA UNICA" in fila_j:
                    return "CONSORCIO_JU", fila_str
            return "CONSORCIO_GENERAL", fila_str
    
    return "DESCONOCIDO", "PROGRAMA NO DETECTADO"

# 🔧 AJUSTES AL ARCHIVO app.py para extraer filas 8 y 9

def extraer_informacion_encabezado_universal(df_raw, tipo_archivo):
    """
    Extrae información del programa y fecha del encabezado según el tipo de archivo
    ⭐ AHORA INCLUYE EMPRESA (fila 4), SOLICITUD_REMESA (fila 8) y DIAS_CONSUMO (fila 9)
    """
    programa = "PROGRAMA NO DETECTADO"
    fecha_entrega = None
    empresa = "EMPRESA NO ESPECIFICADA"   # ⭐ NUEVA VARIABLE
    solicitud_remesa = "NO ESPECIFICADO"  
    dias_consumo = "NO ESPECIFICADO"      
    
    # Buscar información en las primeras filas
    for i in range(min(15, len(df_raw))):
        fila = df_raw.iloc[i, 0] if not pd.isna(df_raw.iloc[i, 0]) else ""
        fila_str = str(fila).upper()
        
        # ⭐ EXTRAER EMPRESA DE LA FILA 4 (índice 3)
        if i == 3:  # Fila 4 (índice base 0)
            empresa_raw = str(df_raw.iloc[i, 0]).strip() if not pd.isna(df_raw.iloc[i, 0]) else ""
            if empresa_raw:
                empresa = extraer_empresa_del_texto(empresa_raw)
        
        # ⭐ EXTRAER SOLICITUD DE REMESA (FILA 8, índice 7)
        if i == 7:  # Fila 8 (índice base 0)
            solicitud_remesa_raw = str(df_raw.iloc[i, 0]).strip() if not pd.isna(df_raw.iloc[i, 0]) else ""
            if solicitud_remesa_raw:
                # Limpiar el texto de "Solicitud Remesa:" si está presente
                solicitud_remesa = solicitud_remesa_raw.replace("Solicitud Remesa:", "").strip()
                if not solicitud_remesa:
                    solicitud_remesa = solicitud_remesa_raw  # Si queda vacío, usar el original
            
        # ⭐ EXTRAER DÍAS DE CONSUMO (FILA 9, índice 8)  
        if i == 8:  # Fila 9 (índice base 0)
            dias_consumo_raw = str(df_raw.iloc[i, 0]).strip() if not pd.isna(df_raw.iloc[i, 0]) else ""
            if dias_consumo_raw:
                # Limpiar el texto de "Dias de consumo:" si está presente
                dias_consumo = dias_consumo_raw.replace("Dias de consumo:", "").strip()
                if not dias_consumo:
                    dias_consumo = dias_consumo_raw  # Si queda vacío, usar el original
        
        # Buscar programa según el tipo (código original)
        if tipo_archivo == "COMEDORES_COMUNITARIOS":
            if "COMEDORES COMUNITARIOS" in fila_str:
                programa = fila_str
        elif tipo_archivo.startswith("CONSORCIO"):
            if "CONSORCIO ALIMENTANDO" in fila_str:
                programa = fila_str
                
        # Buscar fecha de entrega (código original)
        if "ENTREGA" in fila_str or "ELABORACIÓN" in fila_str or "DESPACHO" in fila_str:
            # Patrón para fechas tipo "2025-07-21"
            fecha_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', fila_str)
            if fecha_match:
                fecha_entrega = fecha_match.group(1)
            else:
                # Patrón para fechas tipo "21 JULIO"
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
                    
    return programa, fecha_entrega, empresa, solicitud_remesa, dias_consumo  # ⭐ RETORNAR 5 VALORES

def extraer_empresa_del_texto(texto_completo):
    """
    Extrae la empresa del texto de la fila 4
    Formato esperado: "PROGRAMA:CONSORCIO ALIMENTANDO A CALI 2025 - CONSORCIO ALIMENTANDO A CALI 2025 / ALMUERZO JORNADA UNICA"
    Objetivo: Extraer el texto entre "-" y "/"
    
    ⭐ NUEVA FUNCIÓN ESPECÍFICA PARA EXTRAER EMPRESA
    """
    try:
        # Convertir a string y limpiar
        texto = str(texto_completo).strip()
        
        # Buscar el patrón: texto después de "-" y antes de "/"
        # Ejemplo: "PROGRAMA:... - CONSORCIO ALIMENTANDO A CALI 2025 / ALMUERZO..."
        if " - " in texto and " / " in texto:
            # Dividir por " - " y tomar la parte después
            parte_despues_guion = texto.split(" - ", 1)[1]  # Tomar solo el primer split
            
            # Dividir por " / " y tomar la parte antes
            empresa_extraida = parte_despues_guion.split(" / ")[0]
            
            # Limpiar espacios adicionales
            empresa_final = empresa_extraida.strip()
            
            # Verificar que no esté vacía
            if empresa_final:
                return empresa_final
        
        # ⭐ PATRONES ALTERNATIVOS SI NO ENCUENTRA EL FORMATO PRINCIPAL
        
        # Patrón alternativo 1: Solo hay "-" pero no "/"
        if " - " in texto and " / " not in texto:
            empresa_extraida = texto.split(" - ", 1)[1].strip()
            if empresa_extraida:
                return empresa_extraida
        
        # Patrón alternativo 2: Buscar "CONSORCIO" directamente
        if "CONSORCIO" in texto.upper():
            # Buscar la palabra CONSORCIO y tomar hasta el final o hasta "/"
            texto_upper = texto.upper()
            inicio_consorcio = texto_upper.find("CONSORCIO")
            if inicio_consorcio != -1:
                texto_desde_consorcio = texto[inicio_consorcio:]
                # Si hay "/", tomar hasta ahí
                if " / " in texto_desde_consorcio:
                    empresa_extraida = texto_desde_consorcio.split(" / ")[0].strip()
                else:
                    empresa_extraida = texto_desde_consorcio.strip()
                
                if empresa_extraida:
                    return empresa_extraida
        
        # ⭐ PATRÓN ALTERNATIVO 3: Buscar por "ALIMENTANDO"
        if "ALIMENTANDO" in texto.upper():
            texto_upper = texto.upper()
            # Buscar desde antes de "ALIMENTANDO" hasta después
            palabras = texto.split()
            indices_alimentando = [i for i, palabra in enumerate(palabras) if "ALIMENTANDO" in palabra.upper()]
            
            if indices_alimentando:
                # Tomar desde 2 palabras antes hasta 4 palabras después de "ALIMENTANDO"
                idx = indices_alimentando[0]
                inicio = max(0, idx - 2)
                fin = min(len(palabras), idx + 5)
                empresa_candidata = " ".join(palabras[inicio:fin])
                
                # Limpiar caracteres no deseados
                empresa_candidata = empresa_candidata.replace("PROGRAMA:", "").strip()
                if empresa_candidata:
                    return empresa_candidata
        
        # Si no encuentra ningún patrón, devolver texto limpio o valor por defecto
        texto_limpio = texto.replace("PROGRAMA:", "").strip()
        if len(texto_limpio) > 5:  # Si tiene contenido mínimo
            return texto_limpio[:50]  # Limitar a 50 caracteres
        
    except Exception as e:
        # En caso de error, registrar y devolver valor por defecto
        print(f"Error extrayendo empresa: {e}")
    
    # Valor por defecto si no se puede extraer
    return "CONSORCIO ALIMENTANDO A CALI 2025"



def detectar_patron_rutas(df_raw, tipo_archivo):
    """
    Detecta el patrón de rutas según el tipo de archivo
    """
    patrones = {
        "COMEDORES_COMUNITARIOS": r"DIA\s+\d+\s*-\s*RUTA\s+\d+",
        "CONSORCIO_CONGELADOS": r"CONGELADOS\s+RUTA\s+\d+",
        "CONSORCIO_JU": r"CONGELADOS\s+RUTA\s+\d+",
        "CONSORCIO_GENERAL": r"CONGELADOS\s+RUTA\s+\d+"
    }
    
    patron = patrones.get(tipo_archivo, r"(DIA|CONGELADOS).*RUTA.*\d+")
    return patron

def procesar_archivo_universal(archivo):
    """
    Procesador universal que detecta el tipo de archivo y aplica la lógica correspondiente
    ⭐ ACTUALIZADO PARA INCLUIR EMPRESA, SOLICITUD_REMESA Y DIAS_CONSUMO
    """
    try:
        # Leer archivo Excel
        df_raw = pd.read_excel(archivo, header=None)
        
        # 1. DETECTAR TIPO DE ARCHIVO
        tipo_archivo, programa_detectado = detectar_tipo_archivo(df_raw)
        
        st.info(f"🔍 **Tipo detectado**: {tipo_archivo}")
        st.info(f"📋 **Programa**: {programa_detectado}")
        
        # 2. EXTRAER INFORMACIÓN DEL ENCABEZADO ⭐ AHORA INCLUYE 5 VALORES
        programa, fecha_entrega, empresa, solicitud_remesa, dias_consumo = extraer_informacion_encabezado_universal(df_raw, tipo_archivo)
        
        # ⭐ MOSTRAR LOS DATOS EXTRAÍDOS
        st.info(f"🏢 **Empresa**: {empresa}")
        st.info(f"📄 **Solicitud Remesa**: {solicitud_remesa}")
        st.info(f"📅 **Días de Consumo**: {dias_consumo}")
        
        # 3. OBTENER PATRÓN DE RUTAS
        patron_rutas = detectar_patron_rutas(df_raw, tipo_archivo)
        
        # Lista para almacenar todos los registros
        registros_consolidados = []
        
        # 4. BUSCAR BLOQUES DE RUTAS (código original hasta línea de creación del registro)
        i = 0
        while i < len(df_raw):
            try:
                celda = str(df_raw.iloc[i, 0]).strip()
                
                # Detectar inicio de ruta usando el patrón correspondiente
                if re.search(patron_rutas, celda, re.IGNORECASE):
                    ruta_completa = celda
                    
                    # Extraer día y ruta según el tipo
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
                    
                    # 5. BUSCAR ENCABEZADOS DE LA TABLA
                    for j in range(i + 1, min(i + 15, len(df_raw))):
                        try:
                            if (not pd.isna(df_raw.iloc[j, 0]) and 
                                str(df_raw.iloc[j, 0]).strip() == "N°" and
                                not pd.isna(df_raw.iloc[j, 1])):
                                
                                # Detectar columnas de productos con la función mejorada
                                columnas_productos, fila_encabezado = detectar_columnas_productos(df_raw, j)
                                
                                # 6. EXTRAER DATOS DE COMEDORES
                                for k in range(j + 1, len(df_raw)):
                                    try:
                                        primera_celda = df_raw.iloc[k, 0]
                                        
                                        # Si es un número, es un comedor
                                        if (not pd.isna(primera_celda) and 
                                            isinstance(primera_celda, (int, float)) and
                                            not pd.isna(df_raw.iloc[k, 1]) and
                                            not pd.isna(df_raw.iloc[k, 2])):
                                            
                                            # ⭐ CREAR REGISTRO CON LA NUEVA COLUMNA EMPRESA
                                            registro = {
                                                'PROGRAMA': programa,
                                                'TIPO_ARCHIVO': tipo_archivo,
                                                'FECHA_ENTREGA': fecha_entrega or "2025-07-15",
                                                'EMPRESA': empresa,                       # ⭐ NUEVA COLUMNA
                                                'SOLICITUD_REMESA': solicitud_remesa,    
                                                'DIAS_CONSUMO': dias_consumo,            
                                                'DIA': dia,
                                                'RUTA': ruta,
                                                'N°': int(primera_celda),
                                                'MUNICIPIO': str(df_raw.iloc[k, 1]).strip(),
                                                'COMEDOR/ESCUELA': str(df_raw.iloc[k, 2]).strip(),
                                                'COBER': df_raw.iloc[k, 3] if not pd.isna(df_raw.iloc[k, 3]) else 0,
                                                'DIRECCIÓN': str(df_raw.iloc[k, 4]).strip() if not pd.isna(df_raw.iloc[k, 4]) else "",
                                            }
                                            
                                            # Mapear productos según las columnas detectadas (código original)
                                            if 'carne_cerdo' in columnas_productos:
                                                col_cerdo = columnas_productos['carne_cerdo']
                                                registro['CARNE_DE_CERDO'] = df_raw.iloc[k, col_cerdo] if not pd.isna(df_raw.iloc[k, col_cerdo]) else 0
                                            else:
                                                registro['CARNE_DE_CERDO'] = 0
                                                
                                            if 'carne_res' in columnas_productos:
                                                col_res = columnas_productos['carne_res']
                                                registro['CARNE_DE_RES'] = df_raw.iloc[k, col_res] if not pd.isna(df_raw.iloc[k, col_res]) else 0
                                            else:
                                                registro['CARNE_DE_RES'] = 0
                                                
                                            if 'MUSLO_CONTRAMUSLO' in columnas_productos:
                                                col_pollo_und = columnas_productos['MUSLO_CONTRAMUSLO']
                                                registro['MUSLO_CONTRAMUSLO'] = df_raw.iloc[k, col_pollo_und] if not pd.isna(df_raw.iloc[k, col_pollo_und]) else 0
                                            else:
                                                registro['MUSLO_CONTRAMUSLO'] = 0
                                                
                                            if 'pollo_peso' in columnas_productos:
                                                col_pollo_peso = columnas_productos['pollo_peso']
                                                registro['POLLO_PESO'] = df_raw.iloc[k, col_pollo_peso] if not pd.isna(df_raw.iloc[k, col_pollo_peso]) else 0
                                            else:
                                                registro['POLLO_PESO'] = 0
                                            
                                            registros_consolidados.append(registro)
                                            
                                        # Si encontramos "TOTAL" o nueva "RUTA", salir del bucle
                                        elif (not pd.isna(primera_celda) and 
                                              ("TOTAL" in str(primera_celda).upper() or 
                                               re.search(patron_rutas, str(primera_celda), re.IGNORECASE))):
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
            
        # 7. CREAR DATAFRAME FINAL
        if registros_consolidados:
            df_final = pd.DataFrame(registros_consolidados)
            
            # Limpiar y validar datos (código original + nueva columna)
            df_final['COBER'] = pd.to_numeric(df_final['COBER'], errors='coerce').fillna(0).astype(int)
            df_final['CARNE_DE_CERDO'] = pd.to_numeric(df_final['CARNE_DE_CERDO'], errors='coerce').fillna(0).astype(float)
            df_final['CARNE_DE_RES'] = pd.to_numeric(df_final['CARNE_DE_RES'], errors='coerce').fillna(0).astype(float)
            df_final['MUSLO_CONTRAMUSLO'] = pd.to_numeric(df_final['MUSLO_CONTRAMUSLO'], errors='coerce').fillna(0).astype(int)
            df_final['POLLO_PESO'] = pd.to_numeric(df_final['POLLO_PESO'], errors='coerce').fillna(0).astype(float)
            
            # ⭐ LAS NUEVAS COLUMNAS SON STRINGS, NO NECESITAN CONVERSIÓN NUMÉRICA
            df_final['EMPRESA'] = df_final['EMPRESA'].astype(str)
            df_final['SOLICITUD_REMESA'] = df_final['SOLICITUD_REMESA'].astype(str)
            df_final['DIAS_CONSUMO'] = df_final['DIAS_CONSUMO'].astype(str)
            
            return df_final, len(registros_consolidados), tipo_archivo
        else:
            return None, 0, tipo_archivo
            
    except Exception as e:
        st.error(f"Error procesando el archivo: {str(e)}")
        return None, 0, "ERROR"



def crear_excel_descarga_universal(df, tipo_archivo):
    """
    Crea un archivo Excel optimizado para descarga con información del tipo
    ⭐ ACTUALIZADO PARA INCLUIR LA NUEVA COLUMNA EMPRESA EN EL RESUMEN
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja principal con datos
        df.to_excel(writer, sheet_name='Datos_Procesados', index=False)
        
        # ⭐ HOJA DE RESUMEN MEJORADA CON NUEVA COLUMNA
        resumen_data = {
            'Métrica': [
                'Tipo de Archivo',
                'Empresa',                       # ⭐ NUEVA FILA
                'Total Comedores',
                'Total Beneficiarios', 
                'Total Carne de Cerdo (kg)',
                'Total Carne de Res (kg)',
                'Total Pollo Unidades',
                'Total Pollo Peso (kg)',
                'Total Rutas',
                'Solicitud Remesa',              
                'Días de Consumo',               
                'Fecha de Procesamiento'
            ],
            'Valor': [
                tipo_archivo,
                df['EMPRESA'].iloc[0] if len(df) > 0 else "N/A",        # ⭐ NUEVA LÍNEA
                len(df),
                df['COBER'].sum(),
                df['CARNE_DE_CERDO'].sum(),
                df['CARNE_DE_RES'].sum(),
                df['MUSLO_CONTRAMUSLO'].sum(),  
                df['POLLO_PESO'].sum(),
                df['RUTA'].nunique(),
                df['SOLICITUD_REMESA'].iloc[0] if len(df) > 0 else "N/A",  
                df['DIAS_CONSUMO'].iloc[0] if len(df) > 0 else "N/A",       
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Resto del código original...
        # Hoja de análisis por ruta (sin cambios)
        df_por_ruta = df.groupby('RUTA').agg({
            'COMEDOR/ESCUELA': 'count',
            'COBER': 'sum',
            'CARNE_DE_CERDO': 'sum',
            'CARNE_DE_RES': 'sum',
            'MUSLO_CONTRAMUSLO': 'sum',
            'POLLO_PESO': 'sum'
        }).round(2)
        
        df_por_ruta.columns = ['Comedores', 'Total_Beneficiarios', 'Total_Cerdo_kg', 'Total_Res_kg', 'Total_muslo_contramuslo_Und', 'Total_Pollo_kg']
        df_por_ruta.to_excel(writer, sheet_name='Analisis_Por_Ruta')
        
        # Hoja de análisis por tipo de archivo (sin cambios)
        if 'TIPO_ARCHIVO' in df.columns:
            df_por_tipo = df.groupby('TIPO_ARCHIVO').agg({
                'COMEDOR/ESCUELA': 'count',
                'COBER': 'sum',
                'CARNE_DE_CERDO': 'sum',
                'CARNE_DE_RES': 'sum',
                'MUSLO_CONTRAMUSLO': 'sum',
                'POLLO_PESO': 'sum'
            }).round(2)
            
            df_por_tipo.columns = ['Comedores', 'Total_Beneficiarios', 'Total_Cerdo_kg', 'Total_Res_kg', 'Total_muslo_contramuslo_Und', 'Total_Pollo_kg']
            df_por_tipo.to_excel(writer, sheet_name='Analisis_Por_Tipo')
        
    output.seek(0)
    return output

def main():
    # Título principal
    st.title("🍽️ Procesador Universal de Reportes - Programas CHVS")
    st.markdown("---")
    
    # Sidebar con información
    with st.sidebar:
        st.header("📋 Información")
        st.markdown("""
        
        **Detección inteligente de productos:**
        
        ✅ **CARNE DE CERDO MAGRA / B X 1000**  
        ✅ **MUSLO / CONTRAMUSLO DE POLLO UND / UND**  
        ✅ **PECHUGA POLLO / KG**  
        ✅ **CARNE DE RES, MAGRA / KG**  
        ✅ **CARNE DE CERDO MAGRA / KG**  
        """)
        
        # Mostrar estado de PDFs
        if PDF_DISPONIBLE:
            st.success("✅ Generación de PDFs habilitada")
        else:
            st.warning("⚠️ PDFs no disponibles\n\nInstala: `pip install reportlab`")
        
        st.markdown("---")
        st.markdown("**Desarrollado para:**  \nTodos los programas CHVS - PAE y Comedores")
    
    # Crear tabs para organizar la funcionalidad
    tab1, tab2 = st.tabs(["📊 Procesar Datos", "📄 Generar PDFs"])
    
    with tab1:
        # Área principal de procesamiento
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("📁 Cargar Archivo")
            archivo_subido = st.file_uploader(
                "Selecciona cualquier archivo Excel de reportes",
                type=['xlsx', 'xls'],
                help="Soporta: Comedores Comunitarios, Consorcio Alimentando (Congelados/JU), PAE"
            )
            
        with col2:
            st.header("📊 Estado")
            if archivo_subido is None:
                st.info("Esperando archivo...")
            else:
                st.success("Archivo cargado ✅")
        
        # Procesar archivo si se ha subido
        if archivo_subido is not None:
            with st.spinner("🔄 Analizando y procesando archivo..."):
                df_procesado, num_registros, tipo_archivo = procesar_archivo_universal(archivo_subido)
                
            if df_procesado is not None and num_registros > 0:
                # Guardar en session_state para uso en tab de PDFs
                st.session_state.df_procesado = df_procesado
                st.session_state.tipo_archivo = tipo_archivo
                
                st.success(f"✅ Archivo procesado exitosamente! {num_registros} comedores encontrados")
                
                # Mostrar información del tipo detectado
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tipo de Archivo", tipo_archivo)
                with col2:
                    programa_unico = df_procesado['PROGRAMA'].iloc[0] if len(df_procesado) > 0 else "N/A"
                    st.metric("Programa", programa_unico[:30] + "..." if len(programa_unico) > 30 else programa_unico)
                
                # Mostrar métricas principales
                st.header("📊 Resumen del Procesamiento")
                
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.metric("Comedores", len(df_procesado))
                with col2:
                    st.metric("Beneficiarios", f"{df_procesado['COBER'].sum():,}")
                with col3:
                    st.metric("Rutas", df_procesado['RUTA'].nunique())
                with col4:
                    st.metric("Cerdo (kg)", f"{df_procesado['CARNE_DE_CERDO'].sum():,.1f}")
                with col5:
                    st.metric("Res (kg)", f"{df_procesado['CARNE_DE_RES'].sum():,.1f}")
                with col6:
                    st.metric("Pollo (kg)", f"{df_procesado['POLLO_PESO'].sum():,.1f}")
                
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
                    'CARNE_DE_RES': 'sum',
                    'MUSLO_CONTRAMUSLO': 'sum',
                    'POLLO_PESO': 'sum'
                }).round(2)
                
                df_analisis.columns = ['Comedores', 'Beneficiarios', 'Cerdo_kg', 'Res_kg', 'Total_muslo_contramuslo_Und', 'Pollo_kg']
                
                st.dataframe(df_analisis, use_container_width=True)
                
                # Mostrar información de detección de columnas
                with st.expander("🔍 Información de Detección de Columnas"):
                    st.markdown(f"""
                    **Detección realizada para tipo**: `{tipo_archivo}`
                    
                    **Productos detectados en el archivo:**
                    """)
                    
                    # Mostrar qué productos fueron detectados
                    productos_detectados = []
                    if df_procesado['CARNE_DE_CERDO'].sum() > 0:
                        productos_detectados.append("🐷 Carne de Cerdo")
                    if df_procesado['CARNE_DE_RES'].sum() > 0:
                        productos_detectados.append("🐄 Carne de Res")  
                    if df_procesado['MUSLO_CONTRAMUSLO'].sum() > 0:
                        productos_detectados.append("🐔 Pollo (Unidades)")
                    if df_procesado['POLLO_PESO'].sum() > 0:
                        productos_detectados.append("🐔 Pollo (Peso)")
                    
                    for producto in productos_detectados:
                        st.success(f"✅ {producto}")
                    
                    st.info("💡 La detección se realiza automáticamente analizando las columnas F, G, H según los patrones específicos de cada tipo de archivo.")
                
                # Botón de descarga
                st.header("💾 Descargar Resultado")
                
                archivo_excel = crear_excel_descarga_universal(df_procesado, tipo_archivo)
                fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f"datos_procesados_{tipo_archivo}_{fecha_actual}.xlsx"
                
                st.download_button(
                    label="📥 Descargar Excel Procesado",
                    data=archivo_excel,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Descarga el archivo Excel con los datos normalizados y análisis"
                )
                
                # Información adicional
                with st.expander("ℹ️ Información del archivo descargado"):
                    st.markdown(f"""
                    **El archivo Excel contiene 4 hojas:**
                    
                    1. **Datos_Procesados**: Datos principales normalizados
                    2. **Resumen**: Estadísticas generales (incluye tipo: {tipo_archivo})
                    3. **Analisis_Por_Ruta**: Agregaciones por ruta
                    4. **Analisis_Por_Tipo**: Comparación por tipo de archivo
                    
                    **Mejoras en esta versión v2.0:**
                    - ✅ Detección inteligente de productos específicos
                    - ✅ Mapeo robusto limitado a columnas F-H
                    - ✅ Soporte para variaciones de nombres
                    - ✅ Manejo de patrones "B X 1000", "UND", "KG"
                    - ✅ Clasificación automática por contexto
                    - ✅ Fallback inteligente con heurísticas
                    
                    **Columnas incluidas:**
                    - `TIPO_ARCHIVO`: Identifica el tipo detectado
                    - `CARNE_DE_CERDO`: Mapeo dinámico (KG o B X 1000)
                    - `CARNE_DE_RES`: Solo cuando está presente
                    - `MUSLO_CONTRAMUSLO`: Muslo/contramuslo cuando aplica
                    - `POLLO_PESO`: Pechuga en KG cuando aplica
                    """)
                    
            else:
                st.error(f"❌ No se pudieron procesar los datos del archivo tipo '{tipo_archivo}'. Verifica que sea un reporte válido.")
                
                with st.expander("🔧 Ayuda para resolución de problemas"):
                    st.markdown("""
                    **Tipos de archivos soportados:**
                    
                    1. **Comedores Comunitarios**: Rutas formato "DIA X - RUTA Y"
                    2. **Consorcio Alimentando**: Rutas formato "CONGELADOS RUTA X"
                    3. **PAE**: Archivos con programas del PAE
                    
                    **Productos específicos que busca:**
                    - `CARNE DE CERDO MAGRA / B X 1000`
                    - `MUSLO / CONTRAMUSLO DE POLLO UND / UND`
                    - `PECHUGA POLLO / KG`
                    - `CARNE DE RES, MAGRA / KG`
                    - `CARNE DE CERDO MAGRA / KG`
                    
                    **Verifica que el archivo contenga:**
                    - Información del programa en el encabezado
                    - Bloques organizados por rutas
                    - Tablas con comedores y sus datos
                    - Columnas de productos en posiciones F, G, H
                    - Encabezados con los nombres específicos listados arriba
                    
                    **Ubicación de columnas:**
                    - La detección se limita a columnas F (6), G (7), H (8)
                    - Los productos deben tener nombres descriptivos
                    - Las unidades deben estar especificadas (KG, UND, B X 1000)
                    """)
    
    with tab2:
        # Tab para generación de PDFs con selectores personalizados
        if PDF_DISPONIBLE:
            from pdf_generator import GeneradorPDFsRutas
            nombres = [
                "Shirley Paola Ibarra", "Jeferson Soto", "Alexandra Luna", "Alexander Molina",
                "Leidy Guzman", "Andres Montenegro", "Isabela Pantoja", "Luis Rodriguez"
            ]
            dictamenes = ["APROBADO", "APROBADO CONDICIONADO"]
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                boton_ruta = st.button("📋 Un PDF por ruta")
            with col2:
                boton_comedor = st.button("🏪 Un PDF por comedor")
            with col3:
                nombre_seleccionado = st.selectbox("Elaborado por:", nombres)
            dictamen_seleccionado = st.selectbox("Dictamen:", dictamenes)

            # ⭐ NUEVA SECCIÓN: Configuración de Lotes
            st.subheader("🏷️ Configuración de Lotes (Opcional)")
            st.info("💡 Si no completas estos campos, se generarán lotes automáticamente")
            col_lotes1, col_lotes2 = st.columns(2)
            with col_lotes1:
                lote_cerdo = st.text_input("🐷 Lote Carne de Cerdo:", placeholder="Ej: CERDO-2025-001")
                lote_muslo = st.text_input("🐔 Lote Muslo/Contramuslo:", placeholder="Ej: MC-2025-A1")
            with col_lotes2:
                lote_pechuga = st.text_input("🐔 Lote Pechuga Pollo:", placeholder="Ej: POLLO-240122")
                lote_res = st.text_input("🐄 Lote Carne de Res:", placeholder="Ej: RES-010225")

            lotes_personalizados = {
                'cerdo': lote_cerdo.strip() if lote_cerdo.strip() else None,
                'pechuga': lote_pechuga.strip() if lote_pechuga.strip() else None,
                'muslo': lote_muslo.strip() if lote_muslo.strip() else None,
                'res': lote_res.strip() if lote_res.strip() else None
            }

            if 'df_procesado' in st.session_state:
                generador = GeneradorPDFsRutas()
                if boton_ruta:
                    zip_buffer, total_pdfs = generador.generar_todos_los_pdfs(
                        st.session_state.df_procesado,
                        modo="por_ruta",
                        elaborado_por=nombre_seleccionado,
                        dictamen=dictamen_seleccionado,
                        lotes_personalizados=lotes_personalizados
                    )
                    st.success(f"ZIP generado con {total_pdfs} PDFs por ruta.")
                    st.download_button(
                        label="Descargar ZIP de PDFs por ruta",
                        data=zip_buffer,
                        file_name="PDFs_por_ruta.zip",
                        mime="application/zip"
                    )
                if boton_comedor:
                    zip_buffer, total_pdfs = generador.generar_todos_los_pdfs(
                        st.session_state.df_procesado,
                        modo="por_comedor",
                        elaborado_por=nombre_seleccionado,
                        dictamen=dictamen_seleccionado,
                        lotes_personalizados=lotes_personalizados
                    )
                    st.success(f"ZIP generado con {total_pdfs} PDFs por comedor.")
                    st.download_button(
                        label="Descargar ZIP de PDFs por comedor",
                        data=zip_buffer,
                        file_name="PDFs_por_comedor.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("Primero procesa un archivo en la pestaña de datos.")
        else:
            st.error("🚫 **Funcionalidad de PDFs no disponible**")
            st.markdown("""
            Para habilitar la generación de PDFs, instala las dependencias necesarias:
            
            ```bash
            pip install reportlab
            ```
            
            Luego reinicia la aplicación.
            """)
            st.info("💡 Los PDFs generarán guías de transporte individuales por ruta, basadas en el formato oficial y adaptadas al tipo de archivo detectado.")

if __name__ == "__main__":
    main()