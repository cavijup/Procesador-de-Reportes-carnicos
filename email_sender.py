import streamlit as st
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def enviar_correo_con_adjunto(destinatarios, asunto, cuerpo_mensaje, archivo_adjunto_buffer, nombre_archivo_adjunto):
    """
    Envía un correo electrónico usando Gmail con un archivo adjunto desde un buffer en memoria.
    (Función original mantenida para compatibilidad)
    """
    return enviar_correo_con_adjuntos(
        destinatarios=destinatarios,
        asunto=asunto, 
        cuerpo_mensaje=cuerpo_mensaje,
        adjuntos=[{
            'buffer': archivo_adjunto_buffer,
            'nombre': nombre_archivo_adjunto
        }]
    )

def enviar_correo_con_adjuntos(destinatarios, asunto, cuerpo_mensaje, adjuntos):
    """
    ⭐ NUEVA FUNCIÓN: Envía correo con múltiples adjuntos
    
    Args:
        destinatarios (list): Lista de correos electrónicos
        asunto (str): Asunto del correo
        cuerpo_mensaje (str): Cuerpo en formato HTML
        adjuntos (list): Lista de diccionarios con 'buffer' y 'nombre'
                        Ejemplo: [
                            {'buffer': excel_buffer, 'nombre': 'reporte.xlsx'},
                            {'buffer': zip_buffer, 'nombre': 'pdfs.zip'}
                        ]
    
    Returns:
        bool: True si exitoso, False si hay error
    """
    try:
        # Cargar credenciales
        remitente = st.secrets["gmail"]["email"]
        password = st.secrets["gmail"]["app_password"]

        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje["From"] = remitente
        mensaje["To"] = ", ".join(destinatarios)
        mensaje["Subject"] = asunto

        # Adjuntar cuerpo del mensaje
        mensaje.attach(MIMEText(cuerpo_mensaje, "html"))

        # ⭐ ADJUNTAR MÚLTIPLES ARCHIVOS
        for adjunto in adjuntos:
            # Crear objeto MIMEBase para cada adjunto
            part = MIMEBase("application", "octet-stream")
            
            # Leer el contenido del buffer
            buffer = adjunto['buffer']
            nombre = adjunto['nombre']
            
            # Si el buffer tiene el método getvalue(), usarlo; sino, leerlo directamente
            if hasattr(buffer, 'getvalue'):
                contenido = buffer.getvalue()
            else:
                # Si es un BytesIO, asegurar que esté en posición 0
                buffer.seek(0)
                contenido = buffer.read()
            
            part.set_payload(contenido)
            
            # Codificar en base64
            encoders.encode_base64(part)
            
            # Añadir cabecera
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {nombre}",
            )
            
            # Adjuntar al mensaje
            mensaje.attach(part)

        # Enviar correo
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(remitente, password)
            server.sendmail(remitente, destinatarios, mensaje.as_string())
            
        return True

    except Exception as e:
        st.error(f"❌ Error al enviar el correo: {e}")
        return False

def enviar_correo_reporte_completo(destinatarios, asunto, cuerpo_mensaje, excel_buffer, zip_buffer, nombre_excel, nombre_zip):
    """
    🎯 FUNCIÓN ESPECÍFICA: Envía correo con Excel + ZIP de PDFs
    
    Args:
        destinatarios (list): Lista de emails
        asunto (str): Asunto del correo
        cuerpo_mensaje (str): Mensaje HTML
        excel_buffer (BytesIO): Buffer con archivo Excel
        zip_buffer (BytesIO): Buffer con archivo ZIP
        nombre_excel (str): Nombre del archivo Excel
        nombre_zip (str): Nombre del archivo ZIP
        
    Returns:
        bool: True si exitoso
    """
    adjuntos = [
        {'buffer': excel_buffer, 'nombre': nombre_excel},
        {'buffer': zip_buffer, 'nombre': nombre_zip}
    ]
    
    return enviar_correo_con_adjuntos(
        destinatarios=destinatarios,
        asunto=asunto,
        cuerpo_mensaje=cuerpo_mensaje,
        adjuntos=adjuntos
    )