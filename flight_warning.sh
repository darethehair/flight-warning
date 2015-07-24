#!/bin/bash
#
# Primary bash script for flight_warning system.
#
# Intended to invoke flight_warning.py python mainline from 'dump1090' feed.
# Some logging of intercepted/translated ADS-B records are sent/appended to standard output.
# Reason for logging to '/tmp' file system is to avoid SD card corruption on Raspberry Pi.

nc localhost 30003 | python /usr/local/bin/flight_warning.py >> /tmp/flight_warning.out
