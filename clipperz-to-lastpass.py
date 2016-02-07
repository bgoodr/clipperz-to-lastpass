#!/usr/bin/env python

import sys
import os
import string
import time
import argparse
import re
import logging
import json

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

def die(errmsg):
    print errmsg
    sys.exit(1)

def blank_entry():
    return {'url':'','username':'','password':'','extra':'','name':'','grouping':'','fav':''}

def main():
    # Parse command-line options:
    parser = argparse.ArgumentParser(description='Converts Clipperz JSON databases to LastPass CSV files.')


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
    parser.add_argument("-outcsv", dest="outcsv", required=True, help="Output LastPass CSV file.")
    args = parser.parse_args(sys.argv[1:])

    # Setup logging:
    #logfile = os.path.join('/tmp',os.path.basename(sys.argv[0]) + ".log");
    logfile = '/dev/stdout'
    setupLogging(logfile)
    
    logging.info("Start: " + os.path.basename(sys.argv[0]))
    
    # Process arguments:
    injsonfile = os.path.expanduser(args.injsonfile)
    print 'injsonfile=="'+str(injsonfile)+'"'
    outcsv = os.path.expanduser(args.outcsv)
    print 'outcsv=="'+str(outcsv)+'"'

    # print json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])

    # with open('test1.txt','w') as g:
    #     print >> g, json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])

    # with open('test1.txt','r') as fp:
    #     jsonobj = json.load(fp);
    #     # json.dumps(jsonobj, sort_keys=True);

    # print "bgdbg", jsonobj


    # Example for csv output that shows how the notes could be formatted:
    #
    # url,username,password,extra,name,grouping,fav
    # http://thesite1.com/,theusername1,thepassword1,"this is some notes for this entry
    # This is another line of that entry",thename1,thefolder1,0
    # http://sn,,,"This is a secure note 1 to be saved.
    # This is another line in that note. a double quote here "" bla bla",secure note 1,,0
    #

    # Regular expression to match field labels to the username field:
    username_re = re.compile(r'^Username or email$\|^Username$')

    entry = {}
    with open(injsonfile,'r') as fp:
        jsonobj = json.load(fp);
        #
        #print json.dumps(jsonobj, sort_keys=True, indent=2);
        #
        for card in jsonobj:

            # Reset new entry:
            entry = blank_entry()

            print '--------------------------------------------------------------------------------'
            print 'card:', json.dumps(card, sort_keys=True, indent=2)
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
                            if field['type'] == 'URL':
                                if 'url' in entry:
                                    # There is only one url entry per
                                    # LastPass record, so preserve the
                                    # subsequent URLs into the extra field:
                                    entry['extra'] += "\n" + fieldlabel + ": " + value
                                else:
                                    entry['url'] = value
                            elif field['type'] == 'PWD':
                                if 'password' in entry:
                                    # There is only one password entry
                                    # per LastPass record, so preserve
                                    # the subsequent passwords into
                                    # the extra field:
                                    entry['extra'] += "\n" + fieldlabel + ": " + value
                                else:
                                    entry['password'] = value
                            elif field['type'] == 'TXT':
                                if username_re.match(fieldlabel):
                                    if username in entry:
                                        # There is only one username entry
                                        # per LastPass record, so preserve
                                        # the subsequent usernames into
                                        # the extra field:
                                        entry['extra'] += "\n" + fieldlabel + ": " + value
                                    else:
                                        entry['username'] = value
                                
            print 'entry:', json.dumps(entry, sort_keys=True, indent=2)
            print '--------------------------------------------------------------------------------'
    
    # with open(injson,'r') as f:
    # with open('test1.txt','w') as g: 
    #     for x in f:
    #         x = x.rstrip()
    #         if not x: continue
    #         print >> g, int(x, 16)


    #     json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    # '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    # >>> print json.dumps("\"foo\bar")
    # "\"foo\bar"
    # >>> print json.dumps(u'\u1234')
    # "\u1234"
    # >>> print json.dumps('\\')
    # "\\"
    # >>> print json.dumps({"c": 0, "b": 0, "a": 0}, sort_keys=True)
    # {"a": 0, "b": 0, "c": 0}
    # >>> from StringIO import StringIO
    # >>> io = StringIO()
    # >>> json.dump(['streaming API'], io)
    # >>> io.getvalue()
    # '["streaming API"]'

if __name__ == '__main__':
    main()

