#!/bin/bash
echo "-------- start ssfd ----------"
killall -9 ssfd
pushd /home/ubuntu/ssf/ssf-linux-x86_64-3.0.0
./ssfd -p 10000&
popd
echo "-------- start docker ----------"
sudo docker run -dit --restart unless-stopped -p 8088:8088 -p 10300:10300/udp -p 8081:8081 snommd 
