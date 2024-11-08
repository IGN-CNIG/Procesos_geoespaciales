from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, List, Dict

import matplotlib.pyplot as plt
from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate
from reportlab.platypus import Paragraph, Table, Spacer, KeepTogether, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PerformanceTracker:
    """
    A class for tracking and logging the performance of various processes.

    Attributes:
        logger (logging.Logger): Logger instance for logging information and errors.
        time_format (str): Format for timestamps.
        processes (List[Dict[str, Optional[str]]]): List of processes with their start times, end times, and durations.

    ## Methods
        start_process(process_name: str) -> None:
            Starts tracking a new process by recording the current time.
        finish_process(process_name: str) -> None:
            Ends tracking of a process, calculates its duration, and records the end time.
        get_report() -> List[Dict[str, Optional[str]]]:
            Returns the performance report as a list of dictionaries.
        print_report() -> None:
            Logs the execution times of all processes.
            
    Example:
        >>> tracker = PerformanceTracker()
        >>> tracker.start_process("DataProcessing")
        >>> # Simulate some processing time
        >>> import time
        >>> time.sleep(2)
        >>> tracker.finish_process("DataProcessing")
        INFO: Ended process: DataProcessing, Duration: 2.00 seconds
        >>> report = tracker.get_report()
        >>> print(report)
        [{'Process': 'DataProcessing', 'Start': '2024-09-19 10:00:00.000000', 'End': '2024-09-19 10:00:02.000000', 'Duration': 2.0}]
        >>> tracker.print_report()
        INFO: Process 'DataProcessing' execution time: 2.00 seconds
    """
    logger: logging.Logger = logging.getLogger(__name__)  # Obtain a logger for this module/class

    def __init__(self, time_format: str = '%Y-%m-%d %H:%M:%S.%f') -> None:
        """
        Initializes the PerformanceTracker with a specified time format.

        Parameters:
            time_format (str): The format string for datetime. Defaults to '%Y-%m-%d %H:%M:%S.%f'.
        """
        self.time_format = time_format
        self.processes = []

    def start_process(self, process_name: str) -> None:
        """
        Starts tracking a new process by recording the current time.

        Parameters:
            process_name (str): The name of the process to start.
        """
        now = datetime.now()
        self.processes.append({
            'Process': process_name,
            'Start': now.strftime(self.time_format),
            'End': None,
            'Duration': None
        })
        self.logger.info(f'Started process: {process_name}')
        
    def finish_process(self, process_name: str) -> None:
        """
        Ends tracking of a process by recording the current time and calculating its duration.

        Parameters:
            process_name (str): The name of the process to finish.
        """
        for process in self.processes:
            if process['Process'] == process_name:
                end_time = datetime.now()
                start_time = datetime.strptime(process['Start'], self.time_format)
                duration = (end_time - start_time).total_seconds()

                process['End'] = end_time.strftime(self.time_format)
                process['Duration'] = duration
                self.logger.info(f'Ended process: {process_name}, Duration: {duration:.2f} seconds')
                break
        else:
            self.logger.warning(f'Process not found: {process_name}')
    
    def get_report(self) -> List[Dict[str, Optional[str]]]:
        """
        Returns the performance report as a list of dictionaries.

        Returns:
            List[Dict[str, Optional[str]]]: List of processes with their start times, end times, and durations.
        """
        return self.processes
    
    def print_report(self) -> None:
        """
        Logs the execution times of all processes in seconds.
        """
        for process in self.processes:
            if process['Duration'] is not None:
                duration_seconds = process['Duration']
                self.logger.info(f"Process '{process['Process']}' execution time: {duration_seconds:.2f} seconds")
            else:
                self.logger.info(f"Process '{process['Process']}' has not finished yet.")


# CREDITS:
# https://nicd.org.uk/knowledge-hub/creating-pdf-reports-with-reportlab-and-pandas

# Header and footer info for the document
HEADER_IMAGE = 'src/images/Encabezado.PNG'
HEADER_IMAGE_HEIGHT = 35
FOOTER_IMAGE = 'src/images/Pie_Pagina.PNG'
FOOTER_IMAGE_HEIGHT = 35
FOOTER_IMAGE_WIDTH = 400
BOTTOM_PADDING = 18

