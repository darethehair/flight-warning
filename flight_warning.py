#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
flight_warning.py
version 1.04

This program will send a Google mail message when an ADS-B data feed from
a dump1090 stream detects an aircraft within a set distance of a geographic point.
It will also send an email when the aircraft leaves that detection area.

The appearance of the records sent to stdout look like this:

2015-07-27T17:46:16.715000-05,75827C,PAL118,49.88521,-100.47669,11887,186.8,295.6,3.5

The format is as follows:

datetime,icao_code,flight_code,latitude,longitude,elevation,distance,azimuth_bearing,altitude_angle

The units of elevation and distance depend on settings within the code below (i.e. meters/kilometers
or feet/miles).

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

#
# import required libraries
#
import sys
import smtplib
import datetime
import time
import math
from math import atan2, sin, cos, radians, degrees, atan

#
# initialize empty dictionaries
#
plane_dict = {}
plane_hist = {}
plane_msg = {}

# 
# set desired units
#
metric_units = True
#metric_units = False

# 
# set desired distance and time limits
#
limit_distance = 10
limit_duplicate_minutes = 60

#
# set geographic location and elevation
#
my_lat = yourlatitude (positive = north, negative = south)
my_lon = yourlongitude (positive = east, negative = west)
my_elevation = yourantennaelevation

#
# set gmail userids and creditials
#
gmail_recv_user = 'yourreceiveruserid@gmail.com'
gmail_send_user = 'yoursenderuserid@gmail.com'
gmail_pwd = 'yourgmailpassword';

#
# calculate time zone for ISO date/timestamp
#
timezone_hours = time.altzone/60/60

#
# define havesine great-circle-distance routine
#
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

#
# define gmail mail sender routine
#
def send_gmail(gmail_send_user, gmail_recv_user, gmail_pwd, gmail_subject, gmail_body):
	smtpserver = smtplib.SMTP("smtp.gmail.com",587)
	smtpserver.ehlo()
	smtpserver.starttls()
	smtpserver.ehlo
	smtpserver.login(gmail_send_user, gmail_pwd)

	gmail_header = 'To:' + gmail_recv_user + '\n' + 'From: ' + gmail_send_user + '\n' + gmail_subject + '\n'
	gmail_msg = gmail_header + '\n' + gmail_body + '\n\n'
	smtpserver.sendmail(gmail_send_user, gmail_recv_user, gmail_msg)
	smtpserver.close()

