import csv
import logging
from typing import Dict, NewType, Set

import numpy as np
import pandas as pd

# Define custom types
Table = NewType('Table', pd.DataFrame)
Matrix = NewType('Matrix', pd.DataFrame)

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def email_getter(participants_file: str) -> Dict[str, str]:
    logger.info(f'reading {participants_file}')
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
    reimbs_matrices = dict()
    table: pd.DataFrame = pd.read_csv(costs_file)

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

    if set(table.columns) != required_fields:
        raise Exception('The input table fields do not match the required \
                fields')

    all_currencies: np.ndarray = table['currency'].drop_duplicates().values
    for c in all_currencies:
        sub_table = table.query(f'currency == "{c}"').drop(columns=['currency'])
        # Make sure the order is right
        sub_table = sub_table[['reimbursee', 'cost', 'reimbursers']]
        logger.info(f'making {c} C matrix') 
        reimbs_matrices[c] = _matrix_maker(sub_table, participants)

    return table, reimbs_matrices

def _matrix_maker(sub_table: Table, participants: Set[str]) -> Matrix:
    # C is the cost matrix
    C = pd.DataFrame(index=participants, columns=participants)

    num_participants = len(participants)
    for (i, (creditor, credit, debtors)) in sub_table.iterrows():
        logger.info(f'{creditor} is the reimbursee with {credit} currency'
                    + ' credits')
        reimbursers = set(participants)
        if debtors is np.nan:
            # If the creditor paid for everyone, the debt is equally split
            # amongst everyone, including the creditor.
            debt = credit / num_participants
            reimbursers = set(participants) - {creditor}
        else:
            # TODO: Implement 'not' case
            # If the creditor only paid for specific participants, the debt is
            # equally split amongst them, which may or may not include the
            # creditor.
            debtor_set = set(map(str.strip, debtors.split(',')))
            debt = credit / len(debtor_set)
            reimbursers = debtor_set - {creditor}

        logger.info(f'the reimbursers are {", ".join(reimbursers)},'
                    + f' each of them owe the reimbursee {debt}')

        C.loc[creditor][reimbursers] = debt

    return C

def reduction_algorithm(C: Matrix) -> None:
    credits: pd.Series = C.sum(axis=1)
    debts: pd.Series = C.sum()
    balance = credits - debts

    C.loc[:, :] = np.nan # reset the matrix

    logger.info(f'the balance is zero: {sum(balance) == 0.0}')
    
    while balance.any():
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
                balance[debtor] += balance[creditor]
                balance[creditor] = 0.0
            else:
                logger.info(f'{debtor}\'s debt will be fully repaid by' \
                            + f' paying {creditor} {-balance[debtor]}' \
                            + ' currency credits')
                C.loc[creditor, debtor] = -balance[debtor]
                balance[creditor] += balance[debtor]
                balance[debtor] = 0.0
