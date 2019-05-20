import csv
import logging
from typing import Dict, NewType, Set

import numpy as np
import pandas as pd

from ._errors import FieldError, FileFormatError
from ._types import Email, Matrix, Name, Table

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.disabled = True

class ReimburserHelper:
    """A helper class containing all the helper functions used in Reimburser. 

    Please see individual attributes for more information.
    """
    @staticmethod
    def email_getter(participants_file: str) -> Dict[Name, Email]:
        """Reads a csv file listing the participants and their emails.

        Takes in a csv file with columns [participant, email]. This function
        will work correctly even if there is no header. However, the column
        order must be respected else the return dict will be inverted.

        Args:
            participants_file: the csv file listing the participants and their
                emails.

        Returns:
            A dict mapping each participant's name to the accompanying email. 

        Raises:
            FileFormatError: The input file is not formatted as a csv.
        """
        if not participants_file.endswith('.csv'):
            raise FileFormatError('The input file is not formatted as a csv.')
        emails = dict()

        with open(participants_file, 'r') as csv_f:
            header_bool = csv.Sniffer().has_header(csv_f.read(1024))
            csv_f.seek(0)
            csv_reader = csv.reader(csv_f)
            if header_bool:
                logger.info('header detected')
                next(csv_reader) # ignore header
            else:
                logger.info('header not detected')

            for row in csv_reader:
                participant, email = map(str.strip, row) # remove whitespace
                logger.info(f'recording {participant}, email {email}')
                emails[participant] = email

        return emails

    @staticmethod
    def reimbs_mats_getter(
            costs_file: str, 
            participants: Set[str], 
            primary_currency: str) -> (Table, Dict[str, Matrix]):
        """Reads a csv file listing the trip costs information.

        Takes in a csv file that should at least have the columns [reimbursee,
        cost, currency, reimbursers]. While the columns do not have to be in
        that order, I think it makes the most sense to be ordered that way.

        Args:
            costs_file: the csv file listing the trip costs information.
            participants: the set of participants of the trip
            primary_currency: the primary currency used on the trip

        Returns:
            This function returns two objects. The first object is a pandas
            DataFrame. This is the same thing as the input costs_file, but
            stored in a differenet data structure (and with all columns set to
            lowercase). the second object is a dict mapping a currency code to
            the corresponding cost matrix, which is a pandas DataFrame.

        Raises:
            FieldError: The input table is missing required columns.
            FileFormatError: The input file is not formatted as a csv.
        """
        if not costs_file.endswith('.csv'):
            raise FileFormatError('The input file is not formatted as a csv.')

        reimbs_matrices = dict()
        table: pd.DataFrame = pd.read_csv(costs_file)
        # Ensure the table columns are lowercase for simplified operations later.
        lowercased = dict(zip(table.columns, map(str.lower, table.columns)))
        table.rename(columns=lowercased, inplace=True)

        if 'currency' not in table:
            logger.info('table does not have the column "currency"')
            table['currency'] = primary_currency
        else:
            logger.info('table has the column "currency"')
            table.fillna(
                    value={'currency': primary_currency},
                    inplace=True)

        required_columns = {
            'reimbursee', 
            'cost',
            'currency',
            'reimbursers',
        }

        table_columns = set(table.columns)
        # It doesn't really matter if there are extra columns, since the code
        # will just ignore them. However, there will be a problem if the input
        # file doesn't have the required columns.
        if not table_columns >= required_columns:
            raise FieldError('The input table is missing required columns.')

        all_currencies: np.ndarray = table['currency'].drop_duplicates().values
        for c in all_currencies:
            sub_table = table.query(f'currency == "{c}"').drop(columns=['currency'])
            # Make sure the order is right
            sub_table = sub_table[['reimbursee', 'cost', 'reimbursers']]
            logger.info(f'making {c} cost matrix') 
            reimbs_matrices[c] = _matrix_maker(sub_table, participants)

        return table, reimbs_matrices

    @staticmethod
    def construct_tables(table: Table) -> str:
        """Constructs a summary of all the collected information.
        """
        summary_tables = ''
        summary_tables += _construct_master_table(table)

        return summary_tables

