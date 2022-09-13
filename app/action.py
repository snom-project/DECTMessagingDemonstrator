# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
from gevent import monkey; monkey.patch_all()
import gevent

import logging
import requests

logger = logging.getLogger('DMAction')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# disbale actions entirely. 
ACTIONS = True

PHONE_IP = '10.110.16.102'
XML_SERVER_IP = '10.110.16.63'
SERVER_IP = XML_SERVER_IP

DECT_MESSAGING_VIEWER_IP_AND_PORT = '127.0.0.1:8081'
DECT_MESSAGING_VIEWER_URL = f'http://{DECT_MESSAGING_VIEWER_IP_AND_PORT}/en_US'

LED_OFFSET = 37 # snomD735
OLD_TAG_STATE = ['holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still', 
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    'holding_still', 'holding_still', 'holding_still', 'holding_still', 'holding_still',
                    ]
TAG_NAME_DICT = { "000413BA0029" : "Kaffeemuehle",
                    "000413BA0059" : "Bild",
                    "000413BA0059" : "Laptop",
                    "000413BA0021" : "Defi",
                }
WAVE_URL = f'http://{XML_SERVER_IP}/IO/test1.wav'

HTTP_D7DIR = 'D7C_XML'
HTTP_ROOT = f'/var/www/html/{HTTP_D7DIR}'

KNX_GATEWAY_URL = f'http://{SERVER_IP}:1234'
GATEWAY_URL = f'http://{SERVER_IP}:8000'

def send_stolen_alarm(handsets_list):
    for elem in handsets_list:
        # send alarm to all handsets - base_connection is needed from the Devices table
        logger.info(f'send alarm to {elem["account"]} on base connection {elem["base_connection"]}' )
        # fire knx action(s)
        #logger.info(f'fire knx action for {elem["account"]},{elem["bt_mac"]} seen by M9B:{elem["beacon_gateway_IPEI"]}' )
        #KNX_gateway.fire_KNX_action(elem["bt_mac"], elem["beacon_gateway_IPEI"], "1")
        # its always proximity !=0 here.
        #if elem["proximity"] != '0':
            # red light
        #    ULE_gateway.fire_KNX_action(elem["bt_mac"], elem["beacon_gateway_IPEI"], '0')
        
        # send alarm to handset

        message = [
            {"name": elem["account"],    "account": elem["account"]},
            {"name": "MessageTextarea1", "account": "Alert near %s, %s moved!" % (elem["beacon_gateway_name"], TAG_NAME_DICT.get(elem["bt_mac"],"not found"))},
            {"name": "SelectPrio",       "account": "1"}, # highest
            {"name": "SelectConfType",   "account": "2"}, # with confirmation
            {"name": "SelectMsgType",    "account": "0"}, # use 100 as reference
            ]

        # notify the user with alarm.
        try:
            # send btmacs updated data back to viewer.
            print('alarm red sent:: %s' % message)
            _r = requests.post(f'{DECT_MESSAGING_VIEWER_URL}/alarm', json=message)
        except requests.exceptions.Timeout:
            logger.exception("Timeout Error location:")


