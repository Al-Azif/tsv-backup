#!/usr/bin/env python
# encoding: utf-8
"""Backup the contents of a TSV file directly to Dropbox
   Source: https://github.com/Al-Azif/tsv-backup
"""

from __future__ import print_function
import csv
import argparse
import os
import time
import dropbox

with open('oauth.conf', 'rb') as oauth:
    DBX = dropbox.Dropbox(oauth.read())


def main(path, dest, interval, sleep):
    """Main Method"""
    with open(path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            title = row['Name'] + ' (' + row['Region'] + ')'
            filename = title + ' (' + row['Title ID'] + ')'
            header = '\t'.join(reader.fieldnames)
            bak = ''
            for field in reader.fieldnames:
                bak += row[field] + '\t'
            print('Downloading ' + title + '...')
            if not row['PKG direct link'] == 'MISSING' or not row['PKG direct link'] == '':
                aid = DBX.files_save_url(
                    dest + filename + '.pkg',
                    row['PKG direct link']
                )
                if 'zRIF' in row and not row['zRIF'] == 'MISSING':
                    DBX.files_upload(
                        row['zRIF'],
                        dest + filename + '.zrif'
                    )
                DBX.files_upload(
                    header + '\n' + bak,
                    dest + filename + '.tsv'
                )
                while not DBX.files_save_url_check_job_status(aid.get_async_job_id()).is_complete():
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

    args = parser.parse_args()

    if not os.path.isfile(args.path):
        print('Could not locate TSV file')
        exit()

    main(args.path, args.dest, int(args.interval), int(args.sleep))
