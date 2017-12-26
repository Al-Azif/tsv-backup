#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backup the contents of a TSV file directly to Dropbox
   Source: https://github.com/Al-Azif/tsv-backup
"""

from __future__ import print_function

import argparse
import csv
import codecs
from io import StringIO
import os
import sys
import time
import urllib3

import certifi
import dropbox


with codecs.open('oauth.conf', 'r', encoding='utf-8') as oauth:
    DBX = dropbox.Dropbox(oauth.read())


def clear_line():
    """Clear last printed line"""
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')


def db_exists(path):
    """Check to see if there is a file at the given path on Dropbox"""
    try:
        DBX.files_get_metadata(path)
        return True
    except dropbox.exceptions.ApiError:
        return False
    except dropbox.exceptions.RateLimitError:
        print('\033[1m\033[91mHit Dropbox rate limit, sleeping...\033[0m')
        # Need to figure out how long it takes their rate limiting to reset
        time.sleep(600)
        return False
    except urllib3.exceptions.ProtocolError:
        return False


def db_async_complete(async_id):
    """Check to see if the async succeeded"""
    return DBX.files_save_url_check_job_status(async_id).is_complete()


def db_async_failed(async_id):
    """Check to see if the async failed"""
    return DBX.files_save_url_check_job_status(async_id).is_failed()


def kickme():
    """Resart the script with the same args"""
    print('\033[1m\033[91mKicking Script...\033[0m')
    os.execv(sys.executable, [sys.executable] + sys.argv)
    exit()


def db_delete_duplicates(dest):
    """Delete duplicate files in the destination folder"""
    for entry in DBX.files_list_folder(dest).entries:
        if '(' in entry.name:
            print('\033[1mDeleting Duplicate:\033[0m   \033[91m' +
                  entry.name + '\033[0m')
            DBX.files_delete_v2(os.path.join(dest, entry.name))


def download(data, dest, sleep, kick):
    """Where the magic happens"""
    reader = csv.DictReader(StringIO(data), delimiter='\t')
    for row in reader:
        title = row['Name'] + ' (' + row['Region'] + ')'
        file_path = os.path.join(dest, row['Content ID'] + '.pkg')

        demo = bool('(DEMO/TRIAL)' in row['Name'])
        valid = bool(row['PKG direct link'] != 'MISSING'
                     and row['PKG direct link'] != 'CART ONLY'
                     and row['PKG direct link'] != ''
                     and not demo)

        if valid and not db_exists(file_path):
            aid = DBX.files_save_url(file_path, row['PKG direct link'])
            aid = aid.get_async_job_id()
            skipped = False
        else:
            skipped = True

        if skipped and valid:
            print('\033[1mSkipped Downloading:\033[0m  \033[94m' +
                  title + '\033[0m')

        if skipped and not valid and not demo:
            print('\033[1mMissing PKG Link:\033[0m     \033[91m' +
                  title + '\033[0m')

        if demo:
            print('\033[1mSkipped Demo:\033[0m         \033[91m' +
                  title + '\033[0m')

        if not skipped:
            print('\033[1mDownloading:\033[0m          \033[93m' +
                  title + '\033[0m')
            kick = time.time() + kick
            while not db_exists(file_path) or not db_async_complete(aid):
                if db_async_failed(aid):
                    print('\033[1m\033[91mSave URL failed!\033[0m')
                    kickme()
                if time.time() >= kick:
                    kickme()
            print('\033[1mFinished Downloading:\033[0m \033[92m' +
                  title + '\033[0m')
            db_delete_duplicates(os.path.join(dest, ''))
            print('Sleeping before next download...')
            time.sleep(sleep)
            clear_line()


def main():
    """Main Method"""
    parser = argparse.ArgumentParser(description='TSV Backup Utility')
    parser.add_argument(
        '--file', dest='path', action='store', default='', required=False,
        help='Path to TSV File')
    parser.add_argument(
        '--npsn', action='store_true', required=False,
        help='Run PSV_GAMES.tsv directly')
    parser.add_argument(
        '--destination', dest='dest', action='store',
        default='/tsv-backup/', required=False,
        help='Destination path to save files to on Dropbox')
    parser.add_argument(
        '--sleep', dest='sleep', action='store', type=int,
        default='10', required=False,
        help='Number of minutes to wait before starting a new download')
    parser.add_argument(
        '--kick', dest='kick', action='store', type=int,
        default='60', required=False,
        help='Number minutes to wait before kicking the script')

    args = parser.parse_args()

    if bool(not args.path and not args.npsn) or bool(args.path and args.npsn):
        print('Please specify either a file or npsn')
        exit()

    if args.path and not os.path.isfile(args.path):
        print('Could not locate TSV file')
        exit()

    if args.path:
        with codecs.open(args.path, 'r', encoding='utf-8') as tsvfile:
            data = tsvfile.read()
    elif args.npsn:
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
        response = http.request(
            'GET',
            'https://nopaystation.com/tsv/PSV_GAMES.tsv')
        if response.status == 200:
            data = response.data.decode('utf-8')
        else:
            print('Error retrieving NPSN data')
            exit()

    download(data, args.dest, args.sleep * 60, args.kick * 60)
    db_delete_duplicates(os.path.join(args.dest, ''))


if __name__ == '__main__':
    main()