#
# loop through all records from dump1090 port 10003 input stream on stdin
#
while True:
   	line=sys.stdin.readline()

	#
	# divide input line into parts and extract desired values
	#
	parts = line.split(",")
	type = parts[1]
	icao = parts[4]
	date = parts[6]
	time = parts[7]
	date_time_local = datetime.datetime.strptime(date + " " + time, '%Y/%m/%d %H:%M:%S.%f')
	date_time_iso = datetime.datetime.strftime(date_time_local, '%Y-%m-%dT%H:%M:%S.%f') + str("%+d" % (-timezone_hours)).zfill(3)

	#
	# check age of newest icao record, compare to newly-input value, and kill dictionary if too old (i.e. start fresh history)
	#
	if (icao in plane_dict):
		then = plane_dict[icao][0]
		now = datetime.datetime.now()
		diff_minutes = (now - then).total_seconds() / 60.
		if (diff_minutes > limit_duplicate_minutes):
			del plane_dict[icao]

	#
	# if type 1 record then extract datetime/flight and create or update dictionary
	#
	if (type == "1"): # this record type contains the aircraft 'flight' identifier
		flight = parts[10].strip()

		if (icao not in plane_dict): 
			plane_dict[icao] = [date_time_local, flight, "", "", "", "", "", "", "", "", ""]
		else:
			plane_dict[icao][0] = date_time_local
			plane_dict[icao][1] = flight

	#
	# if type 3 record then extract datetime/elevation/lat/lon, calculate distance/bearing/angle, and create or update dictionary
	#
	if (type == "3"): # this record type contains the aircraft 'ICAO' identifier, lat/lon, and elevation
		elevation = float(parts[11]) # assumes dump1090 is outputting elevation in feet 
		elevation_units = "ft"
		distance_units = "mi"
		if (metric_units):
			elevation = int(round(elevation * 0.3048)) # convert elevation feet to meters
			elevation_units = "m"
			distance_units = "km"

		plane_lat = float(parts[14])
		plane_lon = float(parts[15])

		distance = round(haversine((my_lat, my_lon), (plane_lat, plane_lon)),1)
		bearing = atan2(sin(radians(plane_lon-my_lon))*cos(radians(plane_lat)), cos(radians(my_lat))*sin(radians(plane_lat))-sin(radians(my_lat))*cos(radians(plane_lat))*cos(radians(plane_lon-my_lon)))
		bearing = round(((degrees(bearing) + 360) % 360),1)

		angle = degrees(atan((elevation - my_elevation)/(distance*1000))) # distance converted from kilometers to meters to match elevation
		if (not metric_units):
			angle = degrees(atan((elevation - my_elevation)/(distance*5280))) # distance converted from miles to feet to match elevation
		angle = round(angle,1)

		if (icao not in plane_dict): 
			plane_dict[icao] = [date_time_local, "", plane_lat, plane_lon, elevation, distance, bearing, angle, "", "", ""]
		else:
			#
			# figure out if plane is approaching/holding/receding
			#
			if (distance < plane_dict[icao][5]):
				plane_dict[icao][9] = "APPROACHING"
				plane_dict[icao][10] = distance
			elif (distance > plane_dict[icao][5]):
				plane_dict[icao][9] = "RECEDING"
			else:
				plane_dict[icao][9] = "HOLDING"

			if (plane_dict[icao][10] == ""):
				plane_dict[icao][10] = distance

			plane_dict[icao][0] = date_time_local
			plane_dict[icao][2] = plane_lat
			plane_dict[icao][3] = plane_lon
			plane_dict[icao][4] = elevation 
			plane_dict[icao][5] = distance 
			plane_dict[icao][6] = bearing 
			plane_dict[icao][7] = angle 

	#
	# if matched record between type 1/3 occurs, log stats to stdout and also email if entering/leaving detection zone
	#
	if ((type == "1" or type == "3") and (icao in plane_dict and plane_dict[icao][1] != "" and plane_dict[icao][2] != "")):
		if (plane_dict[icao][8] == ""):
			plane_dict[icao][8] = "LINKED!"

		plane_log = date_time_iso + "," + icao +"," + str(plane_dict[icao][1]) + "," + str(plane_dict[icao][2]) + "," + str(plane_dict[icao][3]) + "," + str(plane_dict[icao][4]) + "," + str(plane_dict[icao][5]) + "," + str(plane_dict[icao][6]) + "," + str(plane_dict[icao][7])
		gmail_log = date_time_iso + " ICAO=" + icao + " FLIGHT=" + str(plane_dict[icao][1]) + " LATITUDE=" + str(plane_dict[icao][2]) + "°" + " LONGITUDE=" + str(plane_dict[icao][3]) + "°" + " ELEVATION=" + str(plane_dict[icao][4]) + elevation_units + " DISTANCE=" + str(plane_dict[icao][5]) + distance_units + " AZIMUTH=" + str(plane_dict[icao][6]) + "°" + " ALTITUDE=" + str(plane_dict[icao][7]) + "°"
		print plane_log

		#
		# if plane enters detection zone, send email and begin history capture
		#
		if (plane_dict[icao][5] <= limit_distance and plane_dict[icao][8] != "ENTERING"):
			plane_dict[icao][8] = "ENTERING"
			plane_hist[icao] = [plane_log.split(",")]
			gmail_subject = 'Subject:ALERT: Aircraft Entering Dectection Zone: ' + str(plane_dict[icao][1]) + ' ' + str(plane_dict[icao][5])  + ' ' + distance_units
			gmail_body = gmail_log + '\n\n' + 'http://flightaware.com/live/flight/' + str(plane_dict[icao][1])
			send_gmail(gmail_send_user, gmail_recv_user, gmail_pwd, gmail_subject, gmail_body)

		#
		# if plane still within detection zone, add to history capture
		#
		if (plane_dict[icao][5] <= limit_distance and plane_dict[icao][8] == "ENTERING"):
			plane_hist[icao].append(plane_log.split(","))

		#
		# if plane leaves detection zone, generate email and include history capture
		#
		if (plane_dict[icao][5] > limit_distance and plane_dict[icao][8] == "ENTERING"):
			plane_dict[icao][8] = "LEAVING"

			gmail_subject = 'Subject:ALERT: Aircraft Leaving Dectection Zone: ' + str(plane_dict[icao][1]) + ' ' + str(plane_dict[icao][5])  + ' ' + distance_units
			gmail_body = gmail_log + '\n\n' + 'http://flightaware.com/live/flight/' + str(plane_dict[icao][1]) + '\n\n'

			#
			# mark plane history record(s) of closest approach
			#
			for hist_entry in plane_hist[icao]:
				if (str(plane_dict[icao][10]) == str(hist_entry[6])):
					gmail_body = gmail_body + ','.join(hist_entry) + ' *** CLOSEST APPROACH ***' + '\n'
				else:
					gmail_body = gmail_body + ','.join(hist_entry) + '\n'
			del plane_hist[icao]
			gmail_body = gmail_body + '\nClosest approach: ' + str(plane_dict[icao][10]) + distance_units
			send_gmail(gmail_send_user, gmail_recv_user, gmail_pwd, gmail_subject, gmail_body)
