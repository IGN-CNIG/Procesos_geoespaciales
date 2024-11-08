# Reports Module Documentation

## Overview
The `reports.py` module provides a powerful framework for tracking the performance of processes and generating PDF reports. This module contains two primary classes:

- `PerformanceTracker`: A utility for tracking and logging the execution times of various processes.
- `Document`: A class for generating and managing PDF documents, with features like customized headers, footers, tables, and more.

The PerformanceTracker class is ideal for monitoring process durations, while the Document class simplifies the creation of professional PDFs with custom text, tables, and layouts. The logging integration in both classes ensures that all actions are traceable and transparent for debugging or auditing purposes.

This documentation outlines the key attributes and methods of each class, along with example usage.


## Classes

### 1. PerformanceTracker
A class designed to track, log, and report the performance of various processes, making it easier to monitor execution times.

#### Attributes
  - `logger` (logging.Logger): Logger instance for logging information and errors.
  - `time_format` (str): Format for timestamps.
  - `processes` (List[Dict[str, Optional[str]]]): List of processes with their start times, end times, and durations.

#### Methods
  - **`start_process(process_name: str) -> None`**: Starts tracking a new process by recording the current time.
  - **`finish_process(process_name: str) -> None`**: Ends tracking of a process, calculates its duration, and records the end time.
  - **`get_report() -> List[Dict[str, Optional[str]]]`**: Returns the performance report as a list of dictionaries.
  - **`print_report() -> None`**: Logs the execution times of all processes.

#### Example
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
[{'Process': 'DataProcessing', 'Start': '2024-09-19 10:00:00.000000', 'End': '2024-09-19 10:00:02.000000', 'Duration': 2.0}]
tracker.print_report()
INFO: Process 'DataProcessing' execution time: 2.00 seconds
```

---

### 2. Document
A class to generate and manage PDF documents with customized headers, footers, and content.

#### Attributes
  - `logger` (logging.Logger): Logger instance for logging information and errors.
  - `styles` (Dict[str, ParagraphStyle]): A dictionary of paragraph styles.
  - `contents` (List[Union[Paragraph, Table, Spacer]]): List of content elements to be added to the PDF.
  - `num_of_tables` (int): Counter for numbering tables in the document.

#### Methods
  - **`_on_page(canvas, doc, pagesize=A4) -> None`**: Draws the header image, footer image, and page number on each page of the PDF.
  - **`_on_page_landscape(canvas, doc) -> None`**: Draws the header and footer for landscape-oriented pages.
  - **`log(message: str, level: Optional[str] = logging.INFO) -> None`**: Logs a message at the specified logging level if the logger is active, otherwise prints it to the console.
  - **`add_text(text: str, style_name: str = 'Normal') -> None`**: Adds a text paragraph with a specified style to the document contents.
  - **`add_table_from_df(text: str, dataframe, title_columns: int = 1, title_rows: int = 1) -> None`**: Adds a table with a title to the document contents. The table is created from a DataFrame and styled based on - the provided parameters.
  - **`add_spacer() -> None`**: Adds a small space between elements in the document.
  - **`save_pdf() -> None`**: Generates the PDF document and saves it to the specified output file.

#### Example
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