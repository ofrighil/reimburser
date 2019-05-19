import argparse

from .reimburser import Reimburser

def parse_args():
    parser = argparse.ArgumentParser(
        prog='reimburser',
        description='Calculates the reimbursements for a given trip and ' \
            'sends an email of the results to all participants.')
    parser.add_argument(
        'participants_file',
        help='A csv file of the participants',
        metavar='participants_file.csv')
    parser.add_argument(
        'costs_file',
        help='A csv file listing accumulated costs',
        metavar='costs_file.csv')
    parser.add_argument(
        '--title',
        '-t',
        help='The title of the trip',
        metavar='trip_title',
        default='Fun Trip')
    parser.add_argument(
        '--currency',
        '-c',
        help='Primary currency used during trip',
        metavar='currency',
        default='USD')

    return parser.parse_args()

if __name__ == '__main__':
    args: argparse.Namespace = parse_args()
    reimbs: Reimburser = Reimburser(
        args.participants_file,
        args.costs_file,
        args.title,
        args.currency)
    reimbs.send_emails()
