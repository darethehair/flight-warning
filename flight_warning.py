#!/usr/bin/python

"""
flight_warning.py
version 1.00

This program will send a Google mail message when an ADS-B data feed from
a dump1090 stream detects an aircraft within a set distance of a geographic point.

Copyright (C) 2015 Darren Enns <darethehair@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA.
"""

import sys
import smtplib
import datetime
import time
import math
from math import atan2, sin, cos, radians, degrees

plane_position = {}
plane_identification = {}
limit_distance = 10
limit_duplicate_minutes = 60

my_lat = yourlatitude e.g. 49.2 
my_lon = yourlongitude e.g. -98.1

metric_units = True
#metric_units = False

gmail_recv_user = 'yourreceiveruserid@gmail.com'
gmail_send_user = 'yoursenderuserid@gmail.com'
gmail_pwd = 'yourgmailpassword';

timezone_hours = time.altzone/60/60

def haversine(origin, destination):
	lat1, lon1 = origin
	lat2, lon2 = destination

	if (metric_units):
		radius = 6371 # km
	else:
		radius = 3959 # miles

	dlat = radians(lat2-lat1)
	dlon = radians(lon2-lon1)
	a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(radians(lat1)) * math.cos(radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = radius * c

	return d

# this reads in one line at a time from stdin
while True:
   	line=sys.stdin.readline()

	parts = line.split(",")

	type = parts[1]

	icao = parts[4]
	date = parts[8]
	time = parts[9]

	if (type == "1"): # this record type contains the aircraft 'flight' identifier
		flight = parts[10]
		plane_identification[icao] = flight.strip()

	if (type == "3"): # this record type contains the aircraft 'ICAO' identifier, lat/lon, and elevation
		elevation = float(parts[11]) # assumes dump1090 is outputting elevation in feet 
		if (metric_units):
			elevation = int(round(elevation * 0.3048)) # convert elevation feet to meters

		plane_lat = float(parts[14])
		plane_lon = float(parts[15])

		distance = round(haversine((my_lat, my_lon), (plane_lat, plane_lon)),1)

		if (distance <= limit_distance):
			bearing =atan2(sin(radians(plane_lon-my_lon))*cos(radians(plane_lat)), cos(radians(my_lat))*sin(radians(plane_lat))-sin(radians(my_lat))*cos(radians(plane_lat))*cos(radians(plane_lon-my_lon)))
			bearing = round(((degrees(bearing) + 360) % 360),1)

			date_time_local = datetime.datetime.strptime(date + " " + time, '%Y/%m/%d %H:%M:%S.%f')
			date_time_iso = datetime.datetime.strftime(date_time_local, '%Y-%m-%dT%H:%M:%S.%f') + str("%+d" % (-timezone_hours)).zfill(3)

			if (icao not in plane_position and icao in plane_identification):
				plane_position[icao] = date_time_local
				flight = plane_identification[icao]
				msg = date_time_iso + " " + date + " " + time + " " + flight + " " + icao + " " + str(plane_lat) + " " + str(plane_lon) + " " + str(elevation) + " " + str(distance) + " " + str(bearing) + "\n"
				#sys.stdout.write(msg+"*"+"\n")

				smtpserver = smtplib.SMTP("smtp.gmail.com",587)
				smtpserver.ehlo()
				smtpserver.starttls()
				smtpserver.ehlo
				smtpserver.login(gmail_send_user, gmail_pwd)
				header = 'To:' + gmail_recv_user + '\n' + 'From: ' + gmail_send_user + '\n' + 'Subject:WARNING: Pi Detected New Aircraft Nearby: ' + 'FLIGHT=' + flight + ' ICAO=' + icao + ' AZIMUTH=' + str(int(round(bearing))) + unicode(u'\xb0').encode("utf-8") + '\n'
				mail_message = header + '\n' + msg + '\n' + 'http://flightaware.com/live/flight/' + flight + '\n\n'
				smtpserver.sendmail(gmail_send_user, gmail_recv_user, mail_message)
				smtpserver.close()
			elif (icao in plane_position):
				then = plane_position[icao]
				now = datetime.datetime.now()
				diff_minutes = (now - then).total_seconds() / 60.
				if (diff_minutes > limit_duplicate_minutes):
					del plane_position[icao]
			if (icao in plane_position and icao in plane_identification):
				flight = plane_identification[icao]
				msg = date_time_iso + " " + date + " " + time + " " + flight + " " + icao + " " + str(plane_lat) + " " + str(plane_lon) + " " + str(elevation) + " " + str(distance) + " " + str(bearing) + "\n"
				sys.stdout.write(msg)
