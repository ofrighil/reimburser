from typing import Set

from ._reimburser_helpers import (email_getter, reimbs_mats_getter,
    reduction_algorithm)

class Reimburser:
    def __init__(
            self, 
            participants_file: str, 
            costs_file: str, 
            primary_currency: str = 'USD'):

        self.emails = email_getter(participants_file)
        participants: Set[str] = set(self.emails.keys())
        (self.table,
         self.reimbursement_matrices) = reimbs_mats_getter(
            costs_file, 
            participants,
            primary_currency)

    def reduce(self) -> None:
        for matrix in self.reimbursement_matrices.values():
            reduction_algorithm(matrix)

    def save(self) -> None:
        pass

    def send_emails(self) -> None:
        pass
