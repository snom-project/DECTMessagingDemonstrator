#!/bin/bash
while [ 1 ]; do
  curl -L --write-out '%{http_code}' --silent --output /dev/null -i 127.0.0.1:8081/location
  error=$?
  #echo $error
  if [ $error !=  0 ]; then
    echo 'failed, restart' 
    pkill -f DECTMessagingViewer.py 
    # restart 
    python3 DECTMessagingViewer.py &
  else
    echo 'OK' 
  fi
  sleep 10
done
