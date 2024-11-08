import os
from typing import Optional, List

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP, SMTP_SSL

SUBTYPES = ['plain', 'html', 'xml'] # Allowed content subtypes

class Email():
    """
    A class to create and send email messages with support for multiple content types and attachments.

    Attributes:
        email_message (MIMEMultipart): The main email message container.
        subject (str): The subject of the email.
        contents (List[MIMEText]): A list of MIMEText objects containing the email content.
        text_subtype (str): The subtype of the email content (e.g., 'plain', 'html', 'xml').
        attachments (List[MIMEApplication]): A list of MIMEApplication objects for file attachments.
    """
    
    def __init__(self) -> None:
        """Initializes an Email instance with default values."""
        self.email_message: MIMEMultipart = MIMEMultipart()
        self.subject:str = ''
        self.contents:List[MIMEText] = []
        self.text_subtype:str = 'plain'
        self.attachments:List[MIMEApplication] = []
    
    def set_subject(self, text:str) -> None:
        """
        Sets the subject of the email.

        Parameters:
            text (str): The subject text of the email.
        """
        self.subject = text
    
    def set_content_type(self, subtype:str) -> None:
        """
        Sets the content type (subtype) of the email message.

        Parameters:
            subtype (str): The content subtype (e.g., 'plain', 'html', 'xml').

        Raises:
            ValueError: If the specified subtype is not in the allowed SUBTYPES list.
        """
        if subtype.lower() in SUBTYPES:
            self.email_message.set_default_type(subtype.lower())
        else:
            raise ValueError('[ERROR] The specified subtype is not allowed.')
        
    def get_content_type(self) -> str:
        """
        Gets the current content type (subtype) of the email message.

        Returns:
            str: The current content type (e.g., 'plain', 'html', 'xml').
        """
        return self.email_message.get_content_type()
    
    def add_content(self, text:str) -> None:
        """
        Adds text content to the email message.

        Parameters:
            text (str): The text content to be added to the email.
        """
        msg = MIMEText(text, self.text_subtype)
        self.contents.append(msg)
        
    def attach_file(self, filename:str):
        """
        Attaches a file to the email message.

        Parameters:
            filename (str): The path to the file to be attached.

        Raises:
            FileNotFoundError: If the specified file cannot be found.
        """
        try:
            with open(filename, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=os.path.basename(filename)
                )
            # After the file is closed
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'
            self.attachments.append(part)
        except FileNotFoundError:
            raise FileNotFoundError(f'[ERROR] The file {filename} was not found.')
    
    def send(self, smtp_host:str, smtp_port:int, email_from:str, password:Optional[str], email_to:str) -> bool:
        """
        Sends the email using the specified SMTP server.
        
        Notes:
        - If `password` is provided, the SMTP connection will use SSL and TLS encryption. 
        - If `password` is not provided, the connection will default to standard SMTP without encryption.
        - Make sure the `smtp_host` and `smtp_port` are configured correctly, especially if using an external service like Gmail.
        - This function does not support multiple recipients in `email_to`. Only a single recipient address is accepted.

        Parameters:
            smtp_host (str): The SMTP server host.
            smtp_port (int): The SMTP server port.
            email_from (str): The sender's email address.
            password (Optional[str]): The password for the sender's email account. If None, standard SMTP will be used.
            email_to (str): The recipient's email address.

        Returns:
            bool: True if the email is sent successfully, False otherwise.

        Raises:
            Exception: If there is an issue during the email sending process.

        Example:
            >>> email_instance = Email()
            >>> email_instance.set_subject("Test")
            >>> email_instance.add_content("This is a test email.")
            >>> email_instance.send(smtp_host="smtp.gmail.com", smtp_port=465, email_from="you@example.com", password="yourpassword", email_to="recipient@example.com")
            True
        """
        # Set email headers
        self.email_message['Subject'] = self.subject
        self.email_message['From'] = email_from
        self.email_message['To'] = email_to
        
        # Attach content and files
        for content in self.contents:
            self.email_message.attach(content)
        for attachment in self.attachments:
            self.email_message.attach(attachment)
        
        try:
            if password:
                ## this invokes the secure SMTP protocol (port 465, uses SSL)
                mail_server = SMTP_SSL(host=smtp_host, port=smtp_port)
                # Identify ourselves to smtp gmail client
                mail_server.ehlo()
                # Secure our email with tls encryption
                mail_server.starttls()
                # Re-identify ourselves as an encrypted connection
                mail_server.ehlo()
                mail_server.login(email_from, password)
            else:
                # use this for standard SMTP protocol   (port 25, no encryption)
                mail_server = SMTP(host=smtp_host, port=smtp_port)
            
            mail_server.set_debuglevel(False)
            mail_server.sendmail(from_addr=self.email_message['From'], to_addrs=self.email_message['To'].strip(' ').split(','), msg=self.email_message.as_string())
            print(f'Email successfully sent to {email_to}')
            return True
        except Exception as e:
            print(f'[ERROR] {e}')
            return False
        finally:
                mail_server.quit()

# ¡TEST EMAIL SENDING!
if __name__ == '__main__':
    import os
    email = Email()
    email.set_subject('Email de prueba')
    email.add_content('Esto es una prueba')
    email.attach_file(filename=f'{os.getcwd()}/config.ini')
    email.send(smtp_host=os.getenv('SMTP_HOST'), smtp_port=os.getenv('SMTP_PORT'), email_from=os.getenv('FROM'), password=None, email_to=os.getenv('TO'))