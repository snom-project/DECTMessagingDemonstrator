# DectMessagingDemonstrator
Simple message server for snom Multicell DECT M700, M900

build with:
docker build -t snommd .

run with:
sudo docker run -dit --restart unless-stopped -p 10300:10300/udp -p 8081:8081 snommd 


1. start the viewer
python DECTMessagingViewer.py 

DECTMessagingViewer listens on port 8081 on localhost 
check if Viewer is running
http://localhost:8081/


2. start the messaging server
python DECTMessagingServer.py 10300

Messaging server is listening on port 10300 from all incoming Base IPs. 

Multicell Base configuration 

![Alt text](doc/images/base-config.jpg?raw=true "Base Configuration")
