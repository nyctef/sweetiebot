#!/usr/bin/env bash

while true
do

echo "Starting sweetiebot..."
echo '********************************************************************************' >> data/sweetiebot.log
echo "Starting log at" `date '+%Y-%m-%d %H:%M:%S'` >> data/sweetiebot.log
echo '********************************************************************************' >> data/sweetiebot.log
python sweetiebot.py 2>&1 | tee -a data/sweetiebot.log

echo "...Sweetiebot exited: pausing..."
sleep 10
echo "and looping..."

done
