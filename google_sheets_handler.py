import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from datetime import datetime

class GoogleSheetsHandler:
    """
    Clase para manejar la autenticación y la carga de datos a Google Sheets.
    """
    def __init__(self, secrets):
        """
        Autentica usando las credenciales del service account desde st.secrets.
        """
        self.creds = secrets['credentials']
        self.spreadsheet_id = secrets['spreadsheet_id']
        self.gc = gspread.service_account_from_dict(self.creds)
        self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)

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
            'CARNE_DE_RES', 'MUSLO_CONTRAMUSLO', 'POLLO_PESO'
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
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            
            # Preparar el DataFrame
            df_to_append = self._prepare_dataframe_for_upload(df)
            
            # Convertir el DataFrame a una lista de listas (sin encabezado)
            values_to_append = df_to_append.values.tolist()
            
            # Añadir las filas a la hoja de cálculo
            worksheet.append_rows(values_to_append, value_input_option='USER_ENTERED')
            
            return True, f"{len(values_to_append)} filas añadidas exitosamente a '{worksheet_name}'."
        except gspread.exceptions.WorksheetNotFound:
            return False, f"Error: La hoja de cálculo '{worksheet_name}' no fue encontrada."
        except Exception as e:
            return False, f"Ocurrió un error inesperado: {e}"