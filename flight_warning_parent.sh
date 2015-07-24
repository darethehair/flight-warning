#!/bin/bash
#
# Parent bash script for flight_warning system.
#
# Intended to automatically restart the main bash/python scripts if they crash for whatever reason.
# Can be made to automatically start during reboot by adding to crontab schedule e.g
# 
#	@reboot /usr/local/bin/flight_warning_parent.sh
#

logger -t $0 "starting flight_warning.sh..."
until /usr/local/bin/flight_warning.sh; do
	logger -t $0 "flight_warning.sh crashed so restarting it..."
    	sleep 1
done
