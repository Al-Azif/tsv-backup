## What is this?
This is a script that will iterate though a TSV file and download each entry to your Dropbox account directly without downloading them onto your computer first.

## Requirements
- [Python 3](https://www.python.org/downloads/) (Tested on 3.6.4)
    - Should work with Python 2 (Not going to put a lot of effort into supporting it)
    - Currently non-ASCII characters will cause this script to fail in Python 2
- This should run on Windows, OSX, and Linux

## How to download
- Download the zip [here](https://github.com/Al-Azif/tsv-backup/archive/master.zip)
- Download with Git

    `git clone https://github.com/Al-Azif/tsv-backup.git`

## How to run
1. Generate an OAuth token for your Dropbox account and place it in `oauth.conf`
2. Install Dropbox's Python SDK `pip install dropbox`
3. Run `python main.py -c file.tsv` from the command line
4. Wait...

## Contributing
You can check the [issue tracker](https://github.com/Al-Azif/tsv-backup/issues) for my to do list and/or bugs. Feel free to send a [pull request](https://github.com/Al-Azif/ps4-exploit-host/pulls) for whatever.
Be sure to report any bugs, include as much information as possible.

## Other Notes
- This isn't really ready for others to use
- The script will send the link to download then wait for the download to complete before starting the next
- There is a sleep timer in between finishing a file and downloading the next (10 Minutes) which can be modified with the `--sleep` arg
- Skips file if it already exists on Dropbox
- There is basically no error checking

## Why do you commit so many little changes, tweaks, etc?
I have no self control... it also lets people see the actual development. From barely working chicken scratch to actual code.
