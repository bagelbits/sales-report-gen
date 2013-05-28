import sqlite3
import csv
import os
import math

# Get UPC/ISRC, track/album name, and price for everything sold by iTunes

conn = sqlite3.connect('iTunes.db')
conn.text_factory = str
curs = conn.cursor()

curs.execute("CREATE TABLE my_list(code TINYTEXT PRIMARY KEY, title TINYTEXT, price FLOAT)")

for year in range(2009, 2013):
	for month in range(1, 13):
		salesfname = "../sales/" + str(year) + "/salesfile_" + str(month).zfill(2) + "_" + str(year) + ".csv"
		print salesfname
		if not os.path.exists(salesfname):
			continue
		sr_csv = csv.reader(open(salesfname, 'rU'), delimiter=",", quotechar='"')
		sr_csv.next()
		for line in sr_csv:
			if not 'iTunes US' in line[3] and not 'US' in line[4]:
				continue
			#Grab UPC or ISRC
			if line[1]:
				code = line[1]
			else:
				code = line [2]
			title = line[19] + " - " + line[20]
			price = math.fabs(float(line[10]))
			curs.execute("SELECT * FROM my_list WHERE code = ?", (code,))
			found = curs.fetchone()
			if found:
				continue
			curs.execute("INSERT INTO my_list VALUES(?,?,?)", (code, title, price))
			conn.commit()
conn.commit()

results = open("tool_output/UPC_ISRC_list.csv", "w")
curs.execute("SELECT * FROM my_list")
for line in curs:
	line = list(line)
	line[1] = line[1].replace('"', '')
	#line[1].replace(',', '')
	results.write("\"" + '","'.join(map(str, line)) + "\"\n")
os.remove("iTunes.db")
