#!/bin/bash

# turn on bash's job control
set -m

# Start the Viewer process and put it in the background
python ./DECTMessagingViewer.py &

sleep 5

# Start the Messaging Server process
python -u DECTMessagingServer.py 10300

# now we bring the primary process back into the foreground
# and leave it there
fg %1