class Document:
    """
    A class to generate and manage PDF documents with customized headers, footers, and content.

    Attributes:
        logger (logging.Logger): Logger instance for logging information and errors.
        styles (Dict[str, ParagraphStyle]): A dictionary of paragraph styles.
        contents (List[Union[Paragraph, Table, Spacer]]): List of content elements to be added to the PDF.
        num_of_tables (int): Counter for numbering tables in the document.

    ## Methods
        _on_page(canvas, doc, pagesize=A4) -> None:
            Draws the header image, footer image, and page number on each page of the PDF.
        _on_page_landscape(canvas, doc) -> None:
            Draws the header and footer for landscape-oriented pages.
        log(message: str, level: Optional[str] = logging.INFO) -> None:
            Logs a message at the specified logging level if the logger is active, otherwise prints it to the console.
        add_text(text: str, style_name: str = 'Normal') -> None:
            Adds a text paragraph with a specified style to the document contents.
        add_table_from_df(text: str, dataframe, title_columns: int = 1, title_rows: int = 1) -> None:
            Adds a table with a title to the document contents. The table is created from a DataFrame and styled based on the provided parameters.
        add_spacer() -> None:
            Adds a small space between elements in the document.
        save_pdf() -> None:
            Generates the PDF document and saves it to the specified output file.
    """
    logger:logging.Logger = logging.getLogger(__name__)  # Obtain a logger for this module/class
    def __init__(self, output_dir: str, file_name:str, template=None) -> None:
        """
        Initializes the PDF document with the specified output directory, file name, and styles.

        Parameters:
            output_dir (str): Directory where the PDF file will be saved.
            file_name (str): Name of the PDF file.
            template (Optional[PageTemplate]): Optional custom page template to use. If not provided, a default portrait template is used.

        Raises:
            Exception: If there is an error creating the document.
        """
        self.log('Starting document generation')
        self.styles = getSampleStyleSheet()
        # Alter the current styles
        self.styles.get('Heading2')._setKwds(**{'alignment': 4, 'fontSize': 13})
        self.styles.get('Heading3')._setKwds(**{'alignment': 4, 'fontSize': 12})
        self.styles.get('Normal')._setKwds(**{'alignment': 4, 'fontSize': 11})
        # Add new style
        self.styles.add(ParagraphStyle(name='Table_Title', parent=self.styles['Normal'], alignment=1, fontSize=10))
        # Here we start the document
        if template is None:
            padding = {'leftPadding': 72, 'rightPadding': 72, 'topPadding': 72, 'bottomPadding': (FOOTER_IMAGE_HEIGHT + BOTTOM_PADDING)}
            portrait_frame = Frame(0, 0, *A4, **padding)
            template = PageTemplate(id='portrait', frames=portrait_frame, onPage=self._on_page, pagesize=A4)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.__doc = BaseDocTemplate(
            Path(output_dir).joinpath(f'{file_name}.pdf').as_posix(),
            pageTemplates=[template]
        )

        self.contents = []
        self.num_of_tables = 0

    def _on_page(self, canvas, doc, pagesize=A4) -> None:
        """
        Draws the header image, footer image, and page number on each page of the PDF.

        Parameters:
            canvas: The canvas object to draw on.
            doc: The document object being created.
            pagesize (tuple): The size of the page, defaults to A4.
        """
        header_image = Path.cwd().joinpath(HEADER_IMAGE).as_posix()
        canvas.drawImage(header_image, x=0, y=(pagesize[1] - HEADER_IMAGE_HEIGHT), width=pagesize[0], height=HEADER_IMAGE_HEIGHT)
        footer_image = Path.cwd().joinpath(FOOTER_IMAGE).as_posix()
        canvas.drawImage(footer_image, x=(pagesize[0]/2 - FOOTER_IMAGE_WIDTH/2), y=BOTTOM_PADDING, width=FOOTER_IMAGE_WIDTH, height=FOOTER_IMAGE_HEIGHT)
        canvas.drawCentredString(pagesize[0] - 50, BOTTOM_PADDING, str(canvas.getPageNumber()))

    def _on_page_landscape(self, canvas, doc):
        """
        Draws the header and footer for landscape-oriented pages.

        Parameters:
            canvas: The canvas object to draw on.
            doc: The document object being created.
        """
        return self._on_page(canvas, doc, pagesize=landscape(A4))
    
    @classmethod
    def log(cls, message:str, level:Optional[str] = logging.INFO) -> None:
        """
        Logs a message at the specified logging level if the logger is active, otherwise prints it in console.

        Parameters:
            message (str): The message to log.
            level (Optional[int]): The logging level to use (e.g., logging.DEBUG, logging.INFO).

        If the level is not recognized, the message will be logged at the INFO level.
        """
        if cls.logger:
            if level == logging.DEBUG:
                cls.logger.debug(message)
            elif level == logging.WARNING:
                cls.logger.warning(message)
            elif level == logging.ERROR:
                cls.logger.error(message)
            elif level == logging.CRITICAL:
                cls.logger.critical(message)
            else:
                cls.logger.info(message)
        else:
            print(message)

    def add_text(self, text: str, style_name:str ='Normal') -> None:
        """
        Adds a text paragraph with a specified style to the document contents.

        Parameters:
            text (str): The text to add to the document.
            style_name (str): The name of the style to use. Defaults to 'Normal'.
        """
        self.log('Adding text to document', logging.DEBUG)
        style = self.styles.get(style_name)
        self.contents.append(Paragraph(text, style))
        self.add_spacer()
    
    def add_table_from_df(self, text: str, dataframe, title_columns:int=1, title_rows:int=1) -> None:
        """
        Adds a table with its title to the document content. The table is created from a DataFrame and styled based on the provided parameters.

        Parameters:
            text (str): Table title (to be added to the bottom of the table with its table number).
            dataframe (pd.DataFrame): DataFrame containing the table data.
            title_columns (int): Number of columns to color in grey. Defaults to 1.
            title_rows (int): Number of rows to color in grey. Defaults to 1.
        """
        self.num_of_tables += 1
        self.log(f'Adding table {self.num_of_tables} to document', logging.DEBUG)
        # https://docs.reportlab.com/reportlab/userguide/ch7_tables/#table-user-methods
        style = [
                ('FONTNAME', (0, 0), (-1, title_rows-1), 'Helvetica-Bold'), # Filas en negrita
                ('FONTNAME', (0, 0), (title_columns-1, -1), 'Helvetica-Bold'), # Columnas en negrita
                ('LINEBELOW', (0, title_rows-1), (-1, title_rows-1), 1, colors.black),
                ('LINEAFTER', (title_columns-1, 0), (title_columns-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 0), (-1, title_rows-1), [colors.lightgrey]),
                ('ROWBACKGROUNDS', (0, 0), (title_columns-1, -1), [colors.lightgrey]),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER')
                ]
        
        text = f'Tabla {self.num_of_tables}. {text}'
        if dataframe.empty:
            style = self.styles.get('Normal')
            table = Paragraph('&#9888 [No se han encontrado datos]', style)
        else:
            table = Table(
                [[col for col in dataframe.columns]] + dataframe.values.tolist(),
                style=style,
                spaceBefore=6, 
                spaceAfter=6
            )
            
        style = self.styles.get('Table_Title') if self.styles.get('Table_Title') is not None else self.styles.get('Definition')
        title = Paragraph(text, style)
        self.contents.append(KeepTogether([table, title]))
        self.add_spacer()
        
    def add_plot_from_df(self, text:str, dataframe, xlabel:str, ylabel:str) -> None:
        # Set the index to 'Año' for a cleaner x-axis
        # Plot the DataFrame
        dataframe.plot(x=dataframe.columns[0], y=dataframe.columns[1], marker='o', linestyle='-', grid=True, title=text)

        # Add labels
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        # Create a BytesIO buffer to save the plot in-memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        # Move the buffer's pointer to the beginning
        buffer.seek(0)
        # Insert the image into the PDF (directly from the BytesIO object)
        img = Image(buffer)
        img.drawHeight = 400  # Adjust the height of the image
        img.drawWidth = 500   # Adjust the width of the image

        # Append the image to the elements
        self.contents.append(img)
        
    def add_spacer(self) -> None:
        """Adds a small space between elements in the document."""
        self.contents.append(Spacer(1,6))
    
    def save_pdf(self) -> None:
        """Generates the PDF document and saves it to the specified output file."""
        self.log('Saving pdf document')
        try:
            self.__doc.build(self.contents)
            self.log(f'The document has been saved to: {self.__doc.filename}')
        except Exception as e:
            self.log(f'The document could not be saved: {str(e)}', logging.CRITICAL)