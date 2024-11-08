# Documentación del Módulo de Informes

## Resumen
El módulo `reports.py` proporciona un marco potente para rastrear el rendimiento de procesos y generar informes en PDF. Este módulo contiene dos clases principales:

- `PerformanceTracker`: Una utilidad para rastrear y registrar los tiempos de ejecución de varios procesos.
- `Document`: Una clase para generar y gestionar documentos PDF, con características como encabezados, pies de página, tablas y más.

La clase PerformanceTracker es ideal para monitorear la duración de los procesos, mientras que la clase Document simplifica la creación de PDFs profesionales con texto personalizado, tablas y diseños. La integración de registro en ambas clases garantiza que todas las acciones sean rastreables y transparentes para fines de depuración o auditoría.

Esta documentación describe los atributos y métodos clave de cada clase.

## Clases

### 1. PerformanceTracker
Clase diseñada para rastrear, registrar e informar sobre el rendimiento de varios procesos, facilitando el monitoreo de los tiempos de ejecución.

#### Atributos
  - `logger` (logging.Logger): Instancia del logger para registrar información y errores.
  - `time_format` (str): Formato para las marcas de tiempo.
  - `processes` (List[Dict[str, Optional[str]]]): Lista de procesos con sus tiempos de inicio, fin y duración.

#### Métodos
  - **`start_process(process_name: str) -> None`**: Comienza a rastrear un nuevo proceso registrando el tiempo actual.
  - **`finish_process(process_name: str) -> None`**: Finaliza el rastreo de un proceso, calcula su duración y registra el tiempo de finalización.
  - **`get_report() -> List[Dict[str, Optional[str]]]`**: Devuelve el informe de rendimiento como una lista de diccionarios.
  - **`print_report() -> None`**: Registra los tiempos de ejecución de todos los procesos.

#### Ejemplo
```python
import time
tracker = PerformanceTracker()
tracker.start_process("DataProcessing")
# Simulate some processing time
time.sleep(2)
tracker.finish_process("DataProcessing")
INFO: Ended process: DataProcessing, Duration: 2.00 seconds
report = tracker.get_report()
print(report)
# [{'Process': 'DataProcessing', 'Start': '2024-09-19 10:00:00.000000', 'End': '2024-09-19 10:00:02.000000', 'Duration': 2.0}]
tracker.print_report()
# INFO: Process 'DataProcessing' execution time: 2.00 seconds
```

---

### 2. Document
Clase para generar y gestionar documentos PDF con encabezados, pies de página y contenido personalizados.

#### Atributos
  - `logger` (logging.Logger): Instancia del logger para registrar información y errores.
  - `styles` (Dict[str, ParagraphStyle]): Un diccionario de estilos de párrafo.
  - `contents` (List[Union[Paragraph, Table, Spacer]]): Lista de elementos de contenido que se agregarán al PDF.
  - `num_of_tables` (int): Contador para numerar las tablas en el documento.

#### Métodos
  - **`_on_page(canvas, doc, pagesize=A4) -> None`**: Dibuja la imagen del encabezado, la imagen del pie de página y el número de página en cada página del PDF.
  - **`_on_page_landscape(canvas, doc) -> None`**: Dibuja el encabezado y el pie de página para páginas en orientación horizontal.
  - **`log(message: str, level: Optional[str] = logging.INFO) -> None`**: Registra un mensaje en el nivel de registro especificado si el logger está activo; de lo contrario, lo imprime en la consola.
  - **`add_text(text: str, style_name: str = 'Normal') -> None`**: Agrega un párrafo de texto con un estilo especificado al contenido del documento.
  - **`add_table_from_df(text: str, dataframe, title_columns: int = 1, title_rows: int = 1) -> None`**: Agrega una tabla con un título al contenido del documento. La tabla se crea a partir de un DataFrame y se estiliza según los parámetros proporcionados.
  - **`add_spacer() -> None`**: Agrega un pequeño espacio entre los elementos en el documento.
  - **`save_pdf() -> None`**: Genera el documento PDF y lo guarda en el archivo de salida especificado.

#### Ejemplo
```python
from datetime import datetime
today = f'{datetime.now().year}{datetime.now().month}{datetime.now().day}'

# Create a new PDF document
report = Document(output_dir='reports', file_name=f'Report_{today}')

# Add content to the report
report.add_text('Automated Update Report<br/>{name}', 'Heading1')
report.add_text('This is the content of the report.')

# Save the PDF document
report.save_pdf()
```