from typing import Dict, List

import pandas as pd

from ._types import Matrix, Table

def _html_tagger(tag: str, attr_pair: tuple = None,
                indentation: str ='', long: bool = False):
    """Wraps a string with an html tag."""
    if attr_pair:
        beg = tag + ' {0}={1!r}'.format(*attr_pair)
    else:
        beg = tag
    end = tag

    if long:
        def wrap(string):
            return indentation + f'<{beg}>\n' \
            + string + '\n' \
            + indentation + f'</{end}>'
    else:
        def wrap(string):
            return indentation + f'<{beg}>{string}</{end}>'
    return wrap

# indentation level for html document
INDENTATION_WIDTH = ' ' * 2
LEVEL_0 = ''
LEVEL_1 = LEVEL_0.join(INDENTATION_WIDTH)
LEVEL_2 = LEVEL_1.join(INDENTATION_WIDTH)
LEVEL_3 = LEVEL_2.join(INDENTATION_WIDTH)
LEVEL_4 = LEVEL_3.join(INDENTATION_WIDTH)
LEVEL_5 = LEVEL_4.join(INDENTATION_WIDTH)

attach_tag_html = _html_tagger('html', indentation=LEVEL_0, long=True)
attach_tag_head = _html_tagger('head', indentation=LEVEL_1, long=True)
attach_tag_title = _html_tagger('title', indentation=LEVEL_2)
attach_tag_body = _html_tagger('body', indentation=LEVEL_1, long=True)
attach_tag_div = _html_tagger('div', indentation=LEVEL_2, long=True)
attach_tag_p = _html_tagger('p', indentation=LEVEL_3)
attach_tag_ul = _html_tagger('ul', indentation=LEVEL_4, long=True)
attach_tag_li = _html_tagger('li', indentation=LEVEL_5)
attach_tag_table = _html_tagger('table', indentation=LEVEL_2, long=True)
attach_tag_caption = _html_tagger('caption', indentation=LEVEL_3)
attach_tag_tbody = _html_tagger('tbody', indentation=LEVEL_3, long=True)
attach_tag_tr = _html_tagger('tr', indentation=LEVEL_4, long=True)
attach_tag_tr_rjust = _html_tagger('tr', attr_pair=('align', 'right'),
                                   indentation=LEVEL_4, long=True)
attach_tag_th = _html_tagger('th', indentation=LEVEL_5)
attach_tag_td = _html_tagger('td', indentation=LEVEL_5)

