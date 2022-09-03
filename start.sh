#!/bin/bash

# turn on bash's job control
set -m

# Start the Viewer process and put it in the background
python ./DECTMessagingViewer.py &

sleep 10 

/usr/local/bin/sqlite_web -p 8088 --host 0.0.0.0 DB/DECTMessaging.db &

# Start the Messaging Server process
python -u DECTMessagingServer.py 10300

# now we bring the primary process back into the foreground
# and leave it there
#fg %1
