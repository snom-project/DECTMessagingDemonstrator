#!/bin/bash

# turn on bash's job control
set -m

/usr/local/bin/sqlite_web --host 0.0.0.0 DB/DECTMessaging.db &

# Start the Viewer process and put it in the background
python ./DECTMessagingViewer.py &

sleep 5

# Start the Messaging Server process
python -u DECTMessagingServer.py 10300

# now we bring the primary process back into the foreground
# and leave it there
fg %1
