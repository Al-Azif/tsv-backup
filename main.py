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
    except dropbox.exceptions.ApiError:
        return False
    except Exception:
        # I get some wierd error here every once and a while releated to
        # Dropbox's files_get_metadata()
        #
        # Error is a urllib3.exceptions.ProtocolError exception
        return False


def db_async_complete(async_id):
    """Check to see if the async succeeded"""
    return DBX.files_save_url_check_job_status(async_id).is_complete()


def db_async_failed(async_id):
    """Check to see if the async failed"""
    return DBX.files_save_url_check_job_status(async_id).is_failed()


def kickme(now=False):
    """If KICK_TICK >= KICK_MAX resart the script

    Set now to True to kick now reguardless of tick/max
    """
    if now or KICK_TICK >= KICK_MAX:
        print('\033[1m\033[91mKicking Script\033[0m...\033[0m')
        os.execv(sys.executable, ['python'] + sys.argv)
        exit()


def db_delete_duplicates(dest):
    for entry in DBX.files_list_folder(dest).entries:
        if '(' in entry.name:
            print('\033[1mDeleting Duplicate:\033[0m \033[91m' +
                  entry.name + '\033[0m...')
            DBX.files_delete_v2(os.path.join(dest, entry.name))


def main(path, dest, interval, sleep):
    """Main Method"""
    global KICK_TICK

    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            title = row['Name'] + ' (' + row['Region'] + ')'
            file_path = os.path.join(dest, row['Content ID'] + '.pkg')

            valid = bool(row['PKG direct link'] != 'MISSING'
                         and row['PKG direct link'] != 'CART ONLY'
                         and row['PKG direct link'] != ''
                         )

            if valid and not db_exists(file_path):
                aid = DBX.files_save_url(file_path, row['PKG direct link'])
                aid = aid.get_async_job_id()
                skipped = False
            else:
                skipped = True

            if skipped and valid:
                print('\033[1mSkipped Downloading:\033[0m \033[92m' +
                      title + '\033[0m')

            if skipped and not valid:
                print('\033[1mSkipped Downloading:\033[0m \033[91m' +
                      title + '\033[0m')

            if not skipped:
                print('\033[1mDownloading:\033[0m \033[93m' +
                      title + '\033[0m...')
                while not db_exists(file_path) and not db_async_complete(aid):
                    if db_async_failed(aid):
                        print('\033[1m\033[91mSave URL failed!\033[0m\033[0m')
                        kickme(now=True)
                    kickme()
                    KICK_TICK = KICK_TICK + 1
                    time.sleep(interval)
                print('\033[1mFinished Downloading:\033[0m \033[92m' +
                      title + '\033[0m')
                db_delete_duplicates(os.path.join(dest, ''))
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
