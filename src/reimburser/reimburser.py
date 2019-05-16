from typing import Set

from ._reimburser_helpers import email_getter, reimbs_mats_getter

class Reimburser:
    def __init__(
            self, 
            participants_file: str, 
            costs_file: str, 
            primary_currency: str = 'USD'):

        self.emails = email_getter(participants_file)
        participants: Set[str] = set(self.emails.keys())
        (self.table,
         self.reimbs_matrices) = reimbs_mats_getter(
            costs_file, 
            participants,
            primary_currency)

    def reduce(self):
        pass

    def send_email(self):
        pass
