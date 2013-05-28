#!/usr/bin/env python
# -*- coding: utf8 -*-

import re
import csv
import sys
import os
import glob
import math
import sales_tools.sales_SQLaccess as sales_SQLaccess
import argparse
from datetime import date
from monthdelta import MonthDelta
from decimal import Decimal

################################################
#              Data Calculator                 #
# Used to pass processed data to the SR tables #
################################################


def dataCalculator(territory, gross_income, quantity):
    #Transfer strings to integers for ease
    quantity = float(quantity)
    downloads = 0
    unit_sales = 0
    streams = 0

    if quantity:
        ratio = math.fabs(Decimal(gross_income) / Decimal(quantity))
    else:
        ratio = 0

    if (ratio < .1):
        streams = quantity
    else:
        downloads = quantity
        if territory == "US" or territory == "MX":
            unit_sales = quantity
    data = {'gross_sales': gross_income, 'unit_sales': unit_sales,
            'streams': streams, 'downloads': downloads}
    return data

##############################
# TopSpin Data Miner for SR  #
##############################


def TopSpinDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    UPC = sales_db.id_override(db_cursor, line[31].strip())
    ISRC = sales_db.id_override(db_cursor, line[32].strip())

    if not UPC and not ISRC:
        errorReport.append("Error: TopSpin entry Missing UPC and ISRC: %s\n" % line)
        if not args.force_gen:
            print "\nError: TopSpin entry Missing UPC and ISRC: %s" % line
        return ""

    sales_date = line[6].split('-')
    quantity = line[15]
    storeFee = float(line[16]) - float(line[21])
    beforeTax = float(line[16]) * int(quantity)
    afterTax = float(line[21])
    gross_income = afterTax * float(line[14])

    report = []
    report.append("\"%s\",\"%s\",\"%s\"," % (line[27], UPC, ISRC))
    report.append("\"TopSpin\",\"US\",\"%s\"," % line[50])
    report.append("\"%s\",\"%s\",\"Sale\","
        % (sales_date[1].zfill(2), sales_date[0]))
    report.append("\"%s\",\"%s\",\"%s\"," % (quantity, line[16], line[21]))
    report.append("\"%s\",\"%s\"," % (storeFee, beforeTax))
    report.append("\"0.00%%\",\"%s\",\"%s\"," % (afterTax, line[14]))
    report.append("\"%s\",\"%s\",\"\"," % (gross_income, line[0]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[26], line[4], line[53]))
    report.append("\"%s\",\"\",\"\",\"%s\"\n" % (line[61], line[8]))
    report = "".join(report)

    # Checks if UPC or ISRC exits. Non-existing
    # ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator("US", gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

########################################
# BundleDragon Sales Data Miner for SR #
########################################


def BundleDragonDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args
    month = str(sales_period.month).zfill(2)
    year = str(sales_period.year)

    UPC = sales_db.id_override(db_cursor, line[0].strip())
    ISRC = ""
    if not UPC and not ISRC:
        errorReport.append(
            "Error: BundleDragon Sales entry Missing UPC and ISRC: %s\n" % line)
        if not args.force_gen:
            print "\nError: BundleDragon Sales entry Missing UPC and ISRC: %s" % line
        return ""

    territory = "US"
    quantity = line[2]
    gross_income = line[6]
    price = str(float(line[3]) / float(line[2]))
    store_fee = str((float(line[4]) + float(line[5])) / float(line[2]))
    share = str(float(price) - float(store_fee))

    report = []
    report.append("\"Album\",\"%s\",\"%s\"," % (UPC, ISRC))
    report.append("\"BundleDragon\",\"%s\",\"BundleDragon Store\"," % territory)
    report.append("\"%s\",\"%s\",\"Sale\"," % (month, year))
    report.append("\"%s\",\"%s\",\"%s\"," % (quantity, price, share))
    report.append("\"%s\",\"%s\",\"0\"," % (store_fee, gross_income))
    report.append("\"%s\",\"1\",\"%s\"," % (gross_income, gross_income))
    report.append("\"\",\"\",\"%s\"," % line[1])
    report.append("\"\",\"US\",\"Album Bundle\",")
    report.append("\"\",\"\",\"USD\"\n")
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator(territory, gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

##################################
# Direct Sales Data Miner for SR #
##################################


def DirectDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    UPC = sales_db.id_override(db_cursor, line[1].strip())
    ISRC = sales_db.id_override(db_cursor, line[2].strip())
    if not UPC and not ISRC:
        errorReport.append("Error: Direct Sales entry Missing UPC and ISRC: %s\n" % line)
        if not args.force_gen:
            print "\nError: Direct Sales entry Missing UPC and ISRC: %s" % line
        return ""

    quantity = line[9]
    gross_income = line[17]

    report = []
    report.append("\"%s\",\"%s\",\"%s\"," % (line[0], UPC, ISRC))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[3], line[4], line[5]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[6], line[7], line[8]))
    report.append("\"%s\",\"%s\",\"%s\"," % (quantity, line[10], line[11]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[12], line[13], line[14]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[15], line[16], gross_income))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[18], line[19], line[20]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[21], line[22], line[23]))
    report.append("\"%s\",\"%s\",\"%s\"\n" % (line[24], line[25], line[26]))
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator(line[4], gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

###########################
# MATCH Data Miner for SR #
###########################


def matchDataMiner(line, sales_period, match_convert):
    global errorReport
    global db_cursor
    global sales_db
    global args
    month = str(sales_period.month).zfill(2)
    year = str(sales_period.year)
    line = [x.strip("\n") for x in line]
    base_file_path = '*scrubbed*'

    UPC = sales_db.id_override(db_cursor, line[2].strip())
    ISRC = sales_db.id_override(db_cursor, line[3].strip())

    if not UPC and not ISRC:
        return ""
    if UPC and ISRC:
        UPC = ''

    if not line[5]:
        errorReport.append("ERROR: Quantity is blank on entry: %s\n" % line)
        if not args.force_gen:
            print "\nERROR: Quantity is blank on entry: %s" % line

    iTune_Codes = csv.reader(open('%s/iTunes/itunes_codes.csv' % base_file_path, 'rU'),
                             delimiter=",", quotechar='"')
    for code in iTune_Codes:
        if code != []:
            if line[15] == code[0]:
                product_type = code[1]
                detail_product_type = code[2]
                break

    if int(month) - 1 < 1:
        FX_name = '%s/iTunes/FX/%s%s_FX.txt' \
            % (base_file_path, int(year) - 1, str(12 + int(month) - 1).zfill(2))
    else:
        FX_name = '%s/iTunes/FX/%s%s_FX.txt' \
            % (base_file_path, year, str(int(month) - 1).zfill(2))

    FX_txt = csv.reader(open(FX_name, 'rU'), delimiter="\t", quotechar='"')
    for FX_line in FX_txt:
        FX_line = [x.strip(' ') for x in FX_line]
        if line[8] == FX_line[0]:
            withholdTax = math.fabs(float(FX_line[4].replace(",", "")) / float(FX_line[3].replace(",", "")))
            FX_rate = FX_line[8]
            break

    sales_date = line[1].split("/")
    quantity = line[5]
    storeFee = "0.00"
    beforeIncome = float(quantity) * float(match_convert)
    afterIncome = beforeIncome - beforeIncome * withholdTax
    gross_income = afterIncome * float(FX_rate)

    report = []
    report.append("\"%s\",\"%s\",\"%s\"," % (product_type, UPC, ISRC))
    report.append("\"iTunes Match\",\"%s\"," % line[8][0:2])
    report.append("\"iTunes %s\",\"%s\"," % (line[8][0:2], sales_date[0]))
    report.append("\"%s\",\"Sale\",\"%s\",\"0.00\"," % (sales_date[2], quantity))
    report.append("\"%s\",\"%s\"," % (match_convert, storeFee))
    report.append("\"%s\",\"%s%%\"," % (beforeIncome, withholdTax * 100))
    report.append("\"%s\",\"%s\"," % (afterIncome, FX_rate))
    report.append("\"%s\",\"%s\"," % (gross_income, line[10]))
    report.append("\"%s\",\"%s\"," % (line[11], line[12].replace('"', "")))
    report.append("\"%s\",\"%s\"," % (line[13], line[17]))
    report.append("\"%s\",\"%s\"," % (detail_product_type, line[19]))
    report.append("\"%s\",\"%s\"\n" % (line[21], line[8]))
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator(line[8][0:2], gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

##############################
# TuneCore Data Miner for SR #
##############################


def TuneCoreDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    UPC = sales_db.id_override(db_cursor, line[9].strip())
    ISRC = sales_db.id_override(db_cursor, line[11].strip())

    if not UPC and not ISRC:
        errorReport.append("Error: TuneCore entry Missing UPC and ISRC: %s\n" % line)
        if not args.force_gen:
            print "\nError: TuneCore entry Missing UPC and ISRC: %s" % line
        return ""
    if UPC and ISRC:
        UPC = ''

    sales_date = line[0].split('-')
    quantity = line[14]
    storeFee = "0.00"
    beforeTax = float(line[15]) * int(quantity)
    afterTax = float(line[16])
    gross_income = line[19]

    if not line[18]:
        FX_rate = "1"
    else:
        FX_rate = line[18]

    if not line[7]:
        title = line[6]
    else:
        title = line[7]

    report = []
    report.append("\"%s\",\"%s\",\"%s\",\"TuneCore\"," % (line[5], UPC, ISRC))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[3], line[2], sales_date[1].zfill(2)))
    report.append("\"%s\",\"Sale\",\"%s\",\"%s\"," % (sales_date[0], quantity, line[15]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[15], storeFee, beforeTax))
    report.append("\"0.00%%\",\"%s\",\"%s\"," % (afterTax, FX_rate))
    report.append("\"%s\",\"\",\"%s\",\"%s\"," % (gross_income, line[4], title))
    report.append("\"%s\",\"%s\",\"%s\",\"\"," % (line[8], line[3], line[13]))
    report.append("\"%s\",\"%s\"\n" % (line[17], line[20]))
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator(line[3][0:2], gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

##############################
#  PayPal Data Miner for SR  #
##############################


def PayPalDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    if not line[19].strip() or not line[18].strip():
        return ""
    if line[5].strip() == "Pending":
        return ""
    if abs(float("".join(line[8].split(",")))) < 0.1:
        return ""

    UPC = sales_db.id_override(db_cursor, line[19].strip())
    ISRC = ""

    sales_date = line[0].split("/")

    if line[44] == "Credit":
        status = "Sale"
    else:
        status = "Return"

    if line[44] == "Credit":
        quantity = "1"
    else:
        quantity = "-1"

    storeFee = line[9]
    beforeTax = float(line[10]) * int(quantity)
    afterTax = float(line[10])
    FX_rate = "1"
    gross_income = line[10]

    title = line[18]

    report = []
    report.append("\"Album\",\"%s\",\"%s\",\"PayPal\",\"US\"," % (UPC, ISRC))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[3], sales_date[0].zfill(2), sales_date[2]))
    report.append("\"%s\",\"%s\",\"%s\"," % (status, quantity, line[8]))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[10], storeFee, beforeTax))
    report.append("\"0.00%%\",\"%s\",\"%s\"," % (afterTax, FX_rate))
    report.append("\"%s\",\"%s\",\"\",\"%s\"," % (gross_income, line[14], title))
    report.append("\"\",\"%s\",\"Download\",\"\",\"\",\"%s\"\n" % (line[42], line[7]))
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator("US", gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

##########################
# IRIS Data Miner for SR #
##########################


def IRISDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    if not line[4].strip() and not line[7].strip():
        return ""
    if line[14] == '':
        errorReport.append("ERROR: Quantity is blank on entry: %s\n" % line)
        if not args.force_gen:
            print "\nERROR: Quantity is blank on entry: %s" % line

    UPC = ""
    ISRC = ""
    sales_date = line[23].split("-")

    quantity = line[14]
    if line[13].lower() == "return":
        quantity = str(float(line[14]) * -1)

    share = float(line[15]) - float(line[15]) * float(line[19])
    gross_income = str(float(quantity) * share)

    report = []
    report.append("\"%s\"," % line[9])
    if line[9] == "ALBUM":
        UPC = sales_db.id_override(db_cursor, line[4].strip())
        report.append("\"%s\",\"\"," % UPC)

    if line[9] == "TRACK":
        ISRC = sales_db.id_override(db_cursor, line[7].strip())
        report.append("\"\",\"%s\"," % ISRC)

    report.append("\"IRIS\",\"US\",\"%s\",\"%s\"," % (line[1], sales_date[1]))
    report.append("\"%s\",\"%s\",\"%s\"," % (sales_date[0], line[13], quantity))
    report.append("\"%s\",\"%s\"," % (line[15], share))
    report.append("\"%s\"," % (float(line[15]) - share,))
    report.append("\"%s\",\"0%%\"," % (float(quantity) * share,))
    report.append("\"%s\",\"1.00000\"," % (float(quantity) * share,))
    report.append("\"%s\",\"%s\"," % (gross_income, line[0]))
    if UPC:
        report.append("\"%s\",\"%s\"," % (line[5], line[3]))
    if ISRC:
        report.append("\"%s\",\"%s\"," % (line[8], line[6].replace("\"", "")))
    report.append("\"%s\",\"%s\",\"%s\"," % (line[2], line[27], line[12]))
    report.append("\"\",\"\",\"USD\"\n")
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator("US", gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

############################
# iTunes Data Miner for SR #
############################


def itunesDataMiner(line, sales_period):
    global errorReport
    global db_cursor
    global sales_db
    global args

    base_file_path = '*scrubbed*'

    month = str(sales_period.month).zfill(2)
    year = str(sales_period.year)
    line = [x.strip("\n") for x in line]

    UPC = sales_db.id_override(db_cursor, line[2].strip())
    ISRC = sales_db.id_override(db_cursor, line[3].strip())
    if not UPC and not ISRC:
        return ""
    if UPC and ISRC:
        UPC = ''
    if line[5] == '':
        errorReport.append("ERROR: Quantity is blank on entry: %s\n" % line)
        if not args.force_gen:
            print "\nERROR: Quantity is blank on entry: %s" % line

    iTune_Codes = csv.reader(open('%s/iTunes/itunes_codes.csv' % base_file_path, 'rU'),
                             delimiter=",", quotechar='"')
    for code in iTune_Codes:
        if code != []:
            if line[15] == code[0]:
                product_type = code[1]
                detail_product_type = code[2]
                break

    if int(month) - 1 < 1:
        FX_name = '%s/iTunes/FX/%s%s_FX.txt' \
            % (base_file_path, int(year) - 1, str(12 + int(month) - 1).zfill(2))
    else:
        FX_name = '%s/iTunes/FX/%s%s_FX.txt' \
            % (base_file_path, year, str(int(month) - 1).zfill(2))

    FX_txt = csv.reader(open(FX_name, 'rU'), delimiter="\t", quotechar='"')
    for FX_line in FX_txt:
        FX_line = [x.strip(' ') for x in FX_line]
        if line[8] == FX_line[0]:
            withholdTax = math.fabs(float(FX_line[4].replace(",", "")) / float(FX_line[3].replace(",", "")))
            FX_rate = FX_line[8]
            break

    sales_date = line[1].split("/")
    quantity = line[5]
    beforeIncome = float(quantity) * float(line[6])
    afterIncome = beforeIncome - beforeIncome * withholdTax
    gross_income = afterIncome * float(FX_rate)

    report = []
    report.append("\"%s\",\"%s\",\"%s\"," % (product_type, UPC, ISRC))
    report.append("\"iTunes\",\"%s\"," % line[8][0:2])
    report.append("\"iTunes %s\",\"%s\"," % (line[8][0:2], sales_date[0]))
    report.append("\"%s\"," % sales_date[2])
    if line[9] == 'S':
        report.append("\"Sale\",")
        storeFee = float(line[20]) - float(line[6])
    if line[9] == 'R':
        storeFee = float(line[20]) + float(line[6])
        report.append("\"Return\",")
    report.append("\"%s\",\"%s\",\"%s\"," % (quantity, line[20], line[6]))
    report.append("\"%s\",\"%s\"," % (storeFee, beforeIncome))
    report.append("\"%s\",\"%s\"," % (withholdTax * 100, afterIncome))
    report.append("\"%s\",\"%s\",\"%s\"," % (FX_rate, gross_income, line[10]))
    report.append("\"%s\",\"%s\"," % (line[11], line[12].replace('"', "")))
    report.append("\"%s\",\"%s\"," % (line[13], line[17]))
    report.append("\"%s\",\"%s\"," % (detail_product_type, line[19]))
    report.append("\"%s\",\"%s\"\n" % (line[21], line[8]))
    report = "".join(report)

    #Checks if UPC or ISRC exits. Non-existing ones are printed to the error file.
    if not sales_db.upc_isrc_checker(db_cursor, UPC, ISRC):
        errorReport.append("ERROR: ISRC/UPC doesn't exist: %s\n" % report)
        if not args.force_gen:
            print "\nERROR: ISRC/UPC doesn't exist: %s" % report
        return ""
    else:
        data = dataCalculator(line[8][0:2], gross_income, quantity)
        if UPC:
            sales_db.sr_data_inserter(db_cursor, sales_period, UPC, data)
        else:
            sales_db.sr_data_inserter(db_cursor, sales_period, ISRC, data)
    return report

###################################################
#            Match Conversion Miner               #
# Grabs the conversion table in a particular file #
###################################################


def matchConversionMiner(filename):
    match_csv = csv.reader(open(filename, 'rU'), delimiter="\t", quotechar='"')
    convert_table = {}
    temp_data = []
    for line in match_csv:
        if len(line) == 12:
            temp_data.append(line)
    for line in temp_data:
        if len(line[0]) == 2:
            convert_table[line[0]] = float(line[5])
    return convert_table

###################################
#          File Processor         #
# Grabs appropriate import files #
###################################


def fileProcessor(month, year):
    global IRISFiles
    global iTunesFiles
    global TopSpinFiles
    global TuneCoreFiles
    global BundleDragonFiles
    global DirectFiles
    global PayPalFiles
    global matchFiles
    global months

    base_file_path = '*scrubbed*'

    BundleDragonDate = year + '_' + month
    DirectDate = year + '_' + month
    PayPalDate = month + year
    if int(month) - 2 < 1:
        IRISdate = '-' + str(int(year) - 1) + '_' \
            + str(12 + int(month) - 2).zfill(2)
        TuneCoreDate = str(12 + int(month) - 2).zfill(2) + '-' \
            + str(int(year) - 1)
    else:
        IRISdate = '-' + year + '_' + str(int(month) - 2).zfill(2)
        TuneCoreDate = str(int(month) - 2).zfill(2) + '-' + year

    if int(month) - 1 < 1:
        iTunesDate = str(12 + int(month) - 1).zfill(2) + str(int(year) - 1)[2:4]
        matchDate = str(12 + int(month) - 1).zfill(2) + str(int(year) - 1)[2:4]
        TopSpinDate = months[str(12 + int(month) - 1).zfill(2)] + '-' \
            + str(int(year) - 1)
    else:
        iTunesDate = str(int(month) - 1).zfill(2) + year[2:4]
        matchDate = str(int(month) - 1).zfill(2) + year[2:4]
        TopSpinDate = months[str(int(month) - 1).zfill(2)] + '-' + year

    IRISFiles = glob.glob('%s/IRIS/RAW Report *_%s%s*.csv' % (base_file_path, IRISdate, IRISdate))
    iTunesFiles = glob.glob('%s/iTunes/Sales/*_%s_[a-zA-Z][a-zA-Z].txt' % (base_file_path, iTunesDate))
    matchFiles = glob.glob('%s/iTunes/Match/C_*_%s_[a-zA-Z][a-zA-Z].txt' % (base_file_path, matchDate))
    TopSpinFiles = glob.glob('%s/TopSpin/* (16125) %s - Shipped Sales Detail.csv' % (base_file_path, TopSpinDate))
    TuneCoreFiles = glob.glob('%s/TuneCore/tunecore-musicsales-sales_period-%s.csv' % (base_file_path, TuneCoreDate))
    BundleDragonFiles = glob.glob('%s/BundleDragon/BundleDragon_%s.csv' % (base_file_path, BundleDragonDate))
    DirectFiles = glob.glob('%s/Direct/Direct_%s.csv' % (base_file_path, DirectDate))
    PayPalFiles = glob.glob('%s/PayPal/DHR_%s.CSV' % (base_file_path, PayPalDate))

############################
# Initializes the SR setup #
############################


def getDateRange(args):
    dateRange = []
    while True:
        if args.start:
            startMonth = args.start[0]
        else:
            startMonth = raw_input("Enter starting month: ")
            startMonth = startMonth.zfill(2)
            #startMonth = "07"
        if not re.search("^\d\d$", startMonth):
            if args.start:
                    del args.start[:]
            if re.search("^00\d$", startMonth):
                print "You seem to have entered a secret agent rather than a month..."
                continue
            print "That's not a valid month, please enter again. (e.g. 01 or 6)"
            continue
        break
    while True:
        if args.start:
            startYear = args.start[1]
        else:
            startYear = raw_input("Enter starting year: ")
            #startYear = "2009"
        if not re.search("^\d\d\d\d$", startYear):
            if args.start:
                    del args.start[:]
            print "That's not a valid year, please enter again. (e.g. 1998)"
            continue
        break
    while True:
        if args.end:
            endMonth = args.end[0]
        else:
            endMonth = raw_input("Enter end month: ")
            endMonth = endMonth.zfill(2)
            #endMonth = "11"
        if not re.search("^\d\d$", endMonth):
            if args.end:
                del args.end[:]
            if re.search("^00\d$", endMonth):
                print "You seem to have entered a secret agent rather than a month..."
                continue
            print "That's not a valid month, please enter again. (e.g. 01 or 6)"
            continue
        break
    while True:
        if args.end:
            endYear = args.end[1]
        else:
            endYear = raw_input("Enter end year: ")
            #endYear = "2012"
        if not re.search("^\d\d\d\d$", endYear):
            if args.end:
                del args.end[:]
            print "That's not a valid year, please enter again. (e.g. 1998)"
            continue
        break
    #Generate Date range
    startDate = date(int(startYear), int(startMonth), 1)
    endDate = date(int(endYear), int(endMonth), 1)
    while(startDate < endDate):
        dateRange.append(startDate)
        startDate = startDate + MonthDelta(1)
    dateRange.append(endDate)
    return dateRange


def SRsetup(month, year):
    #Generate filename off month and year
    absolute_file_path = "*scrubbed*"
    SRFilename = '%s/sales/%s/salesfile_%s_%s.csv' % (absolute_file_path, year, month, year)
    global args
    if not args.force_gen:
        if os.path.exists(SRFilename):
            answer = raw_input("This sales report already exists, overwrite? (y/n): ")
            answer = answer.lower()
            if not(answer == 'y' or answer == 'yes' or answer == 'ye'):
                sys.exit()
    if not os.path.exists('%s/sales/%s' % (absolute_file_path, year)):
        os.makedirs('%s/sales/%s' % (absolute_file_path, year))
    if not os.path.exists('%s/sales/error' % absolute_file_path):
        os.makedirs('%s/sales/error' % absolute_file_path)
    fileProcessor(month, year)
    return SRFilename


#############
# MAIN LOOP #
#############
IRISFiles = []
iTunesFiles = []
TopSpinFiles = []
TuneCoreFiles = []
BundleDragonFiles = []
DirectFiles = []
PayPalFiles = []
itunesData = []
IRISData = []
matchFiles = []
shitDoneBroke = False
months = dict({'01': "Jan", '02': "Feb", '03': "Mar", '04': "Apr", '05': "May",
    '06': "Jun", "07": 'Jul', "08": 'Aug', "09": 'Sep', "10": 'Oct',
    "11": 'Nov', "12": 'Dec'})

#Check for forced generation request
parser = argparse.ArgumentParser()
parser.add_argument('-f', '-force', action='store_true', default=False,
    dest='force_gen', help='Force generation and skip error messages.')
parser.add_argument('-start', nargs=2, dest='start', help="Start date", metavar=('MM', 'YYYY'))
parser.add_argument('-end', nargs=2, dest='end', help="End date", metavar=('MM', 'YYYY'))
args = parser.parse_args()
if args.start:
    args.start[0] = args.start[0].zfill(2)
if args.end:
    args.end[0] = args.end[0].zfill(2)

sales_db = sales_SQLaccess.sales_db_ACCESS()
db_cursor = sales_db.db_access()

dateRange = getDateRange(args)

for sales_period in dateRange:
    warningReport = []
    errorReport = []
    month = str(sales_period.month).zfill(2)
    year = str(sales_period.year)
    SRFilename = SRsetup(month, year)
    if not IRISFiles or not iTunesFiles or not TopSpinFiles or not TuneCoreFiles \
            or not BundleDragonFiles or not DirectFiles or not PayPalFiles or not matchFiles:
        warning = []
        warning.append("Warning: %s-%s: Missing some or all of the proper input files:\n" % (month, year))
        if not IRISFiles:
            warning.append("IRIS\n")
        if not iTunesFiles:
            warning.append("iTunes\n")
        if not TopSpinFiles:
            warning.append("TopSpin\n")
        if not TuneCoreFiles:
            warning.append("TuneCore\n")
        if not BundleDragonFiles:
            warning.append("BundleDragon\n")
        if not DirectFiles:
            warning.append("Direct Sales\n")
        if not PayPalFiles:
            warning.append("PayPal\n")
        if not matchFiles:
            warning.append("iTunes Match\n")

        warning = "".join(warning)
        if not args.force_gen:
            print warning
            answer = raw_input("Continue? (y/n): ")
            answer = answer.lower()
            if not re.match(answer, 'yes'):
                sys.exit()
        warningReport.append(warning)
    SRFile = open(SRFilename, 'w')
    os.chmod(SRFilename, 666)

    #Database setup script
    print "\nSetting up sales table for period: %s-%s" % (month, year)
    sales_db.SR_init(db_cursor, sales_period)
    sales_db.commit_to_db()

    SRFile.write('"Product Type","UPC","ISRC","Aggregator","Territory","Store",'
        + '"Sales Month","Sales Year","Sales or Return","Quantity","Price",'
        + '"Share","Store Fee","Before-Tax Income","Withholding Tax Percentage",'
        + '"After-Tax Income","FX Rate","Gross Income","Aggregator Identifier",'
        + '"Artist","Title","Label","Country of Sale","Detailed Product Type",'
        + '"Promo Code","Customer Currency","Sale Currency"\n')

    print "Commencing data miner..."

    #IRISFiles=[]
    #iTunesFiles=[]
    #TopSpinFiles=[]
    #TuneCoreFiles=[]
    #DirectFiles=[]
    #BundleDragonFiles=[]
    #PayPalFiles=[]
    #matchFiles=[]

    #IRIS Data Mining
    if IRISFiles:
        IRIS_csv = csv.reader(open(IRISFiles[0], 'rU'), delimiter=",", quotechar='"')
        IRIS_csv.next()
        IRIS_csv = list(IRIS_csv)
        line_count = 0
        for line in IRIS_csv:
            line_count += 1
            per = line_count / float(len(IRIS_csv)) * 100
            sys.stdout.write("\rIRIS %d%%" % per)
            sys.stdout.flush()
            SRFile.write(IRISDataMiner(line, sales_period))
        print " COMPLETE!"

    #iTunes Data Mining
    if iTunesFiles:
        for filename in iTunesFiles:
            iTunes_csv = csv.reader(open(filename, 'rU'), delimiter="\t", quotechar='"')
            iTunes_csv.next()
            country = filename[filename.rfind("_") + 1:filename.find(".")]
            iTunes_csv = list(iTunes_csv)
            line_count = 0
            for line in iTunes_csv:
                if len(line) < 4:
                    continue
                line_count += 1
                per = int(line_count / float(len(iTunes_csv)) * 100)
                sys.stdout.write('\riTunes ' + country + ' ' + str(per) + '%')
                sys.stdout.flush()
                SRFile.write(itunesDataMiner(line, sales_period))
            sys.stdout.write('\riTunes ' + country + ' 100% COMPLETE!\n')
            sys.stdout.flush()

    #TopSpin Data Mining
    if TopSpinFiles:
        TS_csv = csv.reader(open(TopSpinFiles[0], 'rU'), delimiter=",", quotechar='"')
        TS_csv.next()
        TS_csv = list(TS_csv)
        line_count = 0
        for line in TS_csv:
            line_count += 1
            per = line_count / float(len(TS_csv)) * 100
            sys.stdout.write("\rTopSpin %d%%" % per)
            sys.stdout.flush()
            SRFile.write(TopSpinDataMiner(line, sales_period))
        print " COMPLETE!"

    #TuneCore Data Mining
    if TuneCoreFiles:
        TC_csv = csv.reader(open(TuneCoreFiles[0], 'rU'), delimiter=",", quotechar='"')
        TC_csv.next()
        TC_csv = list(TC_csv)
        line_count = 0
        for line in TC_csv:
            line_count += 1
            per = line_count / float(len(TC_csv)) * 100
            sys.stdout.write("\rTuneCore %d%%" % per)
            sys.stdout.flush()
            SRFile.write(TuneCoreDataMiner(line, sales_period))
        print " COMPLETE!"

    #BundleDragon Data Mining
    if BundleDragonFiles:
        BD_csv = csv.reader(open(BundleDragonFiles[0], 'rU'), delimiter=",", quotechar='"')
        BD_csv.next()
        BD_csv = list(BD_csv)
        line_count = 0
        for line in BD_csv:
            line_count += 1
            per = line_count / float(len(BD_csv)) * 100
            sys.stdout.write("\rBundleDragon Sales %d%%" % per)
            sys.stdout.flush()
            SRFile.write(BundleDragonDataMiner(line, sales_period))
        print " COMPLETE!"

    #Direct Data Mining
    if DirectFiles:
        Direct_csv = csv.reader(open(DirectFiles[0], 'rU'), delimiter=",", quotechar='"')
        Direct_csv.next()
        Direct_csv = list(Direct_csv)
        line_count = 0
        for line in Direct_csv:
            line_count += 1
            per = line_count / float(len(Direct_csv)) * 100
            sys.stdout.write("\rDirect Sales %d%%" % per)
            sys.stdout.flush()
            SRFile.write(DirectDataMiner(line, sales_period))
        print " COMPLETE!"

    #PayPal Data Mining
    if PayPalFiles:
        PP_csv = csv.reader(open(PayPalFiles[0], 'rU'), delimiter=",", quotechar='"')
        line_length = 0
        PP_csv = list(PP_csv)
        line_count = 0
        for line in PP_csv:
            line_count += 1
            if not line:
                continue
            if not re.search("^\d{1,2}\/\d{1,2}\/\d{4}$", line[0]):
                continue
            per = line_count / float(len(PP_csv)) * 100
            sys.stdout.write("\rPayPal %d%%" % per)
            sys.stdout.flush()
            SRFile.write(PayPalDataMiner(line, sales_period))
        print " COMPLETE!"

    #MATCH Data Mining
    if matchFiles:
        for filename in matchFiles:
            match_convert_table = matchConversionMiner(filename)
            match_csv = csv.reader(open(filename, 'rU'), delimiter="\t", quotechar='"')
            country = filename.rsplit("_", 1)[1][0:2]
            match_csv.next()
            match_csv = list(match_csv)
            match_length = len(match_csv)
            line_count = 0
            for line in match_csv:
                if len(line) == 2:
                    break
                match_convert = match_convert_table[line[17]]
                line_count += 1
                per = int(line_count / float(len(match_csv)) * 100)
                sys.stdout.write('\rMatch %s %s%%' % (country, per))
                sys.stdout.flush()
                SRFile.write(matchDataMiner(line, sales_period, match_convert))
            sys.stdout.write('\rMatch %s 100%% COMPLETE!\n' % country)
            sys.stdout.flush()

    sales_db.commit_to_db()

    #Error Report Printing
    #Any errors printed in console are purely for debug purposes.
    base_file_path = '*scrubbed*'
    warningReport = "".join(warningReport)
    errorReport = "".join(errorReport)
    if warningReport:
        errorFile = open("%s/sales/error/%s_%s_errorlog.txt" % (base_file_path, month, year), 'w')
        os.chmod("%s/sales/error/%s_%s_errorlog.txt" % (base_file_path, month, year), 666)
        errorFile.write(warningReport)
        shitDoneBroke = True
    if errorReport:
        errorFile = open("%s/sales/error/%s_%s_errorlog.txt" % (base_file_path, month, year), 'a')
        os.chmod("%s/sales/error/%s_%s_errorlog.txt" % (base_file_path, month, year), 666)
        errorFile.write(errorReport)
        shitDoneBroke = True

sales_db.close_db_connection(db_cursor)
if shitDoneBroke:
    print 'SHIT DONE BROKE. Check your error logs'
