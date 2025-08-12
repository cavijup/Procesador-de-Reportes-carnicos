import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from logger_config import logger


class GoogleSheetsHandler:
    def __init__(self, secrets):
        """
        Autentica usando las credenciales del service account desde st.secrets.
        """
        logger.info("Inicializando GoogleSheetsHandler...")
        
        try:
            # Hacemos una copia de las credenciales para poder modificarlas
            creds_dict = dict(secrets['credentials'])
            
            # --- INICIO DE LA CORRECCIÓN ROBUSTA DE LA CLAVE PRIVADA ---
            # 1. Reemplaza los caracteres de escape literales '\\n' por saltos de línea reales '\n'.
            private_key = creds_dict['private_key'].replace('\\n', '\n')
            
            # 2. Divide la clave en líneas, elimina espacios en blanco de cada una y las vuelve a unir.
            #    Esto soluciona errores de "Incorrect padding" causados por espacios extra o formato incorrecto.
            cleaned_lines = [line.strip() for line in private_key.strip().split('\n')]
            creds_dict['private_key'] = '\n'.join(cleaned_lines)
            # --- FIN DE LA CORRECCIÓN ROBUSTA ---

            logger.info("Clave privada limpiada. Intentando autenticar con Google Sheets...")
            
            self.spreadsheet_id = secrets['spreadsheet_id']
            self.gc = gspread.service_account_from_dict(creds_dict)
            self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            logger.info("Autenticación con Google Sheets y apertura del libro de cálculo exitosa.")

        except Exception as e:
            # Captura cualquier error durante la inicialización y lo registra con detalles
            logger.error(f"Fallo en la inicialización de GoogleSheetsHandler: {e}", exc_info=True)
            # Vuelve a lanzar la excepción para que la app principal la maneje
            raise

    def _prepare_dataframe_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara el DataFrame para que coincida con la estructura de la hoja de Google.
        - Añade la columna FECHA.
        - Asegura que todas las columnas requeridas existan.
        - Reordena las columnas para que coincidan con la hoja de destino.
        """
        # 1. Crear una copia para evitar modificar el original
        df_upload = df.copy()

        # 2. Añadir la columna FECHA con la fecha actual del procesamiento
        df_upload['FECHA'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 3. Definir las columnas y el orden exacto de la hoja de Google
        target_columns = [
            'FECHA', 'PROGRAMA', 'EMPRESA', 'MODALIDAD', 'SOLICITUD_REMESA',
            'DIAS_CONSUMO', 'FECHA_ENTREGA', 'DIA', 'RUTA', 'N°', 'MUNICIPIO',
            'COMEDOR/ESCUELA', 'COBER', 'DIRECCIÓN', 'CARNE_DE_CERDO',
            'CARNE_DE_RES', 'MUSLO_CONTRAMUSLO', 'POLLO_PESO',
            # --- NUEVAS COLUMNAS AÑADIDAS AL FINAL ---
            'LOTECARNE_DE_CERDO', 'LOTECARNE_DE_RES', 
            'LOTEMUSLO_CONTRAMUSLO', 'LOTEPOLLO_PESO'
        ]

        # 4. Asegurar que todas las columnas de destino existan en el DataFrame
        for col in target_columns:
            if col not in df_upload.columns:
                df_upload[col] = None  # O un valor por defecto apropiado

        # 5. Reordenar y seleccionar solo las columnas de destino
        df_final = df_upload[target_columns]

        # 6. Convertir todos los datos a string para evitar problemas de formato en Sheets
        return df_final.astype(str)

    def append_to_sheet(self, df: pd.DataFrame, worksheet_name: str):
        """
        Añade los datos de un DataFrame al final de una hoja de cálculo específica.
        """
        logger.info(f"Intentando añadir {len(df)} filas a la hoja '{worksheet_name}'...")
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            df_to_append = self._prepare_dataframe_for_upload(df)
            values_to_append = df_to_append.values.tolist()
            worksheet.append_rows(values_to_append, value_input_option='USER_ENTERED')
            
            success_message = f"{len(values_to_append)} filas añadidas exitosamente a '{worksheet_name}'."
            logger.info(success_message)
            return True, success_message
            
        except gspread.exceptions.WorksheetNotFound:
            error_message = f"Error: La hoja de cálculo '{worksheet_name}' no fue encontrada."
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Ocurrió un error inesperado al escribir en la hoja: {e}"
            logger.error(error_message, exc_info=True)
            return False, error_message