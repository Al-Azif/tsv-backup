#!/usr/bin/env python
# encoding: utf-8
"""Backup the contents of a TSV file directly to Dropbox
   Source: https://github.com/Al-Azif/tsv-backup
"""

from __future__ import print_function
import csv
import argparse
import os
import sys
import time
import dropbox

with open('oauth.conf', 'rb') as oauth:
    DBX = dropbox.Dropbox(oauth.read())


def exists(path):
    """Check to see if there is a file at the given path on Dropbox"""
    try:
        DBX.files_get_metadata(path)
        return True
    except:
        return False


def main(path, dest, interval, sleep, kickme):
    """Main Method"""
    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            title = row['Name'] + ' (' + row['Region'] + ')'
            filename = row['Content ID']

            skipped = True
            if row['PKG direct link'] != 'MISSING' and row['PKG direct link'] != '' and row['PKG direct link'] != 'CART ONLY':
                if not exists(dest + filename + '.pkg'):
                    aid = DBX.files_save_url(
                        dest + filename + '.pkg',
                        row['PKG direct link']
                    )
                    skipped = False
            if skipped:
                print('Skipped Downloading: ' + title)
            else:
                print('Downloading ' + title + '...')
                kicktick = 0
                while not exists(dest + filename + '.pkg') and not DBX.files_save_url_check_job_status(aid.get_async_job_id()).is_complete():
                    if kicktick >= kickme:
                        print(os.linesep + '\x1b[1;31mKicking Script...\x1b[0m')
                        os.execv(sys.executable, ['python'] + sys.argv)
                        exit()
                    kicktick = kicktick + 1
                    time.sleep(interval)
                print('Finished Downloading ' + title)
                print('File Located at ' + dest + filename + '.pkg')
                print('Sleeping before next download...')
                time.sleep(sleep)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TSV Backup Utility')
    parser.add_argument(
        '-c', dest='path', action='store', required=True,
        help='Path to TSV File')
    parser.add_argument(
        '--destination', dest='dest', action='store', default='/tsv-backup/', required=False,
        help='Destination path to save files to on Dropbox')
    parser.add_argument(
        '--interval', dest='interval', action='store', type=int, default='60', required=False,
        help='Number of seconds to wait before checking download status')
    parser.add_argument(
        '--sleep', dest='sleep', action='store', type=int, default='300', required=False,
        help='Number of seconds to wait before starting a new download')
    parser.add_argument(
        '--kick', dest='kick', action='store', type=int, default='60', required=False,
        help='Number of intervals to wait before kicking the script')

    args = parser.parse_args()

    if not os.path.isfile(args.path):
        print('Could not locate TSV file')
        exit()

    main(args.path, args.dest, int(args.interval), int(args.sleep), int(args.kick))