def _matrix_maker(sub_table: Table, participants: Set[str]) -> Matrix:
    """Creates the cost matrix for a given cost table for all participants.

    Suppose there are N participants. Then the cost matrix C is defined as an 
    N-by-N hollow matrix (a square matrix whose diagonal elements are all zero,
    or, in this case, NaN) whose elements are either a float or NaN. Each row
    and column take on a participant's name, such that the element C[i, j] 
    denotes the amount participant j owes participant i, or conversely, the
    amount participant i is owed by participant j. If the element value C[i, j]
    is NaN, that means participant j does not owe participant i anything (and
    by definition, one cannot owe oneself money, such that for all i in N,
    C[i, i] is NaN). Let the number of reimbursements be the number of non-NaN
    elements in the cost matrix.

    This function constructs the cost matrix by looking at each row
    (transaction) to determine how much a creditor (the participant who paid
    for the transaction) is owed (the credit) by the debtors (the participants
    who benefited from the transaction). Finally, a reduction algorithm is run
    over the cost matrix to reduce the number of reimbursements.

    Args:
        sub_table: A pandas DataFrame with the columns [reimbursee, cost,
        reimbursers]. This table should contain all transactions related to a
        specific currency. 
        participants: A set of all the participants.

    Returns:
        Returns the cost matrix, which is a pandas DataFrame.
    """
    C = pd.DataFrame(index=participants, columns=participants, dtype=float)

    def not_in(string) -> bool: 
        return True if 'not' in string else False

    num_participants = len(participants)
    for (i, (creditor, credit, debtors)) in sub_table.iterrows():
        logger.info(f'{creditor} is the reimbursee with {credit} currency'
                    + ' credits')
        #reimbursers = set(participants)
        if debtors is np.nan:
            # If the creditor paid for everyone, the debt is equally split
            # amongst everyone, including the creditor.
            debt = _hround(credit / num_participants)
            reimbursers: Set = set(participants) - {creditor}
        else:
            # If the creditor only paid for specific participants, the debt is
            # equally split amongst them, which may or may not include the
            # creditor.
            # If everyone except those beginning with "not" is responsible for
            # the debt, that case is considered by removing those persons
            debtor_set = set(map(str.strip, debtors.split(',')))
            if any(map(not_in, debtor_set)):
                false_debtors: List = list()
                for debtor in debtor_set:
                    if 'not ' == debtor[:4]:
                        false_debtors.append(debtor[4:])
                actual_debtors: Set = set(participants) - set(false_debtors)
                debt = _hround(credit / len(actual_debtors))
                reimbursers: Set = actual_debtors - {creditor}
            else:
                debt = _hround(credit / len(debtor_set))
                reimbursers: Set = debtor_set - {creditor}

        logger.info(f'the reimbursers are {", ".join(reimbursers)},'
                    + f' each of them owe the reimbursee {debt}')

        C.loc[creditor][reimbursers] = debt

    _reduction_algorithm(C)

    return C

