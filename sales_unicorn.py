#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os
import sales_tools.sales_SQLaccess as sales_SQLaccess
from decimal import *
from math import ceil

###########################################################
# sales_unicorn.py: Because this is where the magic happens #
###########################################################


class SALES_CALC:
    SR_dates = []
    printAllTheThings = False

#########################
# Initialization method #
#########################

    def calc(self, artist_names, printAllTheThings, SR_dates):
        self.printAllTheThings = printAllTheThings
        self.SR_dates = SR_dates
        start_date = self.SR_dates[0]
        end_date = self.SR_dates[-1]
        self.sales_db = sales_SQLaccess.SALES_DB_ACCESS()
        self.db_cursor = self.sales_db.db_access()
        absolute_file_path = "*scrubbed*"

        #Generate Artist reports
        if self.printAllTheThings:
            self.artist_totals_file = open('%s/reports/%s-%s/_artist_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 'w')
            os.chmod('%s/reports/%s-%s/_artist_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 666)

            self.pub_totals_file = open('%s/reports/%s-%s/_publisher_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 'w')
            os.chmod('%s/reports/%s-%s/_publisher_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 666)

            self.mm_totals_file = open('%s/reports/%s-%s/mm/_%s-%s_mmid_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"),
                    start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 'w')
            os.chmod('%s/reports/%s-%s/mm/_%s-%s_mmid_payments.csv'
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"),
                    start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")), 666)

        else:
            self.artist_totals_file = ''
            self.pub_totals_file = ''
        self.generate_artist_report(artist_names)

        self.sales_db.close_db_connection(self.db_cursor)

###########################
# Artist Report Main Loop #
###########################

    def generate_artist_report(self, artist_names):
        start_date = self.SR_dates[0]
        end_date = self.SR_dates[-1]
        composition_ids = []
        track_ids = []
        absolute_file_path = "*scrubbed*"

        if(self.printAllTheThings):
            self.db_cursor.execute("SELECT name FROM artist")
            artist_names = list(self.db_cursor.fetchall())
            for x in range(len(artist_names)):
                artist_names[x] = list(artist_names[x])
                artist_names[x] = artist_names[x][0]

        line_count = 0
        for artist_name in artist_names:
            del composition_ids[:]
            del track_ids[:]

        ###################
        # Progress status #
        ###################

            line_count += 1
            per = line_count / float(len(artist_names)) * 100
            sys.stdout.write("\rArtist Reports %d%%" % per)
            sys.stdout.flush()

        ##########################
        # Initialize report file #
        ##########################

            #Get client id
            self.db_cursor.execute("SELECT id FROM artist WHERE name LIKE %s", (artist_name,))
            found = self.db_cursor.fetchone()
            if found:
                artist_id = found[0]
            else:
                print "Artist name: %s Not Found!" % artist_name
                continue

            #Sanitize artist name
            artist_filename = artist_name.replace("/", " ")
            artist_filename = artist_filename.replace(":", "")
            artist_filename = artist_filename.replace("/", "\\")
            artist_filename = '%s_%s-%s_Report.csv' \
                % (artist_filename, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"))
            artist_filename = '%s/reports/%s-%s/%s' \
                % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"), artist_filename)

            artist_report_file = open(artist_filename, 'w')
            os.chmod(artist_filename, 666)

        ##################################
        # Track side of Report Generator #
        ##################################

            #Get track ids
            self.db_cursor.execute("SELECT track_id FROM artist_track \
                WHERE artist_id = %s;", (artist_id,))
            track_ids = list(self.db_cursor.fetchall())

            for x in range(len(track_ids)):
                self.db_cursor.execute("SELECT id, title FROM track WHERE id = %s",
                    (track_ids[x][0]))
                track_ids[x] = self.db_cursor.fetchone()

            #Now sort by name
            track_ids = sorted(track_ids, key=lambda track_info: track_info[1])
            for x in range(len(track_ids)):
                track_ids[x] = track_ids[x][0]

            if track_ids:
                artist_tracks = {'artist_id': artist_id, 'track_ids': track_ids}
                artist_report_file, totalNetIncome = self.make_track_report(artist_name, \
                    artist_tracks, artist_report_file)
            else:
                totalNetIncome = 0

        ########################################
        # Composition side of Report Generator #
        ########################################

            #Get composition ids
            self.db_cursor.execute("SELECT composition_id FROM composition_copyright_holder \
                WHERE copyright_holder_id = %s;", (artist_id,))
            composition_ids = list(self.db_cursor.fetchall())

            for x in range(len(composition_ids)):
                self.db_cursor.execute("SELECT id, name FROM composition WHERE id = %s",
                    (composition_ids[x][0]))
                composition_ids[x] = self.db_cursor.fetchone()

            composition_ids = filter(None, composition_ids)

            if composition_ids:
                #Now sort by name
                composition_ids = sorted(composition_ids, key=lambda comp_info: comp_info[1])
                for x in range(len(composition_ids)):
                    composition_ids[x] = composition_ids[x][0]

                artist_compositions = {'artist_id': artist_id, 'composition_ids': composition_ids}

                totalRoyalty = self.make_composition_report(artist_name, \
                    artist_compositions, artist_report_file)
            else:
                totalRoyalty = 0

        ################
        # Store totals #
        ################
            self.sales_db.total_inserter(artist_id, self.SR_dates, totalNetIncome, totalRoyalty, self.db_cursor)
            if self.printAllTheThings and totalNetIncome:
                self.mm_totals_file.write("\"%s\",\"%s\",\"%s\"\n" % (artist_id, totalNetIncome, artist_name))
            self.sales_db.commit_to_db()
            artist_report_file.close()

        ###############################
        #Take care of empty files here#
        ###############################
            if self.file_len(artist_filename) < 2:
                empty_filename = artist_name.replace("/", " ")
                empty_filename = empty_filename.replace(":", "")
                empty_filename = empty_filename.replace("/", "\\")
                empty_filename = '%s_%s-%s_Report.csv' \
                    % (empty_filename, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"))
                empty_filename = '%s/reports/%s-%s/empty/%s' \
                    % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"), empty_filename)

                #Now copy it over
                artist_report_file = open(artist_filename, 'r')
                empty_report_file = open(empty_filename, 'w')
                os.chmod(empty_filename, 666)
                for line in artist_report_file:
                    empty_report_file.write(line)
                os.remove(artist_filename)
                empty_report_file.close()
            else:
                mm_filename = '%s.csv' % artist_id
                mm_filename = '%s/reports/%s-%s/mm/%s' \
                    % (absolute_file_path, start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y"), mm_filename)
                mm_report_file = open(mm_filename, 'w')
                os.chmod(mm_filename, 666)
                artist_report_file = open(artist_filename, 'r')
                for line in artist_report_file:
                    mm_report_file.write(line)

        print " Complete!"

#########################################################################################
#                                Track Report Generator                                 #
#########################################################################################
#######################
# Track Report Writer #
#######################

    def make_track_report(self, artist_name, artist_tracks, artist_report_file):

        #Starting Data
        track_ids = artist_tracks['track_ids']
        artist_id = artist_tracks['artist_id']
        client_albums_data = []

        #Totals
        totalNetIncome = 0.0
        totalDownloads = 0
        totalStreams = 0

        #And dates
        start_date = self.SR_dates[0]
        end_date = self.SR_dates[-1]
        artist_report = []

    ##############################################
    # Generate track sales portion of the report #
    ##############################################

        for track_id in track_ids:
            """
            Grab all albums for the track and see if it was released
            at some point. If it hasn't been just ignore it and skip
            to the next track.
            """
            self.db_cursor.execute("SELECT album_id, isrc, record_number \
                                    FROM album_track \
                                    WHERE track_id = %s \
                                    AND is_active = 1;", (track_id,))
            track_meta_data = list(self.db_cursor.fetchall())
            for x in range(len(track_meta_data)):
                album_id = track_meta_data[x][0]
                for report_date in self.SR_dates:
                    self.db_cursor.execute("SELECT title, upc \
                                            FROM album \
                                            WHERE id = %s \
                                            AND sales_start_date <= %s \
                                            AND (sales_end_date >= %s OR sales_end_date IS NULL)\
                                            AND is_deleted = 0 \
                                            AND submission_status_id in (5, 6);",
                                            (album_id, report_date, report_date))
                    album_info = self.db_cursor.fetchone()

                    if album_info:
                        break

                if not album_info:
                    track_meta_data[x] = None
                    continue

                self.db_cursor.execute("SELECT COUNT(track_id) \
                                        FROM album_track \
                                        WHERE album_id = %s \
                                        AND is_active = 1;", (album_id))

                track_count = self.db_cursor.fetchone()[0]
                isrc = track_meta_data[x][1]
                record_num = track_meta_data[x][2]
                track_meta_data[x] = {'album_id': album_id, 'isrc': isrc,
                                      'record_num': record_num, 'album_info': album_info,
                                      'track_count': track_count}

            track_meta_data = filter(None, track_meta_data)

            if not track_meta_data:
                continue

            #Get track info
            self.db_cursor.execute("SELECT title, track_length, share_artist \
                                    FROM track \
                                    WHERE id = %s", (track_id,))
            track_info = self.db_cursor.fetchone()

            if not track_info[2]:
                continue
            if not track_info[1]:
                continue

            #Count up the covers
            self.db_cursor.execute("SELECT COUNT(id) \
                                    FROM track_composition \
                                    WHERE track_id = %s \
                                    AND is_cover = 1", (track_id,))
            covers = self.db_cursor.fetchone()
            covers = covers[0]

            #Calulate the royalty rate
            royalty_rate = self.convertToMinutes(track_info[1]) * .0175
            if royalty_rate < .091:
                royalty_rate = .091
            royalty_rate *= covers

            #Calculate the artist share
            self.db_cursor.execute("SELECT ownership_percent \
                                    FROM artist_track \
                                    WHERE track_id = %s \
                                    AND artist_id = %s;",
                                    (track_id, artist_id))
            ownership_percent = float(self.db_cursor.fetchone()[0]) / 100
            artist_share = ownership_percent * float(track_info[2]) / 100
            artist_share *= 100

        #############################
        # FOR LOOP THROUGH ISRCS!!! #
        #############################

            for track_meta_datum in track_meta_data:
                #For ease of use
                album_id = track_meta_datum['album_id']
                ISRC = track_meta_datum['isrc']
                record_num = track_meta_datum['record_num']
                track_count = track_meta_datum['track_count']
                album_info = track_meta_datum['album_info']

                #Check if album track is on has been released and still on sale
                #sometime within the report date range

                #Generate or add to album data for client
                found = False
                for x in range(len(client_albums_data)):
                    if client_albums_data[x]['album_id'] == album_id:
                        client_albums_data[x]['royalty_rate'] += royalty_rate
                        client_albums_data[x]['total_percent'] += artist_share
                        client_albums_data[x]['covers'] += covers
                        found = True
                        break

                if not found:
                    client_albums_data.append({'album_id': album_id,
                        'album_name': album_info[0], 'upc': album_info[1],
                        'royalty_rate': royalty_rate, 'total_percent': artist_share,
                        'track_count': track_count, 'covers': covers})

                #Generate the sales figures and do necessary calculations
                results = self.generate_track_sales(ISRC, royalty_rate)
                totalDownloads += results[5]
                totalStreams += results[3]
                gross_income = results[4] - results[1]
                artist_percent = str(Decimal(str(artist_share)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) + "%"
                net_income = gross_income * artist_share / 100
                totalNetIncome += net_income

                #Write out gathered info
                artist_report.append("\"%s-%s\"," % (start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")))
                artist_report.append("\"%s\",\"%s\"," % (artist_name, album_info[0]))
                artist_report.append("\"%s\",\"%s\"," % (album_info[1], track_info[0]))
                artist_report.append("\"%s\",\"%s\"," % (artist_name, record_num))
                artist_report.append("\"%s\",\"%s\"," % (ISRC, self.print_seconds_as_time(track_info[1])))
                artist_report.append("\"%s\",%s" % (covers, results[0]))
                artist_report.append("\"%s\","
                    % Decimal(str(gross_income)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                artist_report.append("\"%s\"," % artist_percent)
                artist_report.append("\"%s\"\n"
                    % Decimal(str(net_income)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

    ##############################################
    # Generate album sales portion of the report #
    ##############################################

        #Sorts album by name
        client_albums_data = sorted(client_albums_data, key=lambda stuff: stuff['album_name'])
        for client_albums_datum in client_albums_data:
            #Ease of reading
            album_id = client_albums_datum['album_id']
            album_name = client_albums_datum['album_name']
            upc = client_albums_datum['upc']
            royalty_rate = client_albums_datum['royalty_rate']
            total_percent = client_albums_datum['total_percent']
            track_count = client_albums_datum['track_count']
            covers = client_albums_datum['covers']

            #Do ALL THE CALCULATIONS
            total_percent = total_percent / track_count

            results = self.generate_track_sales(upc, royalty_rate)
            totalDownloads += results[5] * track_count
            totalStreams += results[3] * track_count
            gross_income = results[4] - results[1]
            artist_percent = "%s%%" \
                % Decimal(str(total_percent)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            net_income = gross_income * total_percent / 100
            totalNetIncome += net_income

            #Write it all out
            artist_report.append("\"%s-%s\","
                % (start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")))
            artist_report.append("\"%s\",\"%s\",\"%s\",\"\"," % (artist_name, album_name, upc))
            artist_report.append("\"%s\",\"\",\"\",\"\"," % artist_name)
            artist_report.append("\"%s\",%s" % (covers, results[0]))
            artist_report.append("\"%s\","
                % Decimal(str(gross_income)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
            artist_report.append("\"%s\"," % artist_percent)
            artist_report.append("\"%s\"\n"
                % Decimal(str(net_income)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

        if artist_report:
            artist_report_file.write('"Sales Period","Client Name","Album Name","UPC Code",'
            + '"Track Name","Artist Name","Record Number","ISRC Code",'
            + '"Track Length","No. of Covers","Units Downloaded",'
            + '"Units Streamed","Gross Sales","Royalty Rate",'
            + '"Publisher Royalty","Gross Income","Client Split",'
            + '"Net Income"\n')

            for entry in artist_report:
                artist_report_file.write(entry)

            artist_report_file.write(",,,,,,,,,,,,,,,,\"Total Net Income:\",")
            artist_report_file.write("\"%s\"\n"
                % Decimal(str(totalNetIncome)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
            artist_report_file.write(",,,,,,,,,,,,,,,,\"Total Downloads:\",\"")
            artist_report_file.write("%s\"\n" % totalDownloads)
            artist_report_file.write(",,,,,,,,,,,,,,,,\"Total Streams:\",\"%s\"\n\n" % totalStreams)

            #Write to the total files
            if self.printAllTheThings:
                self.artist_totals_file.write("\"%s\",\"%s\",\"" % (artist_id, artist_name))
                self.artist_totals_file.write("%s\"\n"
                    % Decimal(str(totalNetIncome)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

        return artist_report_file, totalNetIncome

#######################################
# Artist Track Sales Report Generator #
#######################################

    def generate_track_sales(self, ISRC_or_UPC, royalty_rate):
        global SR_dates

        ##################
        # Get data first #
        ##################
        gross_sales = 0
        unit_sales = 0
        streams = 0
        downloads = 0
        for SR_date in self.SR_dates:
            self.db_cursor.execute("SELECT gross_sales, num_unit_sales, num_streams, num_downloads \
                                    FROM sales WHERE sales_period = %s \
                                    AND code = %s;", (SR_date, str(ISRC_or_UPC)))
            sales_data = self.db_cursor.fetchone()
            if not sales_data:
                continue

            gross_sales += float(sales_data[0])
            unit_sales += sales_data[1]
            streams += sales_data[2]
            downloads += sales_data[3]

        ############################
        # Now generate report text #
        ############################
        #Note: Maybe come back and convert the lists to dicts
        results = []
        report_string = []

        #Generate empty line if there are no unit sales
        if(unit_sales == 0):
            report_string.append("\"" + str(downloads) + "\",")
            report_string.append("\"" + str(streams) + "\",")
            report_string.append("\"" + str(Decimal(str(gross_sales)).quantize(Decimal('.01'),
                    rounding=ROUND_HALF_UP)) + "\",")
            report_string.append("\"" + str(royalty_rate) + "\",\"0.00\",")
            report_string = "".join(report_string)
            results.extend([report_string, 0, unit_sales, streams])
            results.extend([gross_sales, downloads])
            return results

        gross_royalty = royalty_rate * unit_sales
        net_royalty = gross_royalty

        #Make report string
        report_string.append("\"" + str(downloads) + "\",")
        report_string.append("\"" + str(streams) + "\",")
        report_string.append("\"" + str(Decimal(str(gross_sales)).quantize(Decimal('.01'),
            rounding=ROUND_HALF_UP)) + "\",")
        report_string.append("\"" + str(royalty_rate) + "\",")
        report_string.append("\"" + str(Decimal(str(net_royalty)).quantize(Decimal('.01'),
            rounding=ROUND_HALF_UP)) + "\",")
        report_string = "".join(report_string)

        #Put it together
        results.extend([report_string, net_royalty, unit_sales, streams])
        results.extend([gross_sales, downloads])
        return results

#########################################################################################
#                              Composition Report Generator                             #
#########################################################################################
###########################
# Publisher Report Writer #
###########################

    def make_composition_report(self, artist_name, artist_compositions, artist_report_file):
        #General use data
        composition_ids = artist_compositions['composition_ids']
        artist_id = artist_compositions['artist_id']

        #Totals
        totalRoyalty = 0.0

        #And dates
        start_date = self.SR_dates[0]
        end_date = self.SR_dates[-1]

        artist_report = []

        for comp_id in composition_ids:
            #Find if artist owns any part of the track.
            self.db_cursor.execute("SELECT ownership_percent \
                                    FROM composition_copyright_holder \
                                    WHERE copyright_holder_id = %s \
                                    AND composition_id = %s;",
                                    (artist_id, comp_id))
            ownership_percent = float(self.db_cursor.fetchone()[0])
            if ownership_percent == 0:
                continue

            #Grab compilation data
            self.db_cursor.execute("SELECT name, original_artist, composer \
                                    FROM composition \
                                    WHERE id = %s \
                                    AND (entered_public_domain_on > %s \
                                    OR entered_public_domain_on IS NULL \
                                    OR entered_public_domain_on = '0000-00-00')",
                                    (comp_id, start_date))
            composition_data = self.db_cursor.fetchone()
            if not composition_data:
                continue

            composition_name = composition_data[0]
            original_artist = composition_data[1]

            #Build nice composers string
            #TODO: This won't work yet! Wait on Seabass.
            """
            self.db_cursor.execute("SELECT composer.name \
                                    FROM composer, compostion_composers \
                                    WHERE compostion_composers.composition_id = %s \
                                    AND compostion_composers.composer_id = composer.id"
                                    , (comp_id, ))
            composers = list(self.db_cursor.fetchall())
            for x in range(len(composers)):
                composers[x] = composers[x][0]
            if len(composers) > 1:
                composers = ", ".join(composers)
            else:
                composers = composers[0]
            """
            composers = composition_data[2]

            #Now do the tracks
            self.db_cursor.execute("SELECT track_id \
                                    FROM track_composition \
                                    WHERE composition_id = %s \
                                    AND is_cover = 1;",
                                    (comp_id,))
            track_ids = self.db_cursor.fetchall()

            for track_id in track_ids:
                track_id = track_id[0]

                #Grab album_id, isrc, and record_num pairings for the track
                self.db_cursor.execute("SELECT album_id, isrc, record_number \
                                        FROM album_track \
                                        WHERE track_id = %s \
                                        AND is_active = 1;", (track_id,))
                track_meta_data = list(self.db_cursor.fetchall())
                for x in range(len(track_meta_data)):
                    album_id = track_meta_data[x][0]
                    isrc = track_meta_data[x][1]
                    record_num = track_meta_data[x][2]
                    track_meta_data[x] = {'album_id': album_id, 'isrc': isrc, 'record_num': record_num}

                #Get track info
                self.db_cursor.execute("SELECT title, track_length \
                                        FROM track \
                                        WHERE id = %s", (track_id,))
                track_info = self.db_cursor.fetchone()

                #Get Artist Names
                track_artists = []
                self.db_cursor.execute("SELECT artist_id FROM artist_track \
                    WHERE track_id = %s;", (track_id,))
                track_artist_ids = self.db_cursor.fetchall()
                for track_artist_id in track_artist_ids:
                    self.db_cursor.execute("SELECT name FROM artist WHERE id = %s", (track_artist_id[0]))
                    track_artist = self.db_cursor.fetchone()
                    track_artists.append(track_artist[0])
                track_artists = ", ".join(track_artists)

                ##############################################
                # Loop based on album ids..... unfortunately #
                ##############################################
                for track_meta_datum in track_meta_data:
                    album_id = track_meta_datum['album_id']
                    ISRC = track_meta_datum['isrc']
                    record_num = track_meta_datum['record_num']

                    #Check if album track is on has been released and still on sale
                    #sometime within the report date range
                    for report_date in self.SR_dates:
                        self.db_cursor.execute("SELECT title, upc \
                                                FROM album \
                                                WHERE id = %s \
                                                AND sales_start_date <= %s \
                                                AND (sales_end_date >= %s OR sales_end_date IS NULL)\
                                                AND is_deleted = 0 \
                                                AND submission_status_id in (5, 6);",
                                                (album_id, report_date, report_date))
                        album_info = self.db_cursor.fetchone()
                        if album_info:
                            break
                    if not album_info:
                        continue

                    royalty_rate = self.convertToMinutes(track_info[1]) * .0175
                    if royalty_rate < .091:
                        royalty_rate = .091
                    results = self.generate_composition_sales([ISRC, album_info[1]], royalty_rate, ownership_percent)
                    totalRoyalty += results[1]

                    #Write track and artist name
                    artist_report.append("\"%s-%s\"," % (start_date.strftime("%m.%Y"), end_date.strftime("%m.%Y")))
                    artist_report.append("\"%s\",\"%s\"," % (artist_name, composition_name))
                    artist_report.append("\"%s\",\"%s\"," % (original_artist, composers))
                    artist_report.append("\"%s\",\"%s\"," % (track_info[0], track_artists))
                    artist_report.append("\"%s\",\"%s\"," % (record_num, ISRC))
                    artist_report.append("\"%s\"," % self.print_seconds_as_time(track_info[1]))
                    artist_report.append("\"%s\",\"%s\",%s" % (album_info[0], album_info[1], results[0]))
                    artist_report.append("\"%s%%\","
                        % Decimal(str(ownership_percent)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                    artist_report.append("\"%s\"\n" % results[1])

        """
        Do actual file writing if anything exists.
        """
        if artist_report:
            artist_report_file.write('"Sales Period","Copyright Holder Name","Composition Name",'
            + '"Original Artist","Composers","Track Name",'
            + '"Artist Name","Record Number","ISRC Code","Track Length",'
            + '"Album Name","UPC Code","Unit Sales","Royalty Rate","Gross Royalty"'
            + ',"Ownership Percentage","Net Royalty"\n')

            for entry in artist_report:
                artist_report_file.write(entry)

            totalRoyalty = Decimal(str(totalRoyalty)).quantize(Decimal('.01'),
                rounding=ROUND_HALF_UP)
            artist_report_file.write(",,,,,,,,,,,,,,,,\"Total Net Royalty:\",\"%s\"\n"
                % totalRoyalty)

            self.db_cursor.execute("SELECT payment_threshold FROM artist \
                WHERE id = %s;", (artist_id,))
            artist_report_file.write(",,,,,,,,,,,,,,,,\"Royalty Threshold:\",\"%s\"\n"
                % self.db_cursor.fetchone()[0])

            if self.printAllTheThings:
                self.pub_totals_file.write("\"%s\",\"%s\",\"" % (artist_id, artist_name))
                self.pub_totals_file.write("%s\"\n"
                    % Decimal(totalRoyalty).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

        return totalRoyalty

#################################
# Composition Royalty Generator #
#################################

    def generate_composition_sales(self, ISRC_UPC_list, royalty_rate, ownership_percent):
        ownership_percent /= 100
        unit_sales = 0

        #Aggregate data
        for SR_date in self.SR_dates:
            for code in ISRC_UPC_list:
                self.db_cursor.execute("SELECT num_unit_sales FROM sales WHERE sales_period = %s \
                    AND code = %s;", (SR_date, str(code)))
                num_unit_sales = self.db_cursor.fetchone()
                if num_unit_sales:
                    unit_sales += num_unit_sales[0]

        #Now generate report
        results = []

        if(unit_sales == 0):
            results.append("\"0\",\"0\",\"0\",")
            results.append(0)
            return results

        gross_royalty = royalty_rate * unit_sales
        net_royalty = gross_royalty * ownership_percent

        results.append("\"%s\",\"%s\",\"%s\"," % (unit_sales, royalty_rate, gross_royalty))
        results.append(net_royalty)
        return results

##################################################################
#                       Utility functions                        #
##################################################################

#############################
# Convert string to Minutes #
#############################

    def convertToMinutes(self, trackTime):
        return ceil(float(trackTime) / 60.0)

##########################################
# Convert seconds to minutes and seconds #
##########################################

    def print_seconds_as_time(self, seconds):
        minutes, seconds = divmod(int(ceil(seconds)), 60)
        return "%s:%s" % (minutes, str(seconds).zfill(2))

###############################
# Get number of lines in file #
###############################

    def file_len(self, fname):
        file_to_count = open(fname, "r")
        i = 0
        for line in file_to_count:
            i += 1
        file_to_count.close()
        return i
