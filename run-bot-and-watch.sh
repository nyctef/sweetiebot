#!/usr/bin/env bash

# start sweetiewatch
echo "starting sweetiewatch"
python sweetiewatch.py >> data/sweetiewatch.log 2>&1 &
# We wait a few seconds before starting sweetiebot to make sure the jabber server picks it up as running second.
# Annoyingly, ejabberd seems to throw away all our carefully-set resource priorities and just delivers
# PMs to whichever client connected most recently, so make sure that's sweetiebot.
echo "pausing"
sleep 5
echo "starting sweetiebot"
python sweetiebot.py >> data/sweetiebot.log 2>&1 &
echo "sweetiebot started"
# wait for bot to exit before exiting script
wait %1
echo "sweetiebot ended, cleaning up"
# kill sweetiewatch instead of leaving it lying around
kill $(jobs -p)
echo "remaining jobs killed"
