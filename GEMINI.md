# GEMINI.md - Procesador de Reportes (Comedores Comunitarios)

## Project Overview
This project is a modular Python application built with **Streamlit** to automate the processing, normalization, and distribution of community canteen reports. It takes raw Excel files with complex structures and transforms them into structured data for analysis, generates transport guides in PDF, and integrates with Google Sheets.

### Core Technologies
- **Frontend:** Streamlit
- **Data Processing:** Pandas, Openpyxl, xlrd
- **PDF Generation:** ReportLab
- **Integrations:** Gspread (Google Sheets), SMTPLib (Email)
- **Utilities:** Regex for smart extraction, Logging for traceability

### Architecture
The project follows a modular architecture:
- `app.py`: Main entry point and Streamlit UI orchestration.
- `excel_processor.py`: Core logic for table parsing and product mapping.
- `data_extractor.py`: Specialized metadata extraction (Programs, Dates, Remittances).
- `pdf_generator.py`: Logic for generating transport guide PDFs.
- `google_sheets_handler.py`: Interface for Google Sheets operations.
- `utils.py`: Shared helper functions for formatting, validation, and Excel creation.
- `logger_config.py`: Centralized logging configuration.

## Building and Running

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
1. Create a `.streamlit/secrets.toml` file based on `.streamlit/secrets.toml.template`.
2. Populate it with Google Sheets credentials and Email SMTP settings.

### Running the Application
```bash
streamlit run app.py
```

## Development Conventions

### Coding Style
- **Modular Design:** Features like PDF generation or email sending are encapsulated in their own modules.
- **Docstrings:** Modules and major classes use docstrings to explain their purpose (mostly in Spanish).
- **Type Hinting:** Minimal but present in some areas; prioritize clarity in data structures.

### Data Processing
- **Robust Extraction:** Uses `ExcelProcessor` to handle varying Excel structures by searching for keywords and patterns rather than fixed cell coordinates.
- **Validation:** Always use `FileValidator` before processing and `UtilsHelper.validar_dataframe` after processing to ensure data integrity.
- **Product Mapping:** Product detection is based on regex patterns defined in `ExcelProcessor`. Supported products: Cerdo, Res, Muslo/Contramuslo, Pechuga, Tilapia.

### Logging & Error Handling
- Use the centralized logger from `logger_config.py`.
- Wrap external integrations (Email, GSheets) in try-except blocks to prevent UI crashes.
- Report errors to the user via `st.error()` or `st.warning()`.

## Key Files
- `app.py`: Streamlit UI and Tab management.
- `excel_processor.py`: Table detection and product extraction logic.
- `data_extractor.py`: Header and metadata parsing logic.
- `pdf_generator.py`: PDF template and generation logic.
- `utils.py`: Excel download generation and data validation helpers.
- `google_sheets_handler.py`: Gspread wrapper for data persistence.
