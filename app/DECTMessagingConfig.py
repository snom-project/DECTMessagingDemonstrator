# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
import io, socket

def get_local_ip():
    local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        local_socket.connect(('10.255.255.255', 1))
        local_ip = local_socket.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        local_socket.close()
    return local_ip

# disbale actions entirely. 
ACTIONS = True
# actions only for TAGs
KNX_ACTION = True


PHONE_IP = '192.168.178.20'
PHONE_IP = '192.168.178.20'

XML_SERVER_IP = '192.168.178.25'
XML_SERVER_IP = '10.110.16.101'
# results in localhost on raspi
XML_SERVER_IP = get_local_ip()

# knx ip
KNX_SERVER_IP = '192.168.178.53'
KNX_SERVER_IP = '10.110.16.112'

# ULE server IP needs a real IP - not localhost. It is used on web browsers and minibrowser
ULE_SERVER_IP = '192.168.188.126'


DECT_MESSAGING_VIEWER_IP_AND_PORT = '127.0.0.1:8081'
DECT_MESSAGING_VIEWER_URL = f'http://{DECT_MESSAGING_VIEWER_IP_AND_PORT}/en_US'

LED_OFFSET = 37 # snomD735
OLD_TAG_STATE = ['holding', 'holding', 'holding', 'holding', 'holding', 
                    'holding', 'holding', 'holding', 'holding', 'holding',
                    'holding', 'holding', 'holding', 'holding', 'holding',
                    'holding', 'holding', 'holding', 'holding', 'holding',
                    ]
TAG_NAME_DICT = { "000413BA0029" : "Kaffeemuehle",
                    "000413BA0059" : "Bild",
                    "000413BA00E4" : "Laptop",
                    "000413BA0021" : "Defi",
                    "000413BA001F" : "Oma", 
                }
WAVE_URL = f'http://{XML_SERVER_IP}/IO/test1.wav'

HTTP_D7DIR = 'D7C_XML'
HTTP_ROOT = f'/var/www/html/{HTTP_D7DIR}'

KNX_GATEWAY_URL = f'http://{KNX_SERVER_IP}:1234'
GATEWAY_URL = f'http://{KNX_SERVER_IP}:8000'
ULE_GATEWAY_URL = f'http://{ULE_SERVER_IP}:8881'
