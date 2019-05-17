from typing import NewType, Set

from ._reimburser_helpers import (email_getter, reimbs_mats_getter,
    reduction_algorithm, construct_tables)

# Define custom type
FilePath = NewType('FilePath', str)

class Reimburser:
    def __init__(
            self, 
            participants_file: FilePath,
            costs_file: FilePath,
            trip_title: str = 'fun trip',
            primary_currency: str = 'USD'):

        self.trip_title = trip_title
        self.emails = email_getter(participants_file)
        participants: Set[str] = set(self.emails.keys())
        (self.table,
         self.reimbursement_matrices) = reimbs_mats_getter(
            costs_file, 
            participants,
            primary_currency)

        self.summary_tables = construct_tables(self.table)

    def __repr(self):
        return f'Reimbursements for {trip_title}'

    def __str__(self):
        return self.summary_tables

    def reduce(self) -> None:
        for matrix in self.reimbursement_matrices.values():
            reduction_algorithm(matrix)

    def save(self) -> None:
        pass

    def send_emails(self, send_attach=True, save=False) -> None:
        pass
