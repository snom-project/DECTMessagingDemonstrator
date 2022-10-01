# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-

# disbale actions entirely. 
ACTIONS = True

PHONE_IP = '192.168.178.20'
XML_SERVER_IP = '192.168.178.25'
SERVER_IP = XML_SERVER_IP

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

KNX_GATEWAY_URL = f'http://{SERVER_IP}:1234'
GATEWAY_URL = f'http://{SERVER_IP}:8000'