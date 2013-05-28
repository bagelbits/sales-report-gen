#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import argparse
import os
import sales_unicorn
import sales_tools.sales_SQLaccess as sales_SQLaccess
from datetime import date
from decimal import *
from monthdelta import MonthDelta


class colorz:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


###############################################################################
#                   sales_calc.py Command Line Version                          #
###############################################################################

############################################################################
#                           Check for SR                                   #
# Checks if srgen has been run on each period the report is being run for. #
############################################################################


def check_for_SR(SR_dates):
    errorFlag = False
    sales_db = sales_SQLaccess.SALES_DB_ACCESS()
    db_cursor = sales_db.db_access()

    for date in SR_dates:
        db_cursor.execute("SELECT * FROM sales \
                           WHERE sales_period = %s LIMIT 1", (date, ))
        found = db_cursor.fetchone()

        if not found:
            print "%sPlease run sales_srgen.py for the date: %s%s" \
                % (colorz.FAIL, str(date), colorz.ENDC)
            errorFlag = True
    sales_db.close_db_connection(db_cursor)

    if(errorFlag):
        sys.exit()

###############################################################################
#                             Folder Setup                                    #
# Makes required folders based on period given. Also pulls the names for the  #
# proper Sales Reports for the given period.                                  #
###############################################################################


def folderSetup(startDate, endDate):
    SR_dates = []
    absolute_file_path = "*scrubbed*"
    if(not os.path.exists('%s/reports/%s-%s/empty'
            % (absolute_file_path, startDate.strftime("%m.%Y"),
             endDate.strftime("%m.%Y")))):

        os.makedirs('%s/reports/%s-%s/empty'
            % (absolute_file_path, startDate.strftime("%m.%Y"),
               endDate.strftime("%m.%Y")))
    if(not os.path.exists('%s/reports/%s-%s/mm'
            % (absolute_file_path, startDate.strftime("%m.%Y"),
             endDate.strftime("%m.%Y")))):

        os.makedirs('%s/reports/%s-%s/mm'
            % (absolute_file_path, startDate.strftime("%m.%Y"),
               endDate.strftime("%m.%Y")))

    while(startDate < endDate):
        SR_dates.append(startDate)
        startDate = startDate + MonthDelta(1)
    SR_dates.append(endDate)

    return SR_dates


#########################################
#               Main Method             #
# Commented lines are for forcing input #
#########################################

#Constants
validArguments = False
artist_names = []
pubnames = []
reportType = None
printAllTheThings = False

#########################################
#        ARGUMENTS PROCESSING           #
#########################################

parser = argparse.ArgumentParser()

#verbose?
parser.add_argument('-v', action='store_true', default=False, dest='verbose',
    help='Verbose output?')

#reports types
parser.add_argument('-all', action='store_true', default=False,
    dest='printAllTheReports', help='Process ALL reports')

#report date range
parser.add_argument('-start', nargs=2, dest='start', help="Start date",
    metavar=('MM', 'YYYY'))
parser.add_argument('-end', nargs=2, dest='end', help="End date",
    metavar=('MM', 'YYYY'))


args = parser.parse_args()


#process report type
printAllTheThings = args.printAllTheReports
if printAllTheThings:
    print '%sReport type: all%s' % (colorz.OKBLUE, colorz.ENDC)
    reportType = 2

else:
    print "Please enter the name of the artist"
    artist_names = raw_input("[For multiple reports, delimit with a '|' ]: ")

    if "/" in artist_names:
        artist_names = artist_names.replace("/", " ")
    artist_names = artist_names.split("|")


#process date range
if args.start is None:
    if args.verbose:
        print "%sNo start date specified; enter below:%s" \
            % (colorz.WARNING, colorz.ENDC)

    startMonth = raw_input("Enter starting month: ")
    startYear = raw_input("Enter starting year: ")
    startDate = date(int(startYear), int(startMonth), 1)

else:
    startDate = date(int(args.start[1]), int(args.start[0]), 1)
    if args.verbose:
        print "%sStart date: %s%s" % (colorz.OKGREEN, startDate, colorz.ENDC)


if args.end is None:
    if args.verbose:
        print "%sNo end date specified; enter below:%s" \
            % (colorz.WARNING, colorz.ENDC)

    endMonth = raw_input("Enter ending month: ")
    endYear = raw_input("Enter ending year: ")
    endDate = date(int(endYear), int(endMonth), 1)

else:
    endDate = date(int(args.end[1]), int(args.end[0]), 1)
    if args.verbose:
        print "%sEnd date: %s%s" % (colorz.OKGREEN, endDate, colorz.ENDC)

#########################################
#               Main Method             #
#########################################
#set up folders and crap

SR_dates = folderSetup(startDate, endDate)
check_for_SR(SR_dates)

# RUN IT
unicorn = sales_unicorn.SALES_CALC()
if(args.verbose):
    print 'Starting process...'
unicorn.calc(artist_names, printAllTheThings, SR_dates)