class Writer:
    def __init__(
            self,
            trip_title: str,
            table: Table,
            reimbursement_matrices: Dict[str, Matrix]):
        self.trip_title = trip_title
        self.table = table
        self.reimbursement_matrices = reimbursement_matrices

    def write_plaintext_body(self, recipient: str) -> str:
        """Write the plaintext email content for a given recipient.

        Args:
            recipient: The name of the email recipient.

        Returns:
            The email content for said recipient.
        """
        body = f'Dear {recipient},\n\n' \
            + 'You are receiving this message because you participated ' \
            + f'in {self.trip_title}.\n\n' \
            + 'I hope you had a pleasant time.\n\n' \
            + 'If you have debts to repay, please be courteous and ' \
            + 'reimburse your fellow participant(s) in a timely fashion.\n' \

        subbody: str = ''
        subbody_debt: List = list()
        subbody_credit: List = list()
        for currency, reimbs in self.reimbursement_matrices.items():
            debts = reimbs[recipient].dropna()
            credits = reimbs.loc[recipient].dropna()
            for creditor, credit in debts.iteritems():
                #creditor = creditor.rjust(self._max_name_len)
                amount = f'{credit} {currency}'.ljust(6+1+3)
                subbody_debt.append('\t' + creditor + ' | ' + amount)
            for debtor, debt in credits.iteritems():
                #debtor = debtor.rjust(self._max_name_len)
                amount = f'{debt} {currency}'.ljust(6+1+3)
                subbody_credit.append('\t' + debtor + ' | ' + amount)

        if len(subbody_debt) == 1:
            subbody += 'Please reimburse the following participant:\n' \
                + subbody_debt[0]
        elif len(subbody_debt) > 1:
            subbody += 'Please reimburse the following participants:\n' \
                + '\n'.join(subbody_debt)
        else:
            subbody += 'You do not need to reimburse anyone.'

        subbody += '\n\n'

        if len(subbody_credit) == 1:
            subbody += 'The following participant is obligated to ' \
                + 'reimburse you:\n' + subbody_credit[0]
        elif len(subbody_credit) > 1:
            subbody += 'The following participants are obligated to ' \
                + 'reimburse you:\n' + '\n'.join(subbody_credit)
        else:
            subbody += 'You do not have any outstanding reimbursements.' \

        body += '\n' + subbody

        return body

    def write_html_body(self, recipient: str) -> str:
        """Write the html email content for a given recipient.

        Args:
            recipient: The name of the email recipient.

        Returns:
            The email content for said recipient.
        """
        declaration = '<!DOCTYPE html>\n\n'
        header: str = attach_tag_head(
            attach_tag_title('reimburser')
        ) + '\n'
        preamble: str = self._write_html_preamble(recipient)

        torso: str = self._write_html_torso(recipient)

        middle: str = attach_tag_div(
            attach_tag_p('The rest of the email gives an overview '
                + f'of all the costs from {self.trip_title}:'))

        costs_table: str = self._construct_html_table(self.table)

        matrices = list()
        for currency, matrix in self.reimbursement_matrices.items():
            matrices.append(self._construct_html_matrix(
                currency, matrix))
        matrix_tables = f'\n{LEVEL_2}<br>\n'.join(matrices)


        body: str = attach_tag_body(
            preamble + '\n'
            + torso + '\n'
            + middle + '\n'
            + costs_table + f'\n{LEVEL_2}<br>\n'
            + matrix_tables)

        email_content: str = declaration \
            + attach_tag_html(
                header
                + body)

        return email_content

    def _write_html_preamble(self, recipient: str) -> str:
        """Writes the introduction to the html email content.
        
        Args:
            recipient: The name of the email recipient.

        Returns:
            The email content preamble.
        """
        preamble: str = attach_tag_p(f'Dear {recipient},') + '\n' \
            + attach_tag_p(
                'You are receiving this message because you participated '
                + f'in {self.trip_title}.') + '\n' \
            + attach_tag_p('I hope you had a pleasant time.') + '\n' \
            + attach_tag_p(
                'If you have any debts to repy, please be courteous and '
                + 'reimburse your fellow participant(s) in a timely fashion.')

        return attach_tag_div(preamble)

    def _write_html_torso(self, recipient: str) -> str:
        """Write the debt and credit information in the email content.

        Args:
            recipient: The name of the email recipient.

        Returns:
            The email content debt and credit information.
        """
        torso: str = ''
        debt_statements: List = list()
        credit_statements: List = list()
        for currency, reimbs in self.reimbursement_matrices.items():
            debts = reimbs[recipient].dropna()
            credits = reimbs.loc[recipient].dropna()
            for creditor, credit in debts.iteritems():
                debt_statements.append(
                    attach_tag_li(f'{creditor}, {credit} {currency}'))
            for debtor, debt in credits.iteritems():
                credit_statements.append(
                    attach_tag_li(f'{debtor}, {debt} {currency}'))

        if len(debt_statements) == 1:
            torso += attach_tag_p('Please reimburse the following '
                    + 'participant:') + '\n' \
                + attach_tag_ul(debt_statements[0])
        elif len(debt_statements) > 1:
            torso += attach_tag_p('Please reimburse the following '
                    + 'participants:') + '\n' \
                + attach_tag_ul('\n'.join(debt_statements))
        else:
            torso += attach_tag_p('You don\'t need to reimburse anyone.')

        torso += '\n'

        if len(credit_statements) == 1:
            torso += attach_tag_p('The following participant is obligated to '
                    + 'reimburse you:') \
                + attach_tag_ul(credit_statements[0])
        elif len(credit_statements) > 1:
            torso += attach_tag_p('The following participants are obligated '
                    + ' to reimburse you:') \
                + attach_tag_ul('\n'.join(credit_statements))
        else:
            torso += attach_tag_p('You don\'t have any outstanding '
                    + 'reimbursements.')

        return attach_tag_div(torso)

    def _construct_html_table(self, df: Table) -> str:
        """Constructs the trip cost table in HTML.

        Args:
            df: The trip cost table.

        Returns:
            The cost table as an HTML table.
        """
        string = attach_tag_tr('\n'.join(map(attach_tag_th, df.columns)))
        stringified_df = _stringify_table(df)

        for (i, row_elements) in stringified_df.iterrows():
            string += '\n' + attach_tag_tr('\n'.join(map(attach_tag_td,
                row_elements)))

        return attach_tag_table(
            attach_tag_caption(f'All Costs of {self.trip_title}')
            + '\n'
            + attach_tag_tbody(string))

    def _construct_html_matrix(self, currency: str, df: Matrix) -> str:
        """Constructs a cost matrix for the given currency.

        Args:
            currency: The currency of the cost matrix.
            df: A cost matrix.

        Returns:
            The cost matrix as an HTML table.
        """
        stringified_df = df.copy() \
                            .fillna(value=0.0) \
                            .applymap(_add_decimals)

        matrix = attach_tag_tr(
            attach_tag_th('')
            + '\n'
            + '\n'.join(map(attach_tag_th, df.columns)))

        for (i, row_elements) in stringified_df.iterrows():
            matrix += '\n' \
                + attach_tag_tr_rjust(attach_tag_th(i)
                                + '\n'
                                + '\n'.join(map(attach_tag_td, row_elements)))

        return attach_tag_table(
            attach_tag_caption('Cost Matrix for ' + currency)
            + '\n'
            + attach_tag_tbody(matrix))

def _add_decimals(num): return format(num, '.2f')

def _stringify_table(df: Table) -> pd.DataFrame:
    """Makes all relevant elements in the cost table a string.

    Args:
        df: The trip cost table.

    Returns:
        The trip cost table, a pandas DataFrame, with all elements converted to
        str.
    """
    columns = [
        'reimbursee',
        'cost',
        'currency',
        'reimbursers',
    ]

    if 'notes' in df.columns:
        columns.append('notes')

    side_reimbs = df['reimbursers'].notna()
    def add_space(string):
        return ', '.join(map(str.strip, string.split(',')))
    spaced_reimbursers = df['reimbursers'][side_reimbs].apply(add_space)

    stringified_df = df[columns].fillna(value={'reimbursers': 'everyone'})
    stringified_df.loc[side_reimbs, 'reimbursers'] = spaced_reimbursers

    stringified_df.loc[:, 'cost'] = stringified_df['cost'].apply(_add_decimals)

    return stringified_df
