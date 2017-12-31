#!/usr/bin/env python

import sys
import os
import string
import time
import argparse
import re
import logging
import json

def setupLogging(logfile, level):
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
                        level=level)

    # level=logging.DEBUG

    # Logger.setLevel() specifies the lowest-severity log message a
    # logger will handle, where debug is the lowest built-in severity
    # level and critical is the highest built-in severity. For
    # example, if the severity level is INFO, the logger will handle
    # only INFO, WARNING, ERROR, and CRITICAL messages and will ignore
    # DEBUG messages.


def die(errmsg):
    print errmsg
    sys.exit(1)


description = r"""
clipperz-to-lastpass.py -- Convert Clipperz JSON databases to LastPass CSV files

Why: Unfortunately Clipperz changed their user interface to be much
slower (apparently to accomodate Android apps) and users kept getting
timeouts when saving to the Clipperz server. LastPass did not (at this
point in time 2016-02-06) have any way to convert Clipperz JSON
formatted files into its format (CSV). So, this script fills that need.

Unfortunately, LastPass records are much more rigid than
Clipperz. Clipperz allows you to keep arbitrary key/value pairs while
LastPass does not. So this script adds all of the key value pairs into
the extra field. Therefore, some manual adjustment will be required
after conversion.
"""

def format_csv_field(value):
    value = value.replace('"','""')
    # Translate unicode single-quotes and other characters that cause python's print to croak with an error of the form:
    #
    #   UnicodeEncodeError: 'ascii' codec can't encode character u'\u2026' in position 272: ordinal not in range(128)
    #
    # This rips out the quotes completely which is not quite good enough:
    #   value = value.encode('ascii', 'ignore')
    value = value.replace(u"\u2019","'")
    value = value.replace(u"\u2013","-")
    value = value.replace(u"\u2026","...")
    value = '"' + value + '"'
    return value

def main():
    # Parse command-line options:
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

    # This:
    #
    #   parser.add_argument("-injson", dest="injsonfile", required=True, type=argparse.FileType('r'), help="Input Clipperz JSON file.")
    #
    # Gives this output:
    #
    #   Traceback (most recent call last):
    #     File "./clipperz-to-lastpass.py", line 55, in <module>
    #       main()
    #     File "./clipperz-to-lastpass.py", line 49, in main
    #       injsonfile = os.path.expanduser(args.injsonfile)
    #     File "/usr/lib/python2.7/posixpath.py", line 254, in expanduser
    #       if not path.startswith('~'):
    #   AttributeError: 'file' object has no attribute 'startswith'
    #
    # Puzzling:
    parser.add_argument("-injson", dest="injsonfile", required=True, help="Input Clipperz JSON file.")
    parser.add_argument("-outcsv", dest="outcsvfile", required=True, help="Output LastPass CSV file.")
    parser.add_argument("-debug", dest="debug", help="Show debugging output.", action="store_true")

    args = parser.parse_args(sys.argv[1:])

    # Setup logging:
    logfile = '/dev/stdout'
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    setupLogging(logfile, level)
    
    logging.debug("Start: " + os.path.basename(sys.argv[0]))
    
    # Process arguments:
    injsonfile = os.path.expanduser(args.injsonfile)
    outcsvfile = os.path.expanduser(args.outcsvfile)

    # Regular expression to match field labels to the username field:
    username_re = re.compile(r'^Username or email$|^Username$')

    entries = []
    entry = {}
    with open(injsonfile,'r') as fp:
        jsonobj = json.load(fp);
        #
        #print json.dumps(jsonobj, sort_keys=True, indent=2);
        #
        for card in jsonobj:

            # Reset new entry:
            entry = {}
            entry['extra'] = ''

            logging.debug('--------------------------------------------------------------------------------')
            logging.debug('card: ' + json.dumps(card, sort_keys=True, indent=2))
            entry['name'] = card['label']

            if 'data' in card:
                data = card['data']
                if 'notes' in data:
                    entry['extra'] = data['notes']
                    
            if 'currentVersion' in card:
                currentVersion = card['currentVersion']
                if 'fields' in currentVersion:
                    fields = currentVersion['fields']
                    for fieldkey in fields:
                        field = fields[fieldkey]
                        fieldlabel = field['label']
                        value = field['value']
                        if not(fieldlabel == "" and value == ""):
                            if field['actionType'] == 'URL':
                                if 'url' not in entry:
                                    entry['url'] = value
                            elif field['actionType'] == 'PWD':
                                if 'password' not in entry:
                                    entry['password'] = value
                            elif field['actionType'] == 'TXT':
                                if username_re.match(fieldlabel):
                                    if 'username' not in entry:
                                        entry['username'] = value

                            # No matter what, preserve all
                            # fieldlabel/value combinations in the
                            # extra field given the limitations of
                            # LastPass where you cannot have multiple
                            # key/value pairs as you can in
                            # Clipperz. E.g., there can be multiple
                            # PWD fields in a Clipperz card, but only
                            # one password field per LastPass record:
                            entry['extra'] += "\n" + fieldlabel + ": " + value
                                
            logging.debug('entry: ' + json.dumps(entry, sort_keys=True, indent=2))
            logging.debug('--------------------------------------------------------------------------------')
            entries.append(entry)

    # Write the CSV file:

    # Example for csv output that shows how the csv file looks like
    # when we exported a sample, but it doesn't match what the
    # template is:
    #
    # url,username,password,extra,name,grouping,fav
    # http://thesite1.com/,theusername1,thepassword1,"this is some notes for this entry
    # This is another line of that entry",thename1,thefolder1,0
    # http://sn,,,"This is a secure note 1 to be saved.
    # This is another line in that note. a double quote here "" bla bla",secure note 1,,0

    # Here is the template from
    # https://helpdesk.lastpass.com/importing-from-other-password-managers/#Importing+from+a+Generic+CSV+File
    # That does not explain what the "actionType" and "hostname" fields are
    # for:
    #
    # url,actionType,username,password,hostname,extra,name,grouping
    # http://sn,server,server1username,server1password,server1hostname,,Server 1,Server Group A
    # http://sn,,,,,Adt349fme,Guest wireless key,Sys Admins
    # http://community.spiceworks.com/login,,sysadmins@acme.com,spiceworkspassword,,confidential,Spiceworks Admin Login,Sys Admins
    #
    # So just leave the actionType and hostname fields to be blank:
    field_names = ['url','actionType','username','password','hostname','extra','name','grouping']

    with open(outcsvfile,'w') as outcsvfp:
        print >> outcsvfp, ",".join(field_names)
        for entry in entries:
            output_list = []
            for field_name in field_names:
                if field_name not in entry:
                    entry[field_name] = ''
                output_list.append(format_csv_field(entry[field_name]))
                # print 'field_name: ', field_name
                # print 'field_value:', format_csv_field(entry[field_name])
                # print >> outcsvfp, field_name
                # print >> outcsvfp, format_csv_field(entry[field_name])
            output = ",".join(output_list)
            print >> outcsvfp, output.encode("UTF-8")
            # print >> outcsvfp, json.dumps(output_list, sort_keys=True, indent=2)
        # print >> outcsvfp, json.dumps(entries, sort_keys=True, indent=2)

if __name__ == '__main__':
    main()
