#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
from Levenshtein import distance


def replaceHardCode(track_name):
	if track_name == "somethin' like that":
		track_name = "something like that"
	if track_name == "what's my name? / only girl (a cappella)":
		track_name = "what's my name? / only girl"
	if track_name == "to sostre (the two sisters)":
		track_name = 'to søstre (the two sisters)'
	if track_name == "lost":
		track_name = 'lost?'
	return track_name

def parser(SE_csv, f):
	SE_csv.next()
	ISRC_dict = {}
	track_id = 0
	for line in SE_csv:

		if len(line) == 0:
			break
		for x in list(ISRC_dict.keys()):
			ISRC_dict.pop(x)

		track_csv = csv.reader(open('table_dump/tracks.txt', 'rU'), delimiter=",", quotechar='"')
		track_csv.next()
		track_csv.next()
		saved_min_distance = -1
		for track in track_csv:
			if saved_min_distance == -1:
				saved_min_distance = distance(line[2], track[1].strip().lower())
				saved_details = [track[0].strip(), track[1].strip(), track[3].strip()]
			curr_min_distance = distance(line[2], track[1].strip().lower())
			if saved_min_distance > curr_min_distance:
				saved_min_distance = curr_min_distance
				saved_details = [track[0].strip(), track[1].strip(), track[3].strip()]
		ISRC_dict[int(saved_details[0])] = [saved_details[1], saved_details[2]]


		if len(ISRC_dict) > 1:
			client_csv = csv.reader(open('table_dump/clients.txt', 'rU'), delimiter=",", quotechar='"')
			client_csv.next()
			client_csv.next()
			client_id = 0
			saved_min_distance = -1
			line[1] = line[1].lower().strip()
			for client in client_csv:
				if saved_min_distance == -1:
					saved_min_distance = distance(line[1], client[1].lower().strip())
					saved_details = [track[0].strip(), track[1].strip()]
				curr_min_distance = distance(line[2], track[1].strip())
				if saved_min_distance > curr_min_distance:
					saved_min_distance = curr_min_distance
					saved_details = [track[0].strip(), track[1].strip()]
			client_id = saved_details[0]
				#if line[1].lower().strip() in client[1].lower().strip():
					#client_id = int(client[0].strip())
			if not client_id:
				print "FUCK"
				print line[2].lower().strip()
				print line
				continue
			cltrs_csv = csv.reader(open('table_dump/client_tracks.txt', 'rU'), delimiter=",", quotechar='"')
			cltrs_csv.next()
			cltrs_csv.next()
			track_id = 0
			for cltr in cltrs_csv:
				for x in ISRC_dict.keys():
					if int(cltr[2].strip()) == client_id:
						if int(cltr[1].strip()) == x:
							track_id = int(cltr[1].strip())
					if track_id:
						break
				if track_id:
					break
			if not track_id:
				print "TITS"
				print line[2].lower().strip()
				continue
			for x in list(ISRC_dict.keys()):
				if x != track_id:
					ISRC_dict.pop(x)
		if len(ISRC_dict) == 1:
			f.write(str(ISRC_dict) + "\n")
			f.write(str(line) + "\n\n")
		if len(ISRC_dict) != 1:
			print line
			print ISRC_dict
f = open('test_out.txt', 'w')
f.write("import/SoundExchange/03.2012/_statements"
	+ "_1000013380_000316689_1000040333_R_Detail.csv\n\n")
SE_csv = csv.reader(open('import/SoundExchange/03.2012/'
	+ '_statements_1000013380_000316689_1000040333_R_Detail.csv', 'rU'),
	delimiter=",", quotechar='"')
parser(SE_csv, f)
f.write("\n\n\n\n")

f.write("import/SoundExchange/06.2012/"
	+ "_statements_1000022896_000333197_1000040333_R_Detail.csv\n\n")
SE_csv=csv.reader(open('import/SoundExchange/06.2012/'
	+ '_statements_1000022896_000333197_1000040333_R_Detail.csv', 'rU'),
	delimiter=",", quotechar='"')
parser(SE_csv, f)
f.write("\n\n\n\n")

f.write("import/SoundExchange/09.2012/"
	+ "_statements_1000028377_000358914_1000040333_R_Detail.csv\n\n")
SE_csv=csv.reader(open('import/SoundExchange/09.2012/'
	+ '_statements_1000028377_000358914_1000040333_R_Detail.csv', 'rU'),
	delimiter=",", quotechar='"')
parser(SE_csv, f)
