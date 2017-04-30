#!/usr/bin/env bash

# start sweetiewatch
echo "Starting sweetiewatch..."
echo '********************************************************************************' >> data/sweetiewatch.log
echo "Starting log at" `date '+%Y-%m-%d %H:%M:%S'` >> data/sweetiewatch.log
echo '********************************************************************************' >> data/sweetiewatch.log
python sweetiewatch.py >> data/sweetiewatch.log 2>&1 &
# We wait a few seconds before starting sweetiebot to make sure the jabber server picks it up as running second.
# Annoyingly, ejabberd seems to throw away all our carefully-set resource priorities and just delivers
# PMs to whichever client connected most recently, so make sure that's sweetiebot.
echo "... done. Pausing"
sleep 5
echo "Starting sweetiebot..."
echo '********************************************************************************' >> data/sweetiebot.log
echo "Starting log at" `date '+%Y-%m-%d %H:%M:%S'` >> data/sweetiebot.log
echo '********************************************************************************' >> data/sweetiebot.log
python sweetiebot.py >> data/sweetiebot.log 2>&1 &
echo "... done. Waiting for sweetiebot to quit..."
# wait for bot to exit before exiting script
wait %1
echo "Sweetiebot ended, cleaning up remaining jobs..."
# kill sweetiewatch instead of leaving it lying around
kill $(jobs -p)
echo "... done. Exiting"
