#!/usr/bin/env python
# encoding: utf-8
"""Backup the contents of a TSV file directly to Dropbox
   Source: https://github.com/Al-Azif/tsv-backup
"""

from __future__ import print_function
import argparse
import csv
import os
import sys
import time
import dropbox


with open('oauth.conf', 'rb') as oauth:
    DBX = dropbox.Dropbox(oauth.read())


def db_exists(path):
    """Check to see if there is a file at the given path on Dropbox"""
    try:
        DBX.files_get_metadata(path)
        return True
    except Exception:
        return False


def db_async_complete(async_id):
    """Check to see if the async succeeded"""
    return DBX.files_save_url_check_job_status(async_id).is_complete()


def db_async_failed(async_id):
    """Check to see if the async failed"""
    return DBX.files_save_url_check_job_status(async_id).is_failed()


def kickme():
    """If KICK_TICK >= KICK_MAX resart the script"""
    if KICK_TICK >= KICK_MAX:
        print('\033[1m\033[91mKicking Script\033[0m...\033[0m')
        os.execv(sys.executable, ['python'] + sys.argv)
        exit()


def main(path, dest, interval, sleep):
    """Main Method"""
    global KICK_TICK
    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            title = row['Name'] + ' (' + row['Region'] + ')'
            filename = row['Content ID']

            if row['PKG direct link'] != 'MISSING' \
               and row['PKG direct link'] != 'CART ONLY' \
               and row['PKG direct link'] != '':
                valid = True
            else:
                valid = False

            if valid and not db_exists(dest + filename + '.pkg'):
                aid = DBX.files_save_url(
                    dest + filename + '.pkg',
                    row['PKG direct link']
                )
                async_id = aid.get_async_job_id()
                skipped = False
            else:
                skipped = True

            if skipped:
                print('\033[1mSkipped Downloading:\033[0m \033[92m' + title + '\033[0m')

            if skipped and not valid:
                print('\033[1mSkipped Downloading:\033[0m \033[91m' + title + '\033[0m')

            if not skipped:
                print('\033[1mDownloading:\033[0m \033[93m' + title + '\033[0m...')
                while not db_exists(dest + filename + '.pkg') and not db_async_complete(async_id):
                    kickme()
                    KICK_TICK = KICK_TICK + 1
                    time.sleep(interval)
                print('\033[1mFinished Downloading:\033[0m \033[92m' + title + '\033[0m')
                print('Sleeping before next download...')
                time.sleep(sleep)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TSV Backup Utility')
    parser.add_argument(
        '-c', dest='path', action='store', required=True,
        help='Path to TSV File')
    parser.add_argument(
        '--destination', dest='dest', action='store',
        default='/tsv-backup/', required=False,
        help='Destination path to save files to on Dropbox')
    parser.add_argument(
        '--interval', dest='interval', action='store', type=int,
        default='60', required=False,
        help='Number of seconds to wait before checking download status')
    parser.add_argument(
        '--sleep', dest='sleep', action='store', type=int,
        default='300', required=False,
        help='Number of seconds to wait before starting a new download')
    parser.add_argument(
        '--kick', dest='kick', action='store', type=int,
        default='60', required=False,
        help='Number of intervals to wait before kicking the script')

    args = parser.parse_args()

    if not os.path.isfile(args.path):
        print('Could not locate TSV file')
        exit()

    KICK_MAX = args.kick
    KICK_TICK = 0

    main(args.path, args.dest, args.interval, args.sleep)
