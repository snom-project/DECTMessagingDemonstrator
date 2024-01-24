# DectMessagingDemonstrator
Simple message server for snom Multicell DECT M700, M900

install with:
git clone https://github.com/snom-project/DECTMessagingDemonstrator.git --config core.autocrlf=input

Note: --config core.autocrlf=input must be used on windows based docker versions to store the repository locally with Unix style line endings!

run inside DECTMessagingDemonstrator folder:
**git submodule update --init --recursive**

fully automated build and run:
**source runAll.sh**

***
Build step by step:
build with:
docker build -t snommd .

run with:
sudo docker run -dit --restart unless-stopped -p 10300:10300/udp -p 8081:8081 snommd 

In case your are not using docker:
make sure you install all packages requested in docker.
A script to install all the necessary packages you can run in your python environment.

source install_packages.sh

***
1. start the viewer in app directory:

python DECTMessagingViewer.py 

DECTMessagingViewer listens on port 8081 on localhost 

check if Viewer is running

http://localhost:8081/


2. start the messaging server in app directory

python DECTMessagingServer.py 10300

Messaging server is listening on port 10300 from all incoming Base IPs. 

Multicell Base configuration 
![alt text](https://github.com/snom-project/DECTMessagingDemonstrator/blob/master/app/doc/SampleBaseConfig.png?raw=true)

