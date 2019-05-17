import csv
import logging
from typing import Dict, NewType, Set

import numpy as np
import pandas as pd

from ._custom_errors import FieldError, FileFormatError
from ._custom_types import Email, Matrix, Name, Table

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.disabled = True

def email_getter(participants_file: str) -> Dict[Name, Email]:
    if not participants_file.endswith('.csv'):
        raise FileFormatError('The input file is not formatted as a csv')
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

def reimbs_mats_getter(
        costs_file: str, 
        participants: Set[str], 
        primary_currency: str) -> (Table, Dict[str, Matrix]):
    if not costs_file.endswith('.csv'):
        raise FileFormatError('The input file is not formatted as a csv')

    reimbs_matrices = dict()
    table: pd.DataFrame = pd.read_csv(costs_file)
    # Ensure the table fields are lowercase for simplified operations later.
    lowercased = dict(zip(table.columns, map(str.lower, table.columns)))
    table.rename(columns=lowercased, inplace=True)

    if 'currency' not in table:
        logger.info('table does not have the field "currency"')
        table['currency'] = primary_currency
    else:
        logger.info('table has the field "currency"')
        table.fillna(
                value={'currency': primary_currency},
                inplace=True)

    required_fields = {
        'reimbursee', 
        'cost',
        'currency',
        'reimbursers',
    }

    table_fields = set(table.columns)
    if not table_fields >= required_fields:
        raise FieldError('The input table is missing required fields')

    all_currencies: np.ndarray = table['currency'].drop_duplicates().values
    for c in all_currencies:
        sub_table = table.query(f'currency == "{c}"').drop(columns=['currency'])
        # Make sure the order is right
        sub_table = sub_table[['reimbursee', 'cost', 'reimbursers']]
        logger.info(f'making {c} cost matrix') 
        reimbs_matrices[c] = _matrix_maker(sub_table, participants)

    return table, reimbs_matrices

def _matrix_maker(sub_table: Table, participants: Set[str]) -> Matrix:
    # C is the cost matrix
    C = pd.DataFrame(index=participants, columns=participants, dtype=float)

    num_participants = len(participants)
    for (i, (creditor, credit, debtors)) in sub_table.iterrows():
        logger.info(f'{creditor} is the reimbursee with {credit} currency'
                    + ' credits')
        reimbursers = set(participants)
        if debtors is np.nan:
            # If the creditor paid for everyone, the debt is equally split
            # amongst everyone, including the creditor.
            debt = _hround(credit / num_participants)
            reimbursers = set(participants) - {creditor}
        else:
            # TODO: Implement 'not' case
            # If the creditor only paid for specific participants, the debt is
            # equally split amongst them, which may or may not include the
            # creditor.
            debtor_set = set(map(str.strip, debtors.split(',')))
            debt = _hround(credit / len(debtor_set))
            reimbursers = debtor_set - {creditor}

        logger.info(f'the reimbursers are {", ".join(reimbursers)},'
                    + f' each of them owe the reimbursee {debt}')

        C.loc[creditor][reimbursers] = debt

    _reduction_algorithm(C)

    return C

def _reduction_algorithm(C: Matrix) -> None:
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
                balance[debtor] = _hround(balance[debtor] -
                        balance[creditor])
                balance[creditor] = 0.0
            else:
                logger.info(f'{debtor}\'s debt will be fully repaid by' \
                            + f' paying {creditor} {-balance[debtor]}' \
                            + ' currency credits')
                C.loc[creditor, debtor] = -balance[debtor]
                balance[creditor] = _hround(balance[creditor] -
                        balance[debtor])
                balance[debtor] = 0.0

def _hround(n: float, r: int = 2) -> int:
    """Implements half round up."""
    diff = round((round(n, r+1) - round(n, r)) * 10 ** (r+1))
    if diff >= 5:
        return n + (10 - diff) * 10 ** -(r+1)
    else:
        return round(n, r)

def construct_tables(table: Table) -> str:
    summary_tables = ''
    summary_tables += _construct_master_table(table)

    return summary_tables

def _construct_master_table(table: Table) -> str:
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
    def add_decimals(num): return format(num, '.2f')
    stringified_table['cost'] = stringified_table['cost'].apply(add_decimals)
    stringified_table['reimbursers'][side_reimbs] = spaced_reimbursers

    # In order to format the table properly automatically, it is necessary to
    # adjust all values relative to the longest element in the column.
    max_name_len: int = max(stringified_table['reimbursee'].str.len().max(),
        len(fields[0]))
    # The 1 is for the space and the 3 is for the currency code length
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
