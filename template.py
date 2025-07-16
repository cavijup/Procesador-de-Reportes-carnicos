"""
template.py - Plantilla para generar Guías de Transporte
Basado en el formato del archivo "Reporte_lista_peso para formato.xlsx"
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from datetime import datetime

class PlantillaGuiaTransporte:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Configurar estilos personalizados"""
        
        # Estilo para encabezado principal
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=6,
            alignment=1,  # Centrado
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para información del programa
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            alignment=0,  # Izquierda
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Estilo para secciones importantes
        self.section_style = ParagraphStyle(
            'SectionStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=1,  # Centrado
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
    def crear_encabezado(self, datos_programa, numero_guia=None):
        """Crear la sección de encabezado del documento"""
        elementos = []
        
        # Número de guía
        if not numero_guia:
            numero_guia = "001-001"
        
        titulo_guia = Paragraph(f"GUIA DE TRANSPORTE No. {numero_guia}", self.title_style)
        elementos.append(titulo_guia)
        elementos.append(Spacer(1, 0.2*cm))
        
        # Información del programa
        programa_text = f"PROGRAMA: {datos_programa.get('programa', 'COMEDORES COMUNITARIOS CALI 2025')}"
        elementos.append(Paragraph(programa_text, self.header_style))
        
        # Dirección del consorcio
        direccion = "CONSORCIO ALIMENTANDO A CALI 2025 / DIRECCION: CL 15 No. 26 - 101 BG 34/ YUMBO- VALLE DEL CAUCA"
        elementos.append(Paragraph(direccion, self.header_style))
        
        # Código de inscripción
        codigo = "CODIGO DE INSCRIPCION No. 76892-8050291700"
        elementos.append(Paragraph(codigo, self.header_style))
        
        elementos.append(Spacer(1, 0.3*cm))
        
        # Lista de peso
        lista_peso = "LISTA DE PESO MATERIA PRIMA - CARNES LACTEOS Y QUESOS - TODOS LOS PRODUCTOS - TODOS LOS DIAS"
        elementos.append(Paragraph(lista_peso, self.section_style))
        
        # Información de despacho
        fecha_elaboracion = datetime.now().strftime('%Y-%m-%d')
        despacho_info = f"DESPACHO: CP AM CALI - FECHA ELABORACIÓN: {fecha_elaboracion}"
        elementos.append(Paragraph(despacho_info, self.header_style))
        
        # Fecha de despacho
        fecha_despacho = datos_programa.get('fecha_entrega', datetime.now().strftime('%d/%m/%Y'))
        elementos.append(Paragraph(f"Fecha despacho: {fecha_despacho}", self.header_style))
        
        # Dictamen
        elementos.append(Paragraph("DICTAMEN: APROBADO / APROBADO CONDICIONADO", self.header_style))
        
        # Solicitud de remesa (puede ser configurable)
        elementos.append(Paragraph("Solicitud Remesa: MENU 6 - MENU 7 - MENU 8", self.header_style))
        
        # Días de consumo
        dias_consumo = datos_programa.get('dias_consumo', f"{fecha_despacho} - {fecha_despacho} - {fecha_despacho}")
        elementos.append(Paragraph(f"Dias de consumo: {dias_consumo}", self.header_style))
        
        elementos.append(Spacer(1, 0.4*cm))
        
        return elementos
    
    def crear_tabla_encabezados(self):
        """Crear la tabla de encabezados de productos"""
        
        # Encabezados principales
        data = [
            ['CONSORCIO ALIMENTANDO A CALI 2025', '', '', '', '', '', 
             'CARNE DE RES, MAGRA / KG', 'CARNE DE RES, MAGRA / KG', 'TEMPERATURA PROMEDIO',
             'CARNE DE CERDO, MAGRA / KG', 'CARNE DE CERDO, MAGRA / KG', 'TEMPERATURA PROMEDIO',
             'PECHUGA DE POLLO / KG', 'PECHUGA DE POLLO / KG', 'TEMPERATURA PROMEDIO',
             'FIRMA DE RECIBO', 'HORA DE ENTREGA'],
            
            ['NUMERO DE PESADAS', '', '', '', '', '',
             'CANTIDAD', 'LOTE', '°C', 'CANTIDAD', 'LOTE', '°C',
             'CANTIDAD', 'LOTE', '°C', '', 'HH:MM']
        ]
        
        tabla = Table(data, colWidths=[
            1.2*cm, 1.5*cm, 1.5*cm, 4*cm, 1*cm, 3*cm,  # Datos básicos
            1.2*cm, 2*cm, 1*cm,  # Carne de res
            1.2*cm, 2*cm, 1*cm,  # Carne de cerdo  
            1.2*cm, 2*cm, 1*cm,  # Pollo
            2*cm, 1.5*cm  # Firma y hora
        ])
        
        tabla.setStyle(TableStyle([
            # Estilo general
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            
            # Fondo de encabezados
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey),
            
            # Texto en negrita para encabezados
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ]))
        
        return tabla
    
    def crear_seccion_ruta(self, nombre_ruta):
        """Crear la sección de identificación de ruta"""
        ruta_text = f"CONGELADOS {nombre_ruta}"
        ruta_para = Paragraph(ruta_text, self.section_style)
        return [ruta_para, Spacer(1, 0.2*cm)]
    
    def crear_tabla_comedores(self, datos_comedores):
        """Crear la tabla principal con los comedores"""
        
        # Encabezado de la tabla
        encabezado = [
            'N°', 'MUNICIPIO', 'DEPARTAMENTO', 'COMEDOR / ESCUELA', 'COBER', 'DIRECCIÓN',
            'KG', 'LOTE', 'TEMP (°C)',  # Carne de res
            'KG', 'LOTE', 'TEMP (°C)',  # Carne de cerdo
            'KG', 'LOTE', 'TEMP (°C)',  # Pollo
            'FIRMA DE RECIBO', 'HORA DE ENTREGA'
        ]
        
        # Preparar datos
        data = [encabezado]
        
        total_cobertura = 0
        total_res = 0
        total_cerdo = 0
        total_pollo = 0
        
        for i, comedor in enumerate(datos_comedores, 1):
            fila = [
                str(i),
                comedor.get('MUNICIPIO', 'CALI'),
                comedor.get('DEPARTAMENTO', 'VALLE'),
                comedor.get('COMEDOR/ESCUELA', ''),
                str(comedor.get('COBER', 0)),
                comedor.get('DIRECCIÓN', ''),
                
                # Carne de res
                f"{float(comedor.get('CARNE_DE_RES', 0)):.2f}" if comedor.get('CARNE_DE_RES', 0) else "",
                '',  # LOTE (a llenar manualmente)
                '',  # TEMP (a llenar manualmente)
                
                # Carne de cerdo
                f"{float(comedor.get('CARNE_DE_CERDO', 0)):.2f}" if comedor.get('CARNE_DE_CERDO', 0) else "",
                '',  # LOTE (a llenar manualmente)
                '',  # TEMP (a llenar manualmente)
                
                # Pollo
                f"{float(comedor.get('POLLO_PESO', 0)):.2f}" if comedor.get('POLLO_PESO', 0) else "",
                '',  # LOTE (a llenar manualmente)
                '',  # TEMP (a llenar manualmente)
                
                '',  # FIRMA DE RECIBO (a llenar manualmente)
                ''   # HORA DE ENTREGA (a llenar manualmente)
            ]
            
            data.append(fila)
            
            # Sumar totales
            total_cobertura += int(comedor.get('COBER', 0))
            total_res += float(comedor.get('CARNE_DE_RES', 0) or 0)
            total_cerdo += float(comedor.get('CARNE_DE_CERDO', 0) or 0)
            total_pollo += float(comedor.get('POLLO_PESO', 0) or 0)
        
        # Fila de totales
        fila_total = [
            'TOTAL COBERTURA RUTA', '', '', '', 
            f"{total_cobertura:,}", '',
            f"{total_res:.2f}", '', '',  # Total res
            f"{total_cerdo:.2f}", '', '',  # Total cerdo
            f"{total_pollo:.2f}", '', '',  # Total pollo
            '', ''
        ]
        data.append(fila_total)
        
        # Crear tabla
        tabla = Table(data, colWidths=[
            0.8*cm, 1.5*cm, 1.5*cm, 4.5*cm, 1.2*cm, 3.5*cm,  # Datos básicos
            1*cm, 1.5*cm, 1*cm,  # Carne de res
            1*cm, 1.5*cm, 1*cm,  # Carne de cerdo  
            1*cm, 1.5*cm, 1*cm,  # Pollo
            2*cm, 1.5*cm  # Firma y hora
        ])
        
        # Aplicar estilos
        tabla.setStyle(TableStyle([
            # Estilo general
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Fila de totales
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Alineación especial para algunas columnas
            ('ALIGN', (0, 1), (0, -2), 'CENTER'),  # Números
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),   # Cobertura
            ('ALIGN', (6, 1), (6, -2), 'RIGHT'),   # KG Res
            ('ALIGN', (9, 1), (9, -2), 'RIGHT'),   # KG Cerdo
            ('ALIGN', (12, 1), (12, -2), 'RIGHT'), # KG Pollo
        ]))
        
        return tabla
    
    def crear_seccion_adicional(self):
        """Crear sección adicional con cajas, unidades, etc."""
        elementos = []
        
        elementos.append(Spacer(1, 0.3*cm))
        
        # Tabla para cajas/pacas y unidades
        data_adicional = [
            ['CAJAS / PACAS', '', '', '', '', '', '0'],
            ['UNIDADES', '', '', '', '', '', '0']
        ]
        
        tabla_adicional = Table(data_adicional, colWidths=[3*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 2*cm])
        tabla_adicional.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        elementos.append(tabla_adicional)
        elementos.append(Spacer(1, 0.5*cm))
        
        return elementos
    
    def crear_pie_pagina(self):
        """Crear la sección de pie de página con firmas"""
        elementos = []
        
        # Información del transportador
        transportador = Paragraph("TRANSPORTADOR: _________________________________", self.header_style)
        elementos.append(transportador)
        
        hora_placa = Paragraph("Hora Salida: _______________     Placa: _______________", self.header_style)
        elementos.append(hora_placa)
        
        elementos.append(Spacer(1, 0.5*cm))
        
        # Tabla de firmas
        data_firmas = [
            ['ELABORADO POR:', '', '', '', '', '', '', 'APROBADO POR: SANDRA HENAO TORO'],
            ['SUPERVISOR DE CALIDAD', '', '', '', '', '', '', 'LIDER DE ASEGURAMIENTO - CEL: 318 3645374']
        ]
        
        tabla_firmas = Table(data_firmas, colWidths=[4*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 1*cm, 5*cm])
        tabla_firmas.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        elementos.append(tabla_firmas)
        elementos.append(Spacer(1, 0.3*cm))
        
        # Nota final
        nota = "NOTA: LOS FALTANTES Y NOVEDADES SERAN ASUMIDOS POR EL RESPONSABLE EN EL DESPACHO DE BODEGA Y/O EL RESPONSABLE DE LA ENTREGA EN EL CAMION."
        nota_para = Paragraph(nota, self.header_style)
        elementos.append(nota_para)
        
        return elementos