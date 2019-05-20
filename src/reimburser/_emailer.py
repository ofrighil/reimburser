from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass
from smtplib import SMTP
from typing import Dict

from ._types import Matrix, Table
from ._writer import Writer

class Emailer:
    """A helper class to set up and send emails out.

    Attributes:
        send: Sends out the emails to all participants.
    """
    def __init__(
            self,
            trip_title: str,
            emails: Dict,
            table: Table,
            reimbursement_matrices: Dict[str, Matrix]):
        """Initializes Emailer.

        Args:
            trip_title: The title of the trip (to be used as part of the email
                subject).
            emails: A mapping between the participant's name and the
                participant's email.
            reimbursement_matrices: A dict that maps a currency code to its
                respective cost matrix.
        """
        self.trip_title = trip_title
        self.emails = emails

        #self._max_name_len: int = max(map(len, self.emails.keys()))

        self.writer = Writer(
            self.trip_title,
            table,
            reimbursement_matrices)

    def send(self, subject: str = 'reimbursements', text_type='html') -> None:
        """Sends out the emails to all participants.

        Args:
            subject: The secondary title of the email subject (next to the trip
            title).

        Raises:
            Exception: Text type must either be html or plaintext
        """
        if text_type.lower() == 'html':
            write_body = self.writer.write_html_body
        elif text_type.lower() == 'plain':
            write_body = self.writer.write_plaintext_body
        else:
            raise Exception('Text type must either be html or plain.')

        sender_email = input('Please enter your email account: ')
        password = getpass('Please enter your password: ')

        # TODO: add support for other email servers
        # Currently, this application only supports gmail. Also, the user must
        # give permission for "less secure apps" to access gmail account.
        with SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, password)

            for recipient, recipient_email in self.emails.items():
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = f'{self.trip_title} {subject}'

                body = MIMEText(write_body(recipient), text_type.lower())
                msg.attach(body)

                server.send_message(msg)

        # I think this is redundant, but to be sure the sender email
        # information is deleted.
        del sender_email
        del password
