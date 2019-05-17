from typing import NewType, Set

from ._types import FilePath
from ._reimburser_helper import ReimburserHelper

class Reimburser:
    def __init__(
            self, 
            participants_file: FilePath,
            costs_file: FilePath,
            trip_title: str = 'Fun Trip',
            primary_currency: str = 'USD'):

        self.trip_title = trip_title
        self.emails: Dict[str, str] =  ReimburserHelper.email_getter(
            participants_file)
        participants: Set[str] = set(self.emails.keys())
        (self.table,
         self.reimbursement_matrices) = ReimburserHelper.reimbs_mats_getter(
            costs_file, 
            participants,
            primary_currency)

        self.summary_tables: str = ReimburserHelper.construct_tables(
            self.table)

    def __repr__(self):
        return f'Reimbursements for {self.trip_title}'

    def __str__(self):
        return self.summary_tables

    def save(self) -> None:
        pass

    def send_emails(self, send_attach=True, save=False) -> None:
        pass