def send_returned_alarm(handsets_list):
    for elem in handsets_list:
        # send alarm to all handsets - base_connection is needed from the Devices table
        logger.info(f'send alarm to {elem["account"]} on base connection {elem["base_connection"]}' )
        # fire knx action(s)
        #logger.info(f'fire knx action for {elem["account"]},{elem["bt_mac"]} seen by M9B:{elem["beacon_gateway_IPEI"]}' )
        #KNX_gateway.fire_KNX_action(elem["bt_mac"], elem["beacon_gateway_IPEI"], "1")
        # its always proximity !=0 here.
        #if elem["proximity"] != '0':
            # red light
        #    ULE_gateway.fire_KNX_action(elem["bt_mac"], elem["beacon_gateway_IPEI"], '0')
        
        # send alarm to handset

        message = [
            {"name": elem["account"],    "account": elem["account"]},
            {"name": "MessageTextarea1", "account": "%s near %s save" % (TAG_NAME_DICT.get(elem["bt_mac"],"not found"), elem["beacon_gateway_name"])},
            {"name": "SelectPrio",       "account": "7"}, # lowest
            {"name": "SelectConfType",   "account": "0"}, # no confirmation
            {"name": "SelectMsgType",    "account": "0"}, # use 100 as reference
            ]

        # notify the user with alarm.
        try:
            # send btmacs updated data back to viewer.
            logger.debug('alarm green sent:: %s', message)
            _r = requests.post(f'{DECT_MESSAGING_VIEWER_URL}/en_US/alarm', json=message)
        except requests.exceptions.Timeout:
            logger.exception("Timeout Error location (send_returned_alarm):")

    
def action_on_TAG_data(tag, idx, all_devices):
    global PHONE_IP
    global XML_SERVER_IP
    global LED_OFFSET
    global OLD_TAG_STATE
    #logger.debug("action_on_TAG_data idx=%s:%s",idx,device)

    if not ACTIONS:
        return True

    try: 
        if OLD_TAG_STATE[int(idx)] != tag['proximity']:
            OLD_TAG_STATE[int(idx)] = tag['proximity']
            logger.debug(OLD_TAG_STATE)
            name = tag['account']
    
            # send a colored led and label to key
            # send alarm to available handsets
            if tag['proximity'] != 'holding_still':
                color = 'red'
                effect = 'blinkfast'
                label = f'{tag["beacon_gateway_name"]}: {TAG_NAME_DICT.get(tag["bt_mac"],"not found")} weg'
                #send red alarm
                handset_list = [d for d in all_devices if d['device_type'] == "handset" and d['beacon_gateway'] == tag["beacon_gateway"] ]
                send_stolen_alarm(handset_list)
            else:
                color = 'green'
                effect = 'on'
                label = f'{tag["beacon_gateway_name"]}: {TAG_NAME_DICT.get(tag["bt_mac"],"not found")} da'
                #send green alarm
                handset_list = [d for d in all_devices if d['device_type'] == "handset" and d['beacon_gateway'] == tag["beacon_gateway"] ]
                send_returned_alarm(handset_list)
            
            xml_payload = f'''<?xml version="1.0" encoding="UTF-8"?>
    <SnomIPPhoneText>
    <fetch mil="100">snom://mb_exit</fetch>
    <led number="{int(idx) + LED_OFFSET}" color="{color}">{effect}</led>
    </SnomIPPhoneText>  
                            '''
            logger.debug("send to phone: %s",xml_payload)

            # save xml to file 
            f = open(f"{HTTP_ROOT}/TAG{name}_{idx}.xml", "w")
            f.write(xml_payload)
            f.close()

            # send to phone
            request = f'http://{PHONE_IP}/minibrowser.htm?url=http://{XML_SERVER_IP}/{HTTP_D7DIR}/TAG{name}_{idx}.xml'
            logger.debug("send to phone: %s",request)
            request2 = f'http://{PHONE_IP}/settings.htm?settings=save&fkey_label{int(idx) + LED_OFFSET - 5}={label}&fkey_short_label{int(idx) + LED_OFFSET -5}={label}'
            logger.debug("send to phone: %s",request2)

            try:
                _response = requests.get(request2, timeout=5)
                logger.debug(_response)
                _response = requests.get(request, timeout=5)
                logger.debug(_response)
            except requests.exceptions.Timeout:
                logger.exception("Timeout Error action_on_TAG_data:")
        else:
            #print(f'TAG {idx} didnt change')
            color = 'grey'
        return True
    except:
        #print(f'index {idx} of {OLD_TAG_STATE} out of range?')
        logger.error(f'index {idx} of {OLD_TAG_STATE} out of range?')
        return False
