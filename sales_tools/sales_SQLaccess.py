#!/usr/bin/env python
# -*- coding: utf8 -*-

import MySQLdb
import sys


class SALES_DB_ACCESS:

    def db_access(self):
        try:
            self.conn = MySQLdb.connect(host="localhost",
                                        user="app_unicorn",
                                        passwd="*scrubbed*",
                                        db="mm_prod")
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)
        db_cursor = self.conn.cursor()
        self.conn.commit()

        return db_cursor

####################
# Commit that shit #
####################

    def commit_to_db(self):
        self.conn.commit()

###################
# Close that shit #
###################

    def close_db_connection(self, db_cursor):
        db_cursor.close()
        self.conn.close()

########################################################
#                    SR Table Setup                    #
# If data already exists for a date, it deletes it all #
########################################################

    def SR_init(self, db_cursor, sales_period):
        db_cursor.execute("SELECT id FROM sales \
                           WHERE sales_period = %s", (sales_period,))
        sales_ids = db_cursor.fetchall()
        if sales_ids:
            for sales_id in sales_ids:
                db_cursor.execute("UPDATE sales \
                                   SET gross_sales = 0, num_unit_sales = 0, \
                                   num_streams = 0, num_downloads = 0 \
                                   WHERE id = %s;",
                                   (sales_id[0],))

####################
# SR Data Inserter #
####################
    def sr_data_inserter(self, db_cursor, sales_period, code, data):
        db_cursor.execute("SELECT id FROM sales \
                           WHERE sales_period = %s AND code = %s",
                           (sales_period, code))
        sales_id = db_cursor.fetchone()
        #If it doesn't exist make entries for it in sales_meta_data and sales
        if not sales_id:
            db_cursor.execute("INSERT INTO sales \
                               VALUES(NULL,%s,%s,%s,%s,%s,%s)",
                               (sales_period, code, float(data['gross_sales']),
                                int(data['unit_sales']), int(data['streams']),
                                int(data['downloads'])))
            return

        db_cursor.execute("SELECT gross_sales, num_unit_sales, \
                           num_streams, num_downloads \
                           FROM sales WHERE id = %s",
                           (sales_id[0],))
        meta_data_entry = list(db_cursor.fetchone())
        meta_data_entry = [float(x) for x in meta_data_entry]
        meta_data_entry[0] += float(data['gross_sales'])
        meta_data_entry[1] += int(data['unit_sales'])
        meta_data_entry[2] += int(data['streams'])
        meta_data_entry[3] += int(data['downloads'])

        db_cursor.execute("UPDATE sales \
                           SET gross_sales = %s, num_unit_sales = %s, \
                           num_streams = %s , num_downloads = %s \
                           WHERE id = %s;",
                           (meta_data_entry[0], meta_data_entry[1],
                           meta_data_entry[2], meta_data_entry[3],
                           sales_id[0]))

###########################
# UPC/ISRC OVERRIDE QUERY #
###########################

    def id_override(self, db_cursor, bad_id):
        db_cursor.execute("SELECT good_code FROM sales_override \
            WHERE bad_code = %s;", (bad_id,))
        found = db_cursor.fetchone()
        if found:
            return found[0]
        return bad_id

####################
# UPC/ISRC checker #
####################

    def upc_isrc_checker(self, db_cursor, UPC, ISRC):
        if UPC:
            db_cursor.execute("SELECT * FROM album \
                               WHERE upc = %s \
                               AND is_deleted = 0 \
                               AND submission_status_id IN (5, 6)",
                               (UPC,))
            found = db_cursor.fetchone()
            if found:
                return True
        if ISRC:
            db_cursor.execute("SELECT * FROM album_track \
                               WHERE isrc = %s AND is_active = 1",
                (ISRC,))
            found = db_cursor.fetchone()
            if found:
                return True
        return False

##########################################
# Client/Copyright Holder Total Inserter #
##########################################

    def total_inserter(self, artist_id, SR_dates, totalNetIncome,
                       totalRoyalty, db_cursor):
        if totalNetIncome == 0 and totalRoyalty == 0:
            return

        startDate = SR_dates[0]
        endDate = SR_dates[-1]

        db_cursor.execute("SELECT id FROM artist_totals \
            WHERE period_start = %s AND period_end = %s \
            AND artist_id = %s;", (startDate, endDate, artist_id))
        found = db_cursor.fetchone()
        if found:
            db_cursor.execute("UPDATE artist_totals SET total_net_income = %s \
                , total_net_royalty = %s \
                WHERE id = %s;", (totalNetIncome, totalRoyalty, found[0]))
        else:
            db_cursor.execute("INSERT INTO artist_totals \
                               VALUES(NULL, %s, %s, %s, %s, %s)",
                               (artist_id, startDate, endDate,
                                totalNetIncome, totalRoyalty))