def _reduction_algorithm(C: Matrix) -> None:
    """This algorithm reduces the number of reimbursements by first aggregating
    all participants' credits and debts, then redistributing it by looping over
    the participants with debt, from most to least, to reimburse the
    participants with credit, from most to least.

    The algorithm works as follows: Let there be a list of numbers which sum to
    zero. Let the negative numbers indicate debt and the positive numbers
    indicate credit. The largest debt (the debtor) is picked out and used to
    pay back the largest credit(s) (the creditor(s)) until the debt is
    repaid. This process continues until all debts are repaid.

    Since a pandas DataFrame is a mutable object, the reduction is done in
    place.

    Args:
        C: The cost matrix, a pandas DataFrame.

    """
    credits: pd.Series = C.sum(axis=1)
    debts: pd.Series = C.sum()
    balance = credits - debts

    C.loc[:, :] = np.nan # reset the matrix

    logger.info(f'the balance is zero: {abs(_hround(sum(balance))) == 0.0}')
    
    while balance.all():
        debtor: str = balance.idxmin()
        logger.info(f'{debtor}\'s total debt amounts to {balance[debtor]}' \
                    + ' currency credits')

        while balance[debtor] < 0.0:
            creditor: str = balance.idxmax()
            logger.info(f'{creditor} has been chosen')

            if balance[creditor] < abs(balance[debtor]):
                logger.info(f'{debtor}\'s debt will be partially repaid by' \
                            + f' paying {creditor} {balance[creditor]}' \
                            + ' currency credits')
                C.loc[creditor, debtor] = balance[creditor]
                balance[debtor] = _hround(balance[debtor] +
                        balance[creditor])
                balance[creditor] = 0.0
            else:
                logger.info(f'{debtor}\'s debt will be fully repaid by' \
                            + f' paying {creditor} {-balance[debtor]}' \
                            + ' currency credits')
                C.loc[creditor, debtor] = -balance[debtor]
                balance[creditor] = _hround(balance[creditor] +
                        balance[debtor])
                balance[debtor] = 0.0

def _hround(n: float, r: int = 2) -> int:
    """Implements half round up."""
    diff = round((round(n, r+1) - round(n, r)) * 10 ** (r+1))
    if diff >= 5:
        return n + (10 - diff) * 10 ** -(r+1)
    else:
        return round(n, r)

def _construct_master_table(table: Table) -> str:
    """Constructs a print friendly costs table.
    """
    fields = [
        'reimbursee',
        'cost',
        'currency',
        'reimbursers',
    ]

    if 'notes' in table.columns:
        fields.append('notes')

    side_reimbs = table['reimbursers'].notna()
    def add_space(string): return ', '.join(string.split(','))
    spaced_reimbursers = table['reimbursers'][side_reimbs].apply(add_space)

    stringified_table = table[fields].fillna(value={'reimbursers': 'everyone'})
    stringified_table['cost'] = stringified_table['cost'].apply(str)
    stringified_table['reimbursers'][side_reimbs] = spaced_reimbursers

    # In order to format the table properly automatically, it is necessary to
    # adjust all values relative to the longest element in the column.
    max_name_len: int = max(stringified_table['reimbursee'].str.len().max(),
        len(fields[0]))
    # The 1 is for the space and the 3 is for the currency code length.
    max_amt_len: int = stringified_table['cost'].str.len().max()+1+3
    max_reimb_len: int = max(stringified_table['reimbursers'].str.len().max(),
        len(fields[3]))

    header = fields[0].center(max_name_len) + ' | ' \
        + fields[1].center(max_amt_len) + ' | ' \
        + fields[3].center(max_reimb_len)
    separator = '-' * max_name_len + ' | ' \
        + '-' * max_amt_len + ' | ' \
        + '-' * max_reimb_len

    if 'notes' in fields:
        max_note_len: int = max(stringified_table['notes'].str.len().max(),
            len('notes'))
        header += ' | ' + 'notes'.center(max_note_len) + '\n'
        separator += ' | ' + '-' * max_note_len + '\n'
    else:
        header += '\n'
        separator += '\n'

    table_string = header + separator

    for (i, row) in stringified_table.iterrows():
        (reimbursee,
         cost,
         currency,
         reimbursers,
         *notes) = row

        table_string += reimbursee.ljust(max_name_len) + ' | ' \
            + (cost + ' ' + currency).center(max_amt_len) + ' | ' \
            + reimbursers.center(max_reimb_len)

        if len(notes) == 0:
            table_string += '\n'
        else:
            if notes[0] is np.nan:
                table_string += ' |\n'
            else:
                table_string += ' | ' + notes[0].ljust(max_note_len) + '\n'

    return table_string
