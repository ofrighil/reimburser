from typing import NewType, Set

from ._emailer import Emailer
from ._types import FilePath
from ._reimburser_helper import ReimburserHelper

class Reimburser:
    """Calculates individual reimbursements for a given trip, with the option
    of emailing each participant any credits or debts incurred during the trip.


    Attributes:
        send_emails: send out an email to each participant using the given
            email.
    """
    def __init__(
            self, 
            participants_file: FilePath,
            costs_file: FilePath,
            trip_title: str = 'Fun Trip',
            primary_currency: str = 'USD'):
        """Initializes Reimburser.

        Args:
            participants_file: A csv file listing all participants and their
                emails.
            costs_file: A csv file listing all the expenses from the trip. 
            trip_title: The title of the trip.
            primary_currency: The primary currency used during the trip.
        """

        self.trip_title = trip_title
        self.emails: Dict[str, str] =  ReimburserHelper.email_getter(
            participants_file)
        participants: Set[str] = set(self.emails.keys())
        (self.table,
         self.reimbursement_matrices) = ReimburserHelper.reimbs_mats_getter(
            costs_file, 
            participants,
            primary_currency)

    def __repr__(self):
        return f'Reimbursements for {self.trip_title}'

    def send_emails(self) -> None:
        """Sends out an email to all participants.
        """
        emailer = Emailer(
            self.trip_title,
            self.emails,
            self.table,
            self.reimbursement_matrices)
        emailer.send()
