from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from datetime import datetime
import random
import os

class PlantillaGuiaTransporte:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Configura los estilos personalizados para el documento"""
        # Estilo para encabezado principal
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=1,
            spaceBefore=0,
            alignment=1,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=9
        )
        
        # Estilo para información del programa
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=1,
            spaceBefore=0,
            alignment=1,
            textColor=colors.black,
            fontName='Helvetica',
            leading=9
        )
        
        # Estilo para secciones importantes
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=2,
            spaceBefore=0,
            alignment=1,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=9
        )        
        
        # Estilo para información alineada a la izquierda
        self.left_info_style = ParagraphStyle(
            'LeftInfoStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=1,
            spaceBefore=0,
            alignment=0,
            textColor=colors.black,
            fontName='Helvetica',
            leading=9
        )

    def generar_temperatura_aleatoria(self):
        """Genera una temperatura aleatoria entre -18°C y -10°C"""
        return random.randint(-18, -10)
    
    def generar_lote_aleatorio(self):
        """Genera un número de lote aleatorio"""
        return random.randint(1000, 9999)

    def dividir_lote_inteligente(self, lote_texto, max_chars_por_linea=8):
        """
        Divide un lote largo en múltiples líneas para evitar desbordamiento
        """
        if not lote_texto or len(str(lote_texto)) <= max_chars_por_linea:
            return str(lote_texto)
            
        lote_str = str(lote_texto).strip()
        
        # Si tiene guiones, dividir por ellos
        if '-' in lote_str:
            partes = lote_str.split('-')
            lineas = []
            linea_actual = partes[0]
            for parte in partes[1:]:
                if len(linea_actual + '-' + parte) <= max_chars_por_linea:
                    linea_actual += '-' + parte
                else:
                    lineas.append(linea_actual)
                    linea_actual = parte
            if linea_actual:
                lineas.append(linea_actual)
            return '\n'.join(lineas)
        # Si no tiene guiones, dividir por caracteres
        else:
            lineas = []
            for i in range(0, len(lote_str), max_chars_por_linea):
                lineas.append(lote_str[i:i + max_chars_por_linea])
            return '\n'.join(lineas)

    def crear_encabezado(self, datos_programa, numero_guia=None):
        """
        Crea el encabezado completo del documento
        """
        elementos = []
        
        # Número de guía
        if not numero_guia:
            numero_guia = "001-001"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        titulo_guia = Paragraph(
            f"GUIA DE TRANSPORTE No. {numero_guia} - {timestamp}",
            self.title_style
        )
        elementos.append(titulo_guia)
        elementos.append(Spacer(1, 0.05*cm))

        # Información del programa
        programa_text = f"PROGRAMA: {datos_programa.get('programa', 'COMEDORES COMUNITARIOS CALI 2025')}"
        elementos.append(Paragraph(programa_text, self.header_style))

        empresa = datos_programa.get('empresa', 'CONSORCIO ALIMENTANDO A CALI 2025')
        direccion = f"{empresa} / DIRECCION: CL 15 No. 26 - 101 BG 34/ YUMBO- VALLE DEL CAUCA"
        elementos.append(Paragraph(direccion, self.header_style))

        # Código de inscripción
        codigo = "CODIGO DE INSCRIPCION No. 76892-8050291700"
        elementos.append(Paragraph(codigo, self.header_style))

        elementos.append(Spacer(1, 0.05*cm))

        # Lista de peso
        lista_peso = "LISTA DE PESO MATERIA PRIMA - CARNES LACTEOS Y QUESOS - TODOS LOS PRODUCTOS - TODOS LOS DIAS"
        elementos.append(Paragraph(lista_peso, self.section_style))

        # Información de despacho
        fecha_elaboracion = datetime.now().strftime('%Y-%m-%d')
        despacho_info = f"DESPACHO: CP AM CALI - FECHA ELABORACIÓN: {fecha_elaboracion}"
        elementos.append(Paragraph(despacho_info, self.header_style))

        fecha_despacho = datos_programa.get('fecha_entrega', datetime.now().strftime('%Y-%m-%d'))
        elementos.append(Paragraph(f"Fecha despacho: {fecha_despacho}", self.left_info_style))
        
        dictamen = datos_programa.get('dictamen', 'APROBADO')
        elementos.append(Paragraph(f"DICTAMEN: {dictamen}", self.left_info_style))
        
        solicitud_remesa = datos_programa.get('solicitud_remesa', 'MENUS PARA 10 DIAS')
        elementos.append(Paragraph(f"Solicitud Remesa: {solicitud_remesa}", self.left_info_style))
        
        dias_consumo = datos_programa.get('dias_consumo', f"{fecha_despacho} - {fecha_despacho}")
        elementos.append(Paragraph(f"Dias de consumo: {dias_consumo}", self.left_info_style))

        elementos.append(Spacer(1, 0.15*cm))

        return elementos
    
    def crear_tabla_encabezados(self, datos_programa=None):
        """
        Crea la tabla de encabezados de productos con writing mode vertical
        """
        if datos_programa:
            empresa = datos_programa.get('empresa', 'CONSORCIO ALIMENTANDO A CALI 2025')
        else:
            empresa = 'CONSORCIO ALIMENTANDO A CALI 2025'
        return self._crear_tabla_con_writing_mode_real(empresa)
    
    def _crear_tabla_con_writing_mode_real(self, empresa):
        """
        Crea tabla con encabezados verticales usando Paragraph con saltos de línea
        """
        from reportlab.platypus import Table, TableStyle, Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        
        # ESTILO PARA WRITING MODE VERTICAL
        estilo_vertical = ParagraphStyle(
            'WritingModeReal',
            parent=self.styles['Normal'],
            fontSize=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            leading=8,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0
        )

        def crear_writing_mode_real(texto):
            """Convierte texto horizontal a vertical usando saltos de línea"""
            palabras = texto.split()
            texto_html = '<br/>'.join(palabras)
            html_final = f'<font size="6"><b>{texto_html}</b></font>'
            return Paragraph(html_final, estilo_vertical)

        # ORDEN CORREGIDO: Cerdo, Pechuga, Muslo/Contramuslo, Res
        data = [
            [
                empresa, '', '', '', '', '',  # 0-5: EMPRESA
                crear_writing_mode_real('CARNE DE CERDO, MAGRA / KG'),               # 6: Cerdo
                crear_writing_mode_real('CARNE DE CERDO, MAGRA / KG'),               # 7: Cerdo
                crear_writing_mode_real('TEMPERATURA PROMEDIO'),                      # 8: Cerdo °C
                crear_writing_mode_real('PECHUGA DE POLLO / KG'),                    # 9: Pechuga
                crear_writing_mode_real('PECHUGA DE POLLO / KG'),                    # 10: Pechuga
                crear_writing_mode_real('TEMPERATURA PROMEDIO'),                      # 11: Pechuga °C
                crear_writing_mode_real('MUSLO/CONTRAMUSLO DE POLLO / UND'),         # 12: Muslo/Contramuslo
                crear_writing_mode_real('MUSLO/CONTRAMUSLO DE POLLO / UND'),         # 13: Muslo/Contramuslo 
                crear_writing_mode_real('TEMPERATURA PROMEDIO'),                      # 14: Muslo/Contramuslo °C
                crear_writing_mode_real('CARNE DE RES, MAGRA / KG'),                 # 15: Res
                crear_writing_mode_real('CARNE DE RES, MAGRA / KG'),                 # 16: Res
                crear_writing_mode_real('TEMPERATURA PROMEDIO'),                      # 17: Res °C
                'FIRMA\nDE\nRECIBO',                                                 # 18
                'HORA\nDE\nENTREGA'                                                  # 19
            ],
            
            # SEGUNDA FILA - Encabezados cortos
            ['', '', '', '', '', '',
             'CANT', 'LOTE', '°C',      # Cerdo
             'CANT', 'LOTE', '°C',      # Pechuga
             'CANT', 'LOTE', '°C',      # Muslo/Contramuslo
             'CANT', 'LOTE', '°C',      # Res
             '', 'HH:MM']
        ]

        tabla = Table(data, colWidths=[
            0.5*cm,  # N° 
            1.3*cm,  # MUNICIPIO 
            1.3*cm,  # DEPARTAMENTO   
            3.8*cm,  # COMEDOR/ESCUELA 
            0.9*cm,  # COBER 
            3.0*cm,  # DIRECCIÓN 
            1.2*cm, 1.4*cm, 1.0*cm,  # Cerdo
            1.2*cm, 1.4*cm, 1.0*cm,  # Pechuga
            1.2*cm, 1.4*cm, 1.0*cm,  # Muslo/Contramuslo
            1.2*cm, 1.4*cm, 1.0*cm,  # Res
            2.2*cm, 1.4*cm           # Firma y hora
        ], 
        rowHeights=[None, None])  # Altura automática para ambas filas

        tabla.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            # Combinaciones de celdas
            ('SPAN', (0, 0), (5, 1)),    # EMPRESA 2x6 (posiciones 0-5)
            ('SPAN', (18, 0), (18, 1)),  # FIRMA vertical (posición 18)
            # ESTILOS ESPECÍFICOS PARA WRITING MODE VERTICAL
            ('VALIGN', (6, 0), (17, 0), 'MIDDLE'),
            ('LEFTPADDING', (6, 0), (17, 0), 3),
            ('RIGHTPADDING', (6, 0), (17, 0), 3),
            ('TOPPADDING', (6, 0), (17, 0), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), -1),  # Espacio inferior mínimo en toda la tabla
        ]))

        return tabla
        
    def crear_seccion_ruta(self, nombre_ruta):
        """
        Crea la sección que identifica la ruta
        """
        ruta_style_pequeno = ParagraphStyle(
            'RutaStylePequeno',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=0,
            spaceBefore=0,
            alignment=0,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        ruta_text = f"CONGELADOS {nombre_ruta}"
        ruta_para = Paragraph(ruta_text, ruta_style_pequeno)
        
        return [ruta_para]
    
    def crear_tabla_comedores(self, datos_comedores, lotes_personalizados=None):
        """
        Crea la tabla principal con los comedores y productos
        """
        def dividir_texto_inteligente(texto, max_chars_por_linea=20, max_lineas=3):
            """Divide texto largo en múltiples líneas"""
            if not texto or len(str(texto)) <= max_chars_por_linea:
                return str(texto)
            
            texto_str = str(texto).strip()
            palabras = texto_str.split()
            lineas = []
            linea_actual = ""
            
            for palabra in palabras:
                if linea_actual and len(linea_actual + " " + palabra) > max_chars_por_linea:
                    lineas.append(linea_actual)
                    linea_actual = palabra
                else:
                    if linea_actual:
                        linea_actual += " " + palabra
                    else:
                        linea_actual = palabra
            
            if linea_actual:
                lineas.append(linea_actual)
            
            if len(lineas) > max_lineas:
                lineas = lineas[:max_lineas]
                if len(lineas[max_lineas-1]) <= max_chars_por_linea - 3:
                    lineas[max_lineas-1] += "..."
                else:
                    lineas[max_lineas-1] = lineas[max_lineas-1][:max_chars_por_linea-3] + "..."
            
            return "\n".join(lineas)

        # ENCABEZADO CON ORDEN CORREGIDO
        encabezado = [
            'N°', 'MUNICIPIO', 'DEPARTA\nMENTO', 'COMEDOR / ESCUELA', 'COBER', 'DIRECCIÓN',
            'KG', 'LOTE', '°C',      # Carne de cerdo
            'KG', 'LOTE', '°C',      # Pechuga de pollo  
            'UND', 'LOTE', '°C',     # Muslo/Contramuslo
            'KG', 'LOTE', '°C',      # Carne de res
            'FIRMA DE RECIBO', 'HORA'
        ]
        
        data = [encabezado]
        total_cobertura = 0
        total_cerdo = 0
        total_pollo = 0
        total_muslo_contramuslo = 0
        total_res = 0
        
        for i, comedor in enumerate(datos_comedores, 1):
            # Obtener datos de los productos
            cerdo_peso = float(comedor.get('CARNE_DE_CERDO', 0) or 0)
            pollo_peso = float(comedor.get('POLLO_PESO', 0) or 0)
            muslo_contramuslo_und = int(comedor.get('MUSLO_CONTRAMUSLO', 0) or 0)
            res_peso = float(comedor.get('CARNE_DE_RES', 0) or 0)
            
            # Acumular totales
            total_cobertura += int(comedor.get('COBER', 0) or 0)
            total_cerdo += cerdo_peso
            total_pollo += pollo_peso
            total_muslo_contramuslo += muslo_contramuslo_und
            total_res += res_peso
            
            # Usar lotes personalizados si están presentes
            lotes = lotes_personalizados or {}
            
            fila = [
                str(i),
                comedor.get('MUNICIPIO', 'CALI'),
                comedor.get('DEPARTAMENTO', 'VALLE'),
                dividir_texto_inteligente(comedor.get('COMEDOR/ESCUELA', ''), max_chars_por_linea=25, max_lineas=3),
                str(comedor.get('COBER', 0)),
                dividir_texto_inteligente(comedor.get('DIRECCIÓN', ''), max_chars_por_linea=20, max_lineas=3),
                # 1. Carne de cerdo (columnas 6-8)
                f"{cerdo_peso:.2f}" if cerdo_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('cerdo') if cerdo_peso > 0 and lotes.get('cerdo') else (str(self.generar_lote_aleatorio()) if cerdo_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if cerdo_peso > 0 else "",
                # 2. Pechuga de pollo (columnas 9-11)
                f"{pollo_peso:.2f}" if pollo_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('pechuga') if pollo_peso > 0 and lotes.get('pechuga') else (str(self.generar_lote_aleatorio()) if pollo_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if pollo_peso > 0 else "",
                # 3. Muslo/Contramuslo (columnas 12-14)
                str(muslo_contramuslo_und) if muslo_contramuslo_und > 0 else "",
                self.dividir_lote_inteligente(lotes.get('muslo') if muslo_contramuslo_und > 0 and lotes.get('muslo') else (str(self.generar_lote_aleatorio()) if muslo_contramuslo_und > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if muslo_contramuslo_und > 0 else "",
                # 4. Carne de res (columnas 15-17)
                f"{res_peso:.2f}" if res_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('res') if res_peso > 0 and lotes.get('res') else (str(self.generar_lote_aleatorio()) if res_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if res_peso > 0 else "",
                # 5. Firma y hora (columnas 18-19)
                '',  # FIRMA DE RECIBO
                ''   # HORA DE ENTREGA
            ]
            
            data.append(fila)

        # AGREGAR FILA DE TOTALES
        fila_total = [
            'TOTAL COBERTURA RUTA', '', '', '',     # Posiciones 0-3 combinadas
            f"{total_cobertura:,}", '',             # Posiciones 4-5
            f"{total_cerdo:.2f}" if total_cerdo > 0 else "", '', '',           # Total cerdo (6-8)
            f"{total_pollo:.2f}" if total_pollo > 0 else "", '', '',           # Total pechuga (9-11)
            f"{total_muslo_contramuslo}" if total_muslo_contramuslo > 0 else "", '', '',   # Total muslo/contramuslo (12-14)
            f"{total_res:.2f}" if total_res > 0 else "", '', '',             # Total res (15-17)
            '', ''                                  # Firma y hora (18-19)
        ]
        data.append(fila_total)

        # CREAR LA TABLA CON ANCHOS ESPECÍFICOS
        tabla = Table(data, colWidths=[
            0.5*cm,  # N°
            1.3*cm,  # MUNICIPIO
            1.3*cm,  # DEPARTAMENTO
            3.8*cm,  # COMEDOR/ESCUELA
            0.9*cm,  # COBER
            3.0*cm,  # DIRECCIÓN
            1.2*cm, 1.4*cm, 1.0*cm,  # Cerdo: KG, LOTE, °C
            1.2*cm, 1.4*cm, 1.0*cm,  # Pechuga: KG, LOTE, °C
            1.2*cm, 1.4*cm, 1.0*cm,  # Muslo/Contramuslo: UND, LOTE, °C
            1.2*cm, 1.4*cm, 1.0*cm,  # Res: KG, LOTE, °C
            2.2*cm, 1.4*cm           # FIRMA, HORA
        ], rowHeights=[None for _ in range(len(data))])  # Altura automática para todas las filas

        # APLICAR ESTILOS
        style = [
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), -1),  # Espacio inferior mínimo en toda la tabla
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            # Alineación especial para algunas columnas
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),  # Números
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),   # Cobertura
            ('ALIGN', (6, 1), (6, -2), 'RIGHT'),   # KG Cerdo
            ('ALIGN', (9, 1), (9, -2), 'RIGHT'),   # KG Pechuga
            ('ALIGN', (12, 1), (12, -2), 'RIGHT'), # UND Muslo/Contramuslo
            ('ALIGN', (15, 1), (15, -2), 'RIGHT'), # KG Res
            # AJUSTES ESPECIALES PARA COMEDOR/ESCUELA (columna 3)
            ('FONTSIZE', (3, 1), (3, -2), 6),
            ('ALIGN', (3, 1), (3, -2), 'LEFT'),
            ('VALIGN', (3, 1), (3, -2), 'TOP'),
            ('LEFTPADDING', (3, 1), (3, -2), 2),
            ('RIGHTPADDING', (3, 1), (3, -2), 2),
            # AJUSTES ESPECIALES PARA DIRECCIÓN (columna 5)
            ('FONTSIZE', (5, 1), (5, -2), 6),
            ('ALIGN', (5, 1), (5, -2), 'LEFT'),
            ('VALIGN', (5, 1), (5, -2), 'TOP'),
            ('LEFTPADDING', (5, 1), (5, -2), 2),
            ('RIGHTPADDING', (5, 1), (5, -2), 2),
            # ESTILOS PARA COLUMNAS DE LOTES
            ('FONTSIZE', (7, 1), (7, -2), 6),    # Lote Cerdo (columna 7)
            ('FONTSIZE', (10, 1), (10, -2), 6),  # Lote Pechuga (columna 10)
            ('FONTSIZE', (13, 1), (13, -2), 6),  # Lote Muslo (columna 13)
            ('FONTSIZE', (16, 1), (16, -2), 6),  # Lote Res (columna 16)
            ('VALIGN', (7, 1), (7, -2), 'TOP'),   # Alineación vertical superior
            ('VALIGN', (10, 1), (10, -2), 'TOP'),
            ('VALIGN', (13, 1), (13, -2), 'TOP'),
            ('VALIGN', (16, 1), (16, -2), 'TOP'),
            ('LEFTPADDING', (7, 1), (7, -2), 2),  # Padding reducido
            ('RIGHTPADDING', (7, 1), (7, -2), 2),
            ('LEFTPADDING', (10, 1), (10, -2), 2),
            ('RIGHTPADDING', (10, 1), (10, -2), 2),
            ('LEFTPADDING', (13, 1), (13, -2), 2),
            ('RIGHTPADDING', (13, 1), (13, -2), 2),
            ('LEFTPADDING', (16, 1), (16, -2), 2),
            ('RIGHTPADDING', (16, 1), (16, -2), 2)
        ]
        
        # Estilo de la fila de totales solo si es la última página
        if len(data) > 1 and data[-1][0] == 'TOTAL COBERTURA RUTA':
            style += [
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('SPAN', (0, -1), (3, -1)),
            ]
            
        tabla.setStyle(TableStyle(style))
        return tabla
    
    def crear_seccion_adicional(self):
        """
        Crea la sección adicional con cajas/pacas y unidades
        """
        elementos = []
        
        elementos.append(Spacer(1, 0.15*cm))
        
        cajas_pacas = Paragraph("CAJAS / PACAS: ________________", self.left_info_style)
        elementos.append(cajas_pacas)
        
        unidades = Paragraph("UNIDADES: ________________", self.left_info_style)
        elementos.append(unidades)
        
        elementos.append(Spacer(1, 0.25*cm))
        
        return elementos
        
    def crear_pie_pagina(self, elaborado_por="____________________"):
        """
        Crea el pie de página con firmas y notas finales
        """
        elementos = []
        
        transportador = Paragraph("TRANSPORTADOR: _________________________________", self.left_info_style)
        elementos.append(transportador)
        
        hora_placa = Paragraph("Hora Salida: _______________     Placa: _______________", self.left_info_style)
        elementos.append(hora_placa)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # Crear tabla con firmas dinámicas
        tabla_firmas = self._crear_tabla_firmas_con_imagenes(elaborado_por)
        elementos.append(tabla_firmas)
        
        # Nota final
        elementos.append(Spacer(1, 0.2*cm))
        nota = "NOTA: LOS FALTANTES Y NOVEDADES SERAN ASUMIDOS POR EL RESPONSABLE EN EL DESPACHO DE BODEGA Y/O EL RESPONSABLE DE LA ENTREGA EN EL CAMION."
        nota_para = Paragraph(nota, self.header_style)
        elementos.append(nota_para)
        
        return elementos

    def _crear_tabla_firmas_con_imagenes(self, elaborado_por):
        """
        Crea tabla de firmas con imágenes dinámicas o texto placeholder
        """
        def cargar_imagen_firma(nombre_persona, ancho=2*cm, alto=0.8*cm):
            """Carga imagen de firma desde la carpeta imagenes/"""
            try:
                # Crear carpeta si no existe
                if not os.path.exists("imagenes"):
                    os.makedirs("imagenes")
                
                # Buscar imagen con diferentes extensiones
                extensiones = ['.png', '.jpg', '.jpeg', '.gif']
                for ext in extensiones:
                    ruta_imagen = os.path.join("imagenes", f"{nombre_persona}{ext}")
                    if os.path.exists(ruta_imagen):
                        imagen = Image(ruta_imagen, width=ancho, height=alto)
                        return imagen
                
                # Si no encuentra imagen, devolver línea de firma
                return Paragraph("_" * 25, self.styles['Normal'])
                
            except Exception as e:
                print(f"Error cargando imagen de firma para {nombre_persona}: {e}")
                return Paragraph("_" * 25, self.styles['Normal'])

        # Preparar datos para la tabla de firmas
        elaborado_texto = f'ELABORADO POR: {elaborado_por}'
        aprobado_texto = f'APROBADO POR: SANDRA HENAO TORO'

        firma_elaborado = cargar_imagen_firma(elaborado_por)
        firma_aprobado = cargar_imagen_firma("SANDRA HENAO TORO")

        # Combinar nombre y firma en la misma celda
        celda_elaborado = [Paragraph(elaborado_texto, self.styles['Normal']), Spacer(1, 0.05*cm), firma_elaborado]
        celda_aprobado = [Paragraph(aprobado_texto, self.styles['Normal']), Spacer(1, 0.05*cm), firma_aprobado]

        data_firmas = [
            [celda_elaborado, celda_aprobado],
            ['SUPERVISOR DE CALIDAD', 'LIDER DE ASEGURAMIENTO - CEL: 318 3645374']
        ]

        tabla_firmas = Table(data_firmas, colWidths=[10*cm, 10*cm], rowHeights=[None, None])

        tabla_firmas.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, 1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
        ]))

        return tabla_firmas

    def generar_pdf_con_paginacion(self, datos_programa, datos_comedores, lotes_personalizados=None, elaborado_por="____________________", nombre_archivo="guia_transporte.pdf"):
        """
        Genera el PDF con encabezado y pie constantes en cada página, y tabla principal paginada (máximo 4 filas por página).
        """
        from reportlab.platypus import SimpleDocTemplate, PageTemplate, Frame, Spacer
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm

        # Configuración de documento y frames
        margen_izq = 1.5 * cm
        margen_der = 1.5 * cm
        margen_sup = 1.5 * cm
        margen_inf = 1.5 * cm
        ancho_pagina, alto_pagina = letter
        ancho_frame = ancho_pagina - margen_izq - margen_der
        alto_frame = alto_pagina - margen_sup - margen_inf

        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter,
                               leftMargin=margen_izq, rightMargin=margen_der,
                               topMargin=margen_sup, bottomMargin=margen_inf)

        # Funciones para encabezado y pie
        def dibujar_encabezado(canvas, doc):
            canvas.saveState()
            # Encabezado: dibujar en la parte superior
            encabezado = self.crear_encabezado(datos_programa)
            tabla_encabezado = self.crear_tabla_encabezados(datos_programa)
            w, h = tabla_encabezado.wrap(doc.width, doc.topMargin)
            y = alto_pagina - margen_sup
            for elemento in encabezado:
                elemento.wrapOn(canvas, doc.width, doc.topMargin)
                elemento.drawOn(canvas, margen_izq, y)
                y -= elemento.getSpaceAfter() + elemento.getSpaceBefore() + (elemento.height if hasattr(elemento, 'height') else 10)
            tabla_encabezado.wrapOn(canvas, doc.width, doc.topMargin)
            tabla_encabezado.drawOn(canvas, margen_izq, y - h)
            canvas.restoreState()

        def dibujar_pie(canvas, doc):
            canvas.saveState()
            pie = self.crear_pie_pagina(elaborado_por)
            y = margen_inf
            for elemento in pie:
                elemento.wrapOn(canvas, doc.width, doc.bottomMargin)
                elemento.drawOn(canvas, margen_izq, y)
                y += elemento.getSpaceAfter() + elemento.getSpaceBefore() + (elemento.height if hasattr(elemento, 'height') else 10)
            canvas.restoreState()

        # Crear PageTemplate con encabezado y pie
        frame = Frame(margen_izq, margen_inf, ancho_frame, alto_frame - 6*cm, id='normal')
        plantilla = PageTemplate(id='GuiaTransporte', frames=[frame], onPage=dibujar_encabezado, onPageEnd=dibujar_pie)
        doc.addPageTemplates([plantilla])

        # Dividir datos en bloques de 4 filas (sin contar encabezado ni totales)
        encabezado = [
            'N°', 'MUNICIPIO', 'DEPARTA\nMENTO', 'COMEDOR / ESCUELA', 'COBER', 'DIRECCIÓN',
            'KG', 'LOTE', '°C',      # Carne de cerdo
            'KG', 'LOTE', '°C',      # Pechuga de pollo  
            'UND', 'LOTE', '°C',     # Muslo/Contramuslo
            'KG', 'LOTE', '°C',      # Carne de res
            'FIRMA DE RECIBO', 'HORA'
        ]
        
        filas = []
        for i, comedor in enumerate(datos_comedores, 1):
            cerdo_peso = float(comedor.get('CARNE_DE_CERDO', 0) or 0)
            pollo_peso = float(comedor.get('POLLO_PESO', 0) or 0)
            muslo_contramuslo_und = int(comedor.get('MUSLO_CONTRAMUSLO', 0) or 0)
            res_peso = float(comedor.get('CARNE_DE_RES', 0) or 0)
            lotes = lotes_personalizados or {}
            
            fila = [
                str(i),
                comedor.get('MUNICIPIO', 'CALI'),
                comedor.get('DEPARTAMENTO', 'VALLE'),
                self.dividir_lote_inteligente(comedor.get('COMEDOR/ESCUELA', ''), max_chars_por_linea=25),
                str(comedor.get('COBER', 0)),
                self.dividir_lote_inteligente(comedor.get('DIRECCIÓN', ''), max_chars_por_linea=20),
                f"{cerdo_peso:.2f}" if cerdo_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('cerdo') if cerdo_peso > 0 and lotes.get('cerdo') else (str(self.generar_lote_aleatorio()) if cerdo_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if cerdo_peso > 0 else "",
                f"{pollo_peso:.2f}" if pollo_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('pechuga') if pollo_peso > 0 and lotes.get('pechuga') else (str(self.generar_lote_aleatorio()) if pollo_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if pollo_peso > 0 else "",
                str(muslo_contramuslo_und) if muslo_contramuslo_und > 0 else "",
                self.dividir_lote_inteligente(lotes.get('muslo') if muslo_contramuslo_und > 0 and lotes.get('muslo') else (str(self.generar_lote_aleatorio()) if muslo_contramuslo_und > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if muslo_contramuslo_und > 0 else "",
                f"{res_peso:.2f}" if res_peso > 0 else "",
                self.dividir_lote_inteligente(lotes.get('res') if res_peso > 0 and lotes.get('res') else (str(self.generar_lote_aleatorio()) if res_peso > 0 else "")),
                f"{self.generar_temperatura_aleatoria()}°C" if res_peso > 0 else "",
                '',  # FIRMA DE RECIBO
                ''   # HORA DE ENTREGA
            ]
            filas.append(fila)

        # Paginación: bloques de 4 filas
        bloques = [filas[i:i+4] for i in range(0, len(filas), 4)]

        # Calcular totales
        total_cobertura = sum(int(f[4]) if f[4] else 0 for f in filas)
        total_cerdo = sum(float(f[6]) if f[6] else 0 for f in filas)
        total_pollo = sum(float(f[9]) if f[9] else 0 for f in filas)
        total_muslo_contramuslo = sum(int(f[12]) if f[12] else 0 for f in filas)
        total_res = sum(float(f[15]) if f[15] else 0 for f in filas)

        fila_total = [
            'TOTAL COBERTURA RUTA', '', '', '',
            f"{total_cobertura:,}", '',
            f"{total_cerdo:.2f}" if total_cerdo > 0 else "", '', '',
            f"{total_pollo:.2f}" if total_pollo > 0 else "", '', '',
            f"{total_muslo_contramuslo}" if total_muslo_contramuslo > 0 else "", '', '',
            f"{total_res:.2f}" if total_res > 0 else "", '', '',
            '', ''
        ]

        # Crear story (contenido del PDF)
        story = []
        for idx, bloque in enumerate(bloques):
            data_tabla = [encabezado] + bloque
            # Solo en la última página agregar la fila de totales
            if idx == len(bloques) - 1:
                data_tabla.append(fila_total)
                
            tabla = Table(data_tabla, colWidths=[
                0.5*cm, 1.3*cm, 1.3*cm, 3.8*cm, 0.9*cm, 3.0*cm,
                1.2*cm, 1.4*cm, 1.0*cm, 1.2*cm, 1.4*cm, 1.0*cm,
                1.2*cm, 1.4*cm, 1.0*cm, 1.2*cm, 1.4*cm, 1.0*cm,
                2.2*cm, 1.4*cm
            ], rowHeights=[None for _ in range(len(data_tabla))])
            
            tabla.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue) if idx == len(bloques) - 1 else (),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold') if idx == len(bloques) - 1 else (),
                ('SPAN', (0, -1), (3, -1)) if idx == len(bloques) - 1 else (),
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),
                ('ALIGN', (4, 1), (4, -2), 'RIGHT'),
                ('ALIGN', (6, 1), (6, -2), 'RIGHT'),
                ('ALIGN', (9, 1), (9, -2), 'RIGHT'),
                ('ALIGN', (12, 1), (12, -2), 'RIGHT'),
                ('ALIGN', (15, 1), (15, -2), 'RIGHT'),
                ('FONTSIZE', (3, 1), (3, -2), 6),
                ('ALIGN', (3, 1), (3, -2), 'LEFT'),
                ('VALIGN', (3, 1), (3, -2), 'TOP'),
                ('LEFTPADDING', (3, 1), (3, -2), 2),
                ('RIGHTPADDING', (3, 1), (3, -2), 2),
                ('FONTSIZE', (5, 1), (5, -2), 6),
                ('ALIGN', (5, 1), (5, -2), 'LEFT'),
                ('VALIGN', (5, 1), (5, -2), 'TOP'),
                ('LEFTPADDING', (5, 1), (5, -2), 2),
                ('RIGHTPADDING', (5, 1), (5, -2), 2),
                ('FONTSIZE', (7, 1), (7, -2), 6),
                ('FONTSIZE', (10, 1), (10, -2), 6),
                ('FONTSIZE', (13, 1), (13, -2), 6),
                ('FONTSIZE', (16, 1), (16, -2), 6),
                ('VALIGN', (7, 1), (7, -2), 'TOP'),
                ('VALIGN', (10, 1), (10, -2), 'TOP'),
                ('VALIGN', (13, 1), (13, -2), 'TOP'),
                ('VALIGN', (16, 1), (16, -2), 'TOP'),
                ('LEFTPADDING', (7, 1), (7, -2), 2),
                ('RIGHTPADDING', (7, 1), (7, -2), 2),
                ('LEFTPADDING', (10, 1), (10, -2), 2),
                ('RIGHTPADDING', (10, 1), (10, -2), 2),
                ('LEFTPADDING', (13, 1), (13, -2), 2),
                ('RIGHTPADDING', (13, 1), (13, -2), 2),
                ('LEFTPADDING', (16, 1), (16, -2), 2),
                ('RIGHTPADDING', (16, 1), (16, -2), 2),
            ]))
            
            story.append(tabla)
            if idx < len(bloques) - 1:
                story.append(Spacer(1, 0.5*cm))

        doc.build(story)