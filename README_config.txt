''' 
Deployment steps 
1. clone got repo from 
https://github.com/snom-project/DECTMessagingDemonstrator

2. edit action.py in app directory 
change Server IPs etc to suit your current deployment 

3. use a launcher like this and add its launch on server reboot
#!/bin/bash
sleep 15

echo "System rebooted, DECT Messaging Server launcher running..."

cd /usr/local/DECTMessagingDemonstrator/DECTMessagingDemonstrator/app

echo "Starting DECT Messaging Viewer ..."
/usr/bin/python3 DECTMessagingViewer.py </dev/null >/dev/null 2>&1 &
 
echo "Starting Corona Room Checker ..."
/usr/bin/python3 snomRoomCapacity.py </dev/null >/dev/null 2>&1 &

# no longer supported. Air sensor not existing
#echo "Starting Snom Air ..."
#/usr/bin/python3 DxSnomGateway.py </dev/null >/dev/null 2>&1  &

echo "Starting DECT Messaging Server ..."
/usr/bin/python3 DECTMessagingServer.py 10300 </dev/null >/dev/null 2>&1 &

echo "Starting DB Viewer on 8080 ..."
/usr/local/bin/sqlite_web --host 0.0.0.0 DB/DECTMessaging.db &


echo "Starting DECT ULE Server ... via hancmbs service"
pushd /usr/local/opend/openD/dspg/base/tools
#./cmbs_tcx -usb -han -nomenu &
sleep 1
popd

echo "Starting DECT ULE snom app with MQTT support..."
pushd /usr/local/opend/openD/dspg/base/ule-hub
python3 han_app_mqtt.py &  
popd

4. reboot server and check if all http views are reachable.
e.g. 
local DECT Messaging DB
http://10.110.16.63:8080/
DECT Messaging Viewer
http://10.110.16.63:8081/en_US/ 
'''

### DO NOT EDIT HERE. JUST AN EXAMPLE. EDIT IN app/action.py
# disbale actions entirely. 
ACTIONS = True

# IP of the D735 to receive TAG info on D7C screen and LED
PHONE_IP = '10.110.16.102'
# the server IP, where the phone xml can be pulled via http
XML_SERVER_IP = '10.110.16.101'
# the server IP, where the KNXGW and DECTMessagingServer is located. Mostly identical to XML server ip 
# rasperry PI
SERVER_IP = XML_SERVER_IP
# Messaging Viewer. Use localhost in case it is on the same server
DECT_MESSAGING_VIEWER_IP_AND_PORT = '127.0.0.1:8081'
DECT_MESSAGING_VIEWER_URL = 'http://{DECT_MESSAGING_VIEWER_IP_AND_PORT}/en_US/'

# the server www subdir where all phone xml gets stores
HTTP_D7DIR = 'D7C_XML'
# local http root of the current server
HTTP_ROOT = f'/var/www/html/{HTTP_D7DIR}'

# LEDs on extension keypads starts with different idxs per phone type
LED_OFFSET = 37 # snomD735

# TAGs should trigger actions only on state change. State change needs previous OLD state to change from
# This is a simple start state for couple of TAGs which records the last state in memory
OLD_TAG_STATE = ['holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still', 
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    ]
# TAGs have terible MAC address "names", here we have a simple DICT to translate TAG mac to clear name
# in case TAG is not in the DICT "not found" will be the default name
TAG_NAME_DICT = { "000413BA0029" : "Kaffeemuehle",
                  "000413BA0059" : "Bild",
                  "000413BA0059" : "Laptop",
                  "000413BA0021" : "Defi",
                }
# phone can make noise on alarm. Here is the wave for a soft ding. The file must be present on the server!
WAVE_URL = f'http://{XML_SERVER_IP}/{D7C_XML}/test1.wav'

