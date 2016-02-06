#!/usr/bin/env python

import sys
import os
import string
import time
import argparse
import re
import logging

def setupLogging(logfile):
    # --------------------------------------------------------------------------------
    # Set up logging:
    # --------------------------------------------------------------------------------
    #
    # Log using a millisecond-resolution ISO8601 date format for
    # sortability. Warning: Not timezone info will be in this stamp as
    # would be given in date --iso-8601=ns (we cannot without making
    # things a lot more complicated due to the lack of pytz module in
    # standard Python installs):
    #
    # Compare the logging output to the Linux command: date
    # --iso-8601=ns but has nanosecond granularity while asctime has
    # only millisecond granularity.
    #
    format = "%(asctime)s %(levelname)s: %(message)s"

    logging.basicConfig(filename=logfile,
                        filemode='w',
                        format=format,
                        level=logging.DEBUG)

def main():
    # Parse command-line options:
    parser = argparse.ArgumentParser(description='Converts Clipperz JSON databases to LastPass CSV files.')
    parser.add_argument("-injson", dest="injsonfile", required=True, help="Input Clipperz JSON file.")
    parser.add_argument("-outcsv", dest="outcsv", required=True, help="Output LastPass CSV file.")
    args = parser.parse_args(sys.argv[1:])

    # Setup logging:
    #logfile = os.path.join('/tmp',os.path.basename(sys.argv[0]) + ".log");
    logfile = '/dev/stdout'
    setupLogging(logfile)
    
    logging.info("Start: " + os.path.basename(sys.argv[0]))
    logging.info("Using Python version:" + re.sub(r'\n', ' ', sys.version))
    
    # Process arguments:
    injsonfile = os.path.expanduser(args.injsonfile)
    print 'injsonfile=="'+str(injsonfile)+'"'
    outcsv = os.path.expanduser(args.outcsv)
    print 'outcsv=="'+str(outcsv)+'"'
        
if __name__ == '__main__':
    main()

