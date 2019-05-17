import asyncio

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from getpass import getpass
from smtplib import SMTP
from typing import Dict

from ._types import Matrix, Table

class Emailer:
    def __init__(
            self,
            trip_title: str,
            emails: Dict,
            reimbursement_matrices: Dict[str, Matrix],
            summary_tables: str):
        self.trip_title = trip_title
        self.emails = emails
        self.reimbursement_matrices = reimbursement_matrices
        self.summary_tables = summary_tables

        self_.max_name_len: int = max(map(len, self.emails.keys()))

    def send(self, subject: str = 'reimbursements'):
        sender_email = input('Please enter your email account: ')
        password = getpass('Please enter your password: ')

        # TODO: support for other email servers
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
                msg['Subject'] = f'{self.trip_title} reimbursements'

                body = MIMEText(self.write_body(recipient), 'plain')
                msg.attach(body)

                server.send_message(msg)

        # I think this is unnecessary, but below I make sure that the email
        # information is deleted.
        del sender_email
        del password

    def write_body(self, recipient: str) -> str:
        body = f'Dear {recipient},\n\n' \
            + 'You are receiving this message because you participated ' \
            + f'in {self.trip_title}.\n\n' \
            + 'I hope you had a pleasant time.\n\n' \
            + 'If you have debts to repay, please be courteous and ' \
            + 'reimburse your fellow participant(s) in a timely fashion.\n' \

        subbody_debt = ''
        subbody_credit = ''
        for currency, reimbs in self.reimbursement_matrices.items():
            debts = reimbs[recipient].dropna()
            credits = reimbs[recipient].dropna()
            for creditor, credit in credits.iteritems():
                creditor = creditor.rjust(self._max_name_len)
                amount = f'{credit} {currency}'.ljust(6+1+3)
                subbody_debt += '\t' + creditor + ' | ' + amount + '\n'
            for debtor, debt in debts.iteritems():
                debtor = debtor.rjust(self._max_name_len)
                amount = f'{debt} {currency}'.ljust(6+1+3)
                subbody_credit += '\t' + debtor + ' | ' + amount + '\n'

        if len(subbody_debt):
            subbody_debt = 'Please reimburse the following participant(s):\n' \
                + subbody_debt
        else:
            subbody_debt += 'You do not need to reimburse anyone.\n'

        if len(subbody_credit):
            subbody_credit = 'The following participant(s) are obligated to ' \
                + 'reimburse you.\n' + subbody_credit
        else:
            subbody_credit += 'You do not have any outstanding ' \
                + 'reimbursements.\n'

        body += '\n' + subbody_debt + '\n' + subbody_credit
        #body += 'The remaining email gives an overview of all the expenses ' \
        #    + f'from the trip:\n\n{self.summary_tables}'

        return body
