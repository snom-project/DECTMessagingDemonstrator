# DectMessagingDemonstrator
Simple message server for snom Multicell DECT M700, M900

1. start the viewer
python DECTMessagingViewer.py 

DECTMessagingViewer listens on port 8080 on localhost 
check if Viewer is running
http://localhost:8080/


2. start the messaging server
python DECTMessagingServer.py  1300:0.0.0.0:1300

Messaging server is listening on port 1300 from all incomning Base IPs. 

Multicell Base configuration 

![Alt text](doc/images/base-config.jpg?raw=true "Base Configuration")
