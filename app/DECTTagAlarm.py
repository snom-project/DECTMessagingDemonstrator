# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
import requests
import asyncio
import logging
import time

from DB.DECTMessagingDb import DECTMessagingDb

# disbale actions entirely. 
ACTIONS = True

# could be done by importing 
# from DECTMessagingConfig import *

PHONE_IP = '192.168.178.20'
PHONE_IP = '10.110.16.59'
XML_SERVER_IP = '192.168.178.25'
SERVER_IP = XML_SERVER_IP

DECT_MESSAGING_VIEWER_IP_AND_PORT = '127.0.0.1:8081'
DECT_MESSAGING_VIEWER_URL = f'http://{DECT_MESSAGING_VIEWER_IP_AND_PORT}/en_US'

LED_OFFSET = 37 # snomD735
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

from functools import wraps
def background(f):
    try:
        @wraps(f)
        def wrapped(*args, **kwargs):
            loop = asyncio.get_event_loop()
            if callable(f):
                logger.debug("function %s started in background.", str(f))
                return loop.run_in_executor(None, f, *args, **kwargs)
            else:
                raise TypeError('Task must be a callable')   
        return wrapped
    except:
        logger.exception('background task %s failed!', str(f))

@background
def send_stolen_alarm(handsets_list, tag):
    print('entered send_stolen_alarm')
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
            {"name": "MessageTextarea1", "account": "Alert near %s, %s moved!" % (elem["beacon_gateway_name"], TAG_NAME_DICT.get(tag["bt_mac"],"not found"))},
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

@background
def send_returned_alarm(handsets_list, tag):
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
            {"name": "MessageTextarea1", "account": "%s near %s save" % (TAG_NAME_DICT.get(tag["bt_mac"],"not found"), elem["beacon_gateway_name"])},
            {"name": "SelectPrio",       "account": "7"}, # lowest
            {"name": "SelectConfType",   "account": "0"}, # no confirmation
            {"name": "SelectMsgType",    "account": "0"}, # use 100 as reference
            ]

        # notify the user with alarm.
        try:
            # send btmacs updated data back to viewer.
            logger.debug('alarm green sent:: %s', message)
            _r = requests.post(f'{DECT_MESSAGING_VIEWER_URL}/alarm', json=message)
        except requests.exceptions.Timeout:
            logger.exception("Timeout Error location (send_returned_alarm):")


@background
def send_action_to_phone(name, idx, color, effect, label):
    print('entered send_action_to_phone')

    logger.debug('send_action_to_phone: %s, %s, %s, %s', idx, color, effect, label)

    xml_payload = f'''<?xml version="1.0" encoding="UTF-8"?>
<SnomIPPhoneText>
<fetch mil="100">snom://mb_exit</fetch>
<led number="{int(idx) + LED_OFFSET}" color="{color}">{effect}</led>
</SnomIPPhoneText>  
                    '''
    logger.debug("send to phone: %s",xml_payload)

    # save xml to file
    try:
        f = open(f"{HTTP_ROOT}/{name}_{idx}.xml", "w")
        f.write(xml_payload)
        f.close()
    except:
        logger.debug("file could not be created: %s",f"{HTTP_ROOT}/{name}_{idx}.xml")
    
    #urls = []
    # send to phone
    request = f'http://{PHONE_IP}/minibrowser.htm?url=http://{XML_SERVER_IP}/{HTTP_D7DIR}/TAG{name}_{idx}.xml'
    logger.debug("send to phone: %s",request)
    request2 = f'http://{PHONE_IP}/settings.htm?settings=save&fkey_label{int(idx) + LED_OFFSET - 5}={label}&fkey_short_label{int(idx) + LED_OFFSET -5}={label}'
    logger.debug("send to phone: %s",request2)
    
    '''
    urls.append(request)
    urls.append(request2)
    rs = (grequests.get(u) for u in urls) 
    '''
    try:
        #print(grequests.map(rs))
        _response = requests.get(request2, timeout=5)
        logger.debug(_response)
        _response = requests.get(request, timeout=5)
        logger.debug(_response)        
    except requests.exceptions.Timeout:
        logger.exception("Timeout Error action_on_TAG_data:")


def action_on_TAG_data(tag, idx, all_devices):
    global PHONE_IP
    global XML_SERVER_IP
    global LED_OFFSET
    #logger.debug("action_on_TAG_data idx=%s:%s",idx,device)

    if not ACTIONS:
        return True

    try: 
        if str(tag['tag_last_state']) != str(tag['proximity']):
            # update the device old state in the DB
            msgDb.update_with_key_db(account=tag['account'], 
                                    tag_last_state=tag['proximity']
            )
            logger.debug("TAG old_state changed to:%s", str(tag['proximity']))
            name = tag['account']
    
            # send a colored led and label to key
            # send alarm to available handsets
            if str(tag['proximity']) == 'moving':
                color = 'red'
                effect = 'blinkfast'
                label = f'{tag["beacon_gateway_name"]}: {TAG_NAME_DICT.get(tag["bt_mac"],"not found")} weg'
                #send red alarm
                handset_list = [d for d in all_devices if d['device_type'] == "handset" and d['beacon_gateway'] == tag["beacon_gateway"] ]
                send_stolen_alarm(handset_list, tag)
            elif str(tag['proximity']) == 'holding':
                color = 'green'
                effect = 'on'
                label = f'{tag["beacon_gateway_name"]}: {TAG_NAME_DICT.get(tag["bt_mac"],"not found")} da'
                #send green alarm
                handset_list = [d for d in all_devices if d['device_type'] == "handset" and d['beacon_gateway'] == tag["beacon_gateway"] ]
                send_returned_alarm(handset_list, tag)
            else:
                logger.debug("no action state:%s", str(tag['proximity']))

            send_action_to_phone(name, idx, color, effect, label)

        else:
            #print(f'TAG {idx} didnt change')
            color = 'grey'
            return False

        return True
    except:
        #print(f'index {idx} of {OLD_TAG_STATE} out of range?')
        logger.exception(f'something unkown has happened')
        return False


# prepare logger
logger = logging.getLogger('DECTTagAlarm')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

# get access to the DB
# DB reuse and type
ODBC=False
INITDB=False
msgDb = DECTMessagingDb(odbc=ODBC, initdb=INITDB)

DEVICES = []

if __name__ == "__main__":
    while True:
        # get all devices for handset alarming
        DEVICES = msgDb.read_devices_db()
        # filter TAGs 
        tagDevices = [d for d in DEVICES if d['device_type'] == "BTLETag"]
        
        for idx, tag in enumerate(tagDevices):
            #logger.debug('working on TAG:%s', tag)
            logger.debug('new:%s->old:%s', tag['proximity'], tag['tag_last_state'])
        
            # check and execute scheduled task, return true on action success
            if not action_on_TAG_data(tag, idx, DEVICES):
                logger.debug('no state change on %s', idx)

        # do not burn cpu!
        time.sleep(10)
        