#!/bin/bash
#
# Bash script to determine antenna limits for flight_warning system.
#
# Intended to parse the flight_warning system log for the most distance aircraft position detections in 360 degree directions from antenna.
# This creates a KML file that can be used by the 'dump1090' Google Map as an overlay.
# Reason for logging to '/tmp' file system is to avoid SD card corruption on Raspberry Pi.

awk -F, -f /usr/local/bin/flight_warning.awk /tmp/flight_warning.out | sort -g | awk -F, '{print $4 "," $3}' | /usr/local/bin/csv2kml.sh > /tmp/flight_warning_limits.kml
cp /tmp/flight_warning_limits.kml /usr/share/dump1090/public_html
