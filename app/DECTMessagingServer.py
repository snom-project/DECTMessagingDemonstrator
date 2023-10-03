import pyproxy as pp
from lxml import etree as ET
import lxml.builder
import datetime
import schedule
import time
import socket
import requests

import socketserver



import json
import logging
import random

from mqtt.snomM900MqttClient import snomM900MqttClient

from colorama import init
init()
from colorama import Fore
from colorama import Style

# ASYNC processing
import gevent
#from gevent import monkey; monkey.patch_all()
import subprocess # it's usable from multiple greenlets now

from DB.DECTMessagingDb import DECTMessagingDb
from DECTKNXGatewayConnector import DECT_KNX_gateway_connector

from DECTMessagingConfig import *

# DB reuse and type
ODBC=False
INITDB=False
msgDb = DECTMessagingDb(beacon_queue_size=3, odbc=ODBC, initdb=INITDB)

#msgDb.delete_db()
viewer_autonomous = True

'''
class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        raw_data = self.request[0].strip()
        socket = self.request[1]
        #print("{} wrote:".format(self.client_address[0]))
        #print(data)
        #socket.sendto(data.upper(), self.client_address)

        amsg.m900_connection = self.client_address

        ## queue needs to know, where to send the answer
        ##         #socket.sendto(my_answer_xml, self.client_address)
        ## needs to be called from everywhere 
        ## a proper class send routine would do

        try:
            # quick check if data is valid missing
            xmldata = raw_data.decode('utf-8')
            print(xmldata)
            # process message
            #amsg.msg_process(xmldata)
            gevent.spawn(worker)
            q.put(xmldata)

            # yield to worker
            gevent.sleep(0)

        except:
            logger.warning("main: Message could not be understoood or unexpected error %s" % raw_data)
'''

class MSSeriesMessageHandler:
    """Main M700,M900 Messaging class

    This class implements parts of the message server functionality of an Alarm/SMS/Beacon system between a SnomM700, SnomM900 basestation (FP) and this message serber instance.
    The class processes messaging protocol XML messages received from base station via UDP.

    The class handles:
    - process SMS from handsets to MS
    - process SMS from handsets to handset
    - process alarms from handset to MS
    - send alarms from MS to the handset
    - process Beacon information

    Returns:
        XML message: Responses and Request defined in the protocol
    """
    # instead of sub class.
    from msg_response import msg_response
    from msg_request import msg_request

    namespace = '.' # not used
    # XPATH // means all occurences within the tree!
    msg_xpath_map = {
        'RESPONSE_TYPE_XPATH': "/response/@type",
        'REQUEST_TYPE_XPATH': "/request/@type",

        # snom message with json-data
        'SNOM_REQUEST_JSONDATA':          "/request[@type='json-data']/json-data/text()",
        'SNOM_REQUEST_JSONDATA_JOBTYPE':  "/request[@type='json-data']/jobtype/text()",


        'JOB_RESPONSE_STATUS_XPATH':     "/response[@type='job']/status/text()",

        'X_REQUEST_EXTERNALID_XPATH': "//externalid/text()",
        # RESPONSE
        'X_REQUEST_STATUS_XPATH':     "//status/text()",
        'X_REQUEST_STATUSINFO_XPATH': "//statusinfo/text()",

        'X_SENDERDATA_XPATH': "//senderdata",
        'X_ALARMDATA_XPATH':  "//alarmdata",
        'X_RSSIDATA_XPATH':   "//rssidata",
        'X_BEACONDATA_XPATH': "//beacondata",
        'X_JOBDATA_XPATH':    "//jobdata",

        'X_PERSONDATA_XPATH': "//persondata",
        'JOB_RESPONSE_PERSONDATA_ADDRESS_XPATH':    "//response[@type='job']//persondata//address/text()",

        'X_REQUEST_SYSTEMDATA_NAME_XPATH':       "//systemdata//name/text()",
        'X_REQUEST_SYSTEMDATA_DATETIME_XPATH':   "//systemdata//datetime/text()",
        'X_REQUEST_SYSTEMDATA_TIMESTAMP_XPATH':  "//systemdata//timestamp/text()",
        'X_REQUEST_SYSTEMDATA_STATUS_XPATH':     "//systemdata//status/text()",
        'X_REQUEST_SYSTEMDATA_STATUSINFO_XPATH': "//systemdata//statusinfo/text()",

        'LOGIN_REQUEST_LOGINDATA_STATUS_XPATH': "//request[@type='login']//logindata//status/text()",

        'ALARM_REQUEST_ALARMDATA_TYPE_XPATH':          "/request[@type='alarm']/alarmdata/type/text()",
        'ALARM_REQUEST_ALARMDATA_BEACONTYPE_XPATH':    "/request[@type='alarm']/beacondata/beacontype/text()",
        'ALARM_REQUEST_ALARMDATA_BROADCASTDATA_XPATH': "/request[@type='alarm']/beacondata/broadcastdata/text()",
        'ALARM_REQUEST_ALARMDATA_BDADDR_XPATH':        "/request[@type='alarm']/beacondata/bdaddr/text()",

        'ALARM_REQUEST_RSSIDATA_RFPI_XPATH':        "/request[@type='alarm']/rssidata/rfpi/text()",
        'ALARM_REQUEST_RSSIDATA_RSSI_XPATH':        "/request[@type='alarm']/rssidata/rssi/text()",

        'X_REQUEST_JOBDATA_STATUS_XPATH': "//jobdata//status/text()",
        'X_REQUEST_JOBDATA_PRIORITY_XPATH': "//jobdata/priority/text()",

        'JOB_REQUEST_JOBDATA_MESSAGE1_XPATH':      "//request[@type='job']//jobdata//messages//message1/text()",
        'JOB_REQUEST_JOBDATA_MESSAGE2_XPATH':      "//request[@type='job']//jobdata//messages//message2/text()",
        'JOB_REQUEST_JOBDATA_MESSAGEUUID_XPATH':   "//request[@type='job']//jobdata//messages//messageuui/text()",

        'JOB_REQUEST_PERSONDATA_ADDRESS_XPATH':    "//request[@type='job']//persondata//address/text()",
        'JOB_REQUEST_PERSONDATA_STATUS_XPATH':     "//request[@type='job']//persondata//status/text()",
        'JOB_REQUEST_PERSONDATA_STATUSINFO_XPATH': "//request[@type='job']//persondata//statusinfo/text()",

        'X_SENDERDATA_ADDRESS_XPATH': "//senderdata//address/text()",
        'X_SENDERDATA_NAME_XPATH':     "//senderdata//name/text()",
        'X_SENDERDATA_NAME_EXISTS_XPATH':     "//senderdata/name",

        'X_SENDERDATA_ADDRESS_IPEI_XPATH': "//senderdata/address[@type='IPEI']/text()",

        'X_SENDERDATA_LOCATION_XPATH': "//senderdata//location/text()",

        'X_BEACONDATA_EVENTTYPE_XPATH':     "//beacondata//eventtype/text()",
        'X_BEACONDATA_BEACONTYPE_XPATH':    "//beacondata//beacontype/text()",
        'X_BEACONDATA_BROADCASTDATA_XPATH': "//beacondata//broadcastdata/text()",
        'X_BEACONDATA_BDADDR_XPATH':        "//beacondata//bdaddr/text()",

        'ALARM_NAMESPACE_PREFIX': {'x': namespace}
    }

    def __init__(self, class_logger, devices=[]):
        self.logger = class_logger
        # use standard UDP port by default
        self.m900_connection = ('127.0.0.1', 1300)
        self.devices = devices
        self.btmacaddresses = []
        self.bt_mac = ''
        self.beacon_type = ''
        self.messageuui = ''

        E = lxml.builder.ElementMaker()
        self.RESPONSE = E.response
        self.REQUEST = E.request
        self.SYSTEMDATA = E.systemdata
        self.NAME = E.name
        self.DATETIME = E.datetime
        self.TIMESTAMP = E.timestamp
        self.STATUS = E.status
        self.STATUSINFO = E.statusinfo
        self.EXTERNALID = E.externalid

        self.JOBDATA = E.jobdata
        self.ALARMNUMBER = E.alarmnumber
        self.REFERENCENUMBER = E.referencenumber
        self.CALLBACKNUMBER = E.callbacknumber
        self.PRIORITY = E.priority
        self.FLASH = E.flash
        self.RINGS = E.rings
        self.CONFIRMATIONTYPE = E.confirmationtype
        self.MESSAGES = E.messages
        self.MESSAGE1 = E.message1
        self.MESSAGE2 = E.message2
        self.MESSAGEUUID = E.messageuui

        self.SENDERDATA = E.senderdata
        self.LOCATION = E.location

        self.PERSONDATA = E.persondata
        self.ADDRESS = E.address


    def is_TAG(self, btmac, beacon_type, uui):
        """Check if uuid is a TAG
           Altbeacon, example DFE707D0-- (2-C3A11B2) --951700087B1B39E10000000073
           2 = TAG
           C3A11B2=YYWWSSSSSS when converted in decimal

        Args:
            beacon_type (string): a=AltBeacon, i=iBeacon, e=EddyStone
            uui (string): uuid payload for beacon_type

        Returns:
            [boolean]: True, if TAG is detected
        """
        # only snom and RTX beacons have encoded uuids
        if btmac[0:6] == 'E4E112':
            logger.debug('Blukii TAG detected, type:{beacon_type} uui=%s', uui)
            return True

        if btmac[0:6] == 'E07DEA':
            logger.debug('Safectory TAG detected, type:{beacon_type} uui=%s', uui)
            return True

        if btmac[0:6] == '000413' or btmac[0:6] == '00087B':
            if beacon_type == "a":
                if uui[8] == '2':
                    logger.debug('Snom TAG detected, AltBeacon: uui=%s', uui)
                    return True
            if beacon_type == "i":
                # uuid='8b0ca750e7a74e14bd99095477cb3e772C1E1CA1'
                # 8b0ca750e7a74e14bd99095477cb3e77 relevant production data 2 C1E1CA1
                # 2 is TAG
                # last 8 characters 
                if uui[len(uui)-8] == '2' and uui != '00112233445566778899AABBCCDDEEFF22334455':
                    logger.debug('Snom TAG detected, iBeacon: uui=%s', uui)
                    return True
            # else
            
        return False


    '''
     Job:  <?xml version="1.0" encoding="UTF-8"?>
     <request version="20.3.18.2018" type="job">
     <externalid>1864588637</externalid>
     <systemdata>
     <name>M900</name>
     <datetime>2020-03-22 10:45:44</datetime>
     <timestamp>5e7733c8</timestamp>
     <status>1</status>
     <statusinfo>System running</statusinfo>
     </systemdata>
     <jobdata>
     <priority>0</priority>
     <messages>
     <message1></message1>
     <message2></message2>
     <messageuui>!BT;0004136323B9;p;i;FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF85FF00FF00;0;1;-74</messageuui>
     </messages>
     <status>0</status>
     <statusinfo></statusinfo>
     </jobdata>
     <senderdata>
     <address type="IPEI">0328D7830E</address>
     <location>M900</location>
     </senderdata>
     <persondata>
     <address>M9B200</address>
     </persondata>
     </request>
    '''
    def update_beacon(self, messageuui, senderaddress, personaddress):
        """Updates the received beacon data in the device list.

        Args:
            messageuui (string): <messageuui>!BT;0004136323B9;p;i;FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF85FF00FF00;0;1;-74</messageuui>

            senderaddress (string): M9B which received the beacon. e.g. <address type="IPEI">0328D7830E</address>

            personaddress (string): given Number/Name of the M9B generalSettings.alarmServerAddress. Not the name of the device sending the beacon!
        """
        # this is the sender of the beacon
        beacon_gateway = senderaddress

        #print('update_beacon')
        logger.debug('messageuui from %s:%s', beacon_gateway, messageuui)

        rssi = "-111"
        if messageuui.split(';',1)[0] == '!BT':
            _, bt_mac, _, beacon_type, uuid, d_type, proximity, rssi= messageuui.split(';')
        else:
            logger.warning('not a BT message')
            return False

        # rssi worse than 100 we discard radically, proximity can be 1 (inside), 2 (rssi change)  or 3 (state report)
        if proximity != '0' and int(rssi) < -100:
            logger.info("update_beacon: disregarding Beacon Info with rssi=%s", rssi)
            return False

        # Update device data
        matched_bt_mac = next((item for item in self.devices if item['bt_mac'] == bt_mac), False)
        # we record updated timestamps to identify stale devices
        current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")

        if not matched_bt_mac:
        # we found a new device

            # we see the device_type in the BT message
            if self.is_TAG(bt_mac, beacon_type, uuid):
                device_type_new = 'BTLETag'
                self.devices.append({'device_type': device_type_new, 'bt_mac': bt_mac, 'name': 'moving', 'account': 'Tag_%s' % bt_mac, 'rssi': rssi, 'uuid': uuid, 'beacon_type': beacon_type, 'proximity': 'moving', 'beacon_gateway' : beacon_gateway, 'beacon_gateway_name' : '', 'user_image': '/images/tag.png', 'device_loggedin' : '1', 'base_location': 'None', 'base_connection': self.m900_connection, 'last_beacon': 'Tag', 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime} )
                logger.debug("update_beacon: added Tag %s %s", bt_mac, uuid)
            else:
                # alt beacon M9b TX have payload default e.g. 001122334455667788990011223344556677889000
                # default 000102030405060708090A0B0C0D0E0F1011121300
                # we use only the common part for all beacon types
                if '1122334455667788990011223344' in uuid or '000102030405060708090A0B0C0' in uuid :
                    logger.debug("device is a M9B in TX mode")
                    M9B_beacon = True
                else:
                    M9B_beacon = False

                device_type_new = 'beacon'
                # add a new bt_mac
                self.devices.append({'device_type': device_type_new, 'bt_mac': bt_mac, 'name': 'M9B %s' % personaddress, 'account': bt_mac, 'rssi': rssi, 'uuid': uuid, 'beacon_type': beacon_type, 'proximity': proximity, 'beacon_gateway' : beacon_gateway, 'beacon_gateway_name' : '', 'user_image': '/images/beacon.png', 'device_loggedin' : '1', 'base_location': 'None', 'base_connection': self.m900_connection, 'last_beacon': 'beacon ping', 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime} )
                self.btmacaddresses.append({'account': bt_mac, 'bt_mac': bt_mac})
                if M9B_beacon:
                    logger.debug("added: M9B TX beacon  %s %s %s", personaddress, bt_mac, uuid)
                else:
                    logger.debug("added: beacon seen by M9B RX  %s %s %s", personaddress, bt_mac, uuid)

            # we have added a new device, now match it to process further
            matched_bt_mac = next((item for item in self.devices if item['bt_mac'] == bt_mac), False)
            if not matched_bt_mac:
                logger.error("FATAL: We have added a new device and cant match it.")

        # we found an already existing device
        else:
            # we see the device_type in the BT message
            if self.is_TAG(matched_bt_mac['bt_mac'], beacon_type, uuid):
                matched_bt_mac['device_type'] = 'BTLETag'
            else:
                # we should assume that device_type is already correctly set. 
                # in case it is an unknown beacon device, we leave beacon
                # in case we found a handset with matching BTLE address, we change the handset state
                if matched_bt_mac['device_type'] != 'beacon':
                    matched_bt_mac['device_type'] = 'handset'
            # M9B in TX mode
            if '1122334455667788990011223344' in uuid  or '000102030405060708090A0B0C0' in uuid:
                matched_bt_mac['device_type'] = 'beacon'

            matched_bt_mac['uuid'] = uuid
            matched_bt_mac['rssi'] = rssi
            matched_bt_mac['beacon_type'] = beacon_type
            # timestamp
            matched_bt_mac['time_stamp'] = current_datetime

            # check if address has changed. In this case do not Overwrite with Outside on old location
            #print('################', matched_bt_mac['beacon_gateway'], beacon_gateway, proximity)
            if (matched_bt_mac['beacon_gateway'] != beacon_gateway) and  proximity == '0' and False:
                # we have a new address already, this message is leave message from an old address
                # do nothing
                # IN CASE THE DEVICE IS STILL INSIDE IN ANOTHER M9B
                # THIS IS DISABLED: WE CANNOT GET ALL LEAVE MESSAGE BEACONS RECORDED.
                # we do not overide the device info but instead make sure we record the 0 Beacon
                # in the database by using proximity and gateway directly.
                print('%%%%%%%%%%%%% old leave message, ignore', matched_bt_mac)
                #matched_bt_mac['beacon_gateway'] = matched_bt_mac['beacon_gateway'] + ' left: ' + beacon_gateway
                # proximity stays the old inside
                #return True
            else:
                matched_bt_mac['proximity'] = proximity
                matched_bt_mac['beacon_gateway'] = beacon_gateway
                #print('update:', matched_bt_mac)

            # !!!TAG will toggle wildy for a while.!!!
            # fire action on beacon proximity
            if KNX_ACTION:
                KNX_gateway.fire_KNX_action(matched_bt_mac['bt_mac'], beacon_gateway, proximity)

            # Tags have their own state.
            if matched_bt_mac['device_type'] == 'BTLETag':
                # udpdate newly beacon and all Tags timstamps and states
                # TAGs switch beetween 0 and 1 for some time. Here, we detected a moving TAG already.
                matched_bt_mac['proximity'] = 'moving'
                self.update_tag_and_m9bs(matched_bt_mac)

                # Tags keep sending bursts and a final before they stop. We do not count the bursts
                # instead we assume that after the last burst in the next 30s nothing will come.
                # The Tag rests
                # each TAG has its own scheduler. 
                schedule.clear(f"TAGHold{matched_bt_mac['bt_mac']}")
                schedule.every(30).seconds.do(self.update_all_tags).tag(f"TAGHold{matched_bt_mac['bt_mac']}")


        # at this point we have appended a new device and have a matched_bt_mac

        # rssi change
        if proximity == '2' and matched_bt_mac:
            matched_bt_mac["rssi"] = rssi
            logger.debug("beacon rssi change received from M9B RX  rssi=%s", matched_bt_mac["rssi"])
        # rssi report
        if proximity == '3' and matched_bt_mac:
            matched_bt_mac["rssi"] = rssi
            logger.debug("beacon report received from M9B RX  rssi=%s", matched_bt_mac["rssi"])



        # translate IPEI into clear name
        beacon_gateway_name = beacon_gateway
        # translate m9bIPEI into locations..
        if msgDb:
            result = msgDb.read_gateway_db(beacon_gateway_IPEI=beacon_gateway, beacon_gateway_name='')
            if result:
                beacon_gateway_name = result[0]['beacon_gateway_name']
        else:
            m9bIPEI_description.get(beacon_gateway, str(beacon_gateway))
        matched_bt_mac['beacon_gateway_name'] = beacon_gateway_name

        # mqtt
        mqttc.publish_beacon(matched_bt_mac["bt_mac"], beacon_type, uuid, d_type, matched_bt_mac["proximity"], rssi, matched_bt_mac["name"], matched_bt_mac["beacon_gateway"])

        # record the beacon
        if msgDb:
            # update the full single device data. There might be a new device beacon
            msgDb.update_db(account=matched_bt_mac["account"],
                            device_type=matched_bt_mac['device_type'],
                            bt_mac=matched_bt_mac["bt_mac"],
                            name=matched_bt_mac["name"],
                            rssi=matched_bt_mac["rssi"],
                            uuid=matched_bt_mac["uuid"],
                            beacon_type=matched_bt_mac["beacon_type"],
                            proximity=matched_bt_mac["proximity"],
                            beacon_gateway=matched_bt_mac['beacon_gateway'],
                            beacon_gateway_name=matched_bt_mac["beacon_gateway_name"],
                            user_image = matched_bt_mac['user_image'],
                            device_loggedin = matched_bt_mac['device_loggedin'],
                            base_location = matched_bt_mac['base_location'],
                            base_connection = str(matched_bt_mac['base_connection']),
                            time_stamp=matched_bt_mac["time_stamp"], 
                            tag_time_stamp = matched_bt_mac['tag_time_stamp']
                            ) 

            # record the Beacon in the database by using proximity and gateway directly.
            msgDb.record_beacon_db(account=matched_bt_mac["account"],
                                   device_type=matched_bt_mac["device_type"],
                                   bt_mac=matched_bt_mac["bt_mac"],
                                   name=matched_bt_mac["name"],
                                   rssi=matched_bt_mac["rssi"],
                                   uuid=matched_bt_mac["uuid"],
                                   beacon_type=matched_bt_mac["beacon_type"],
                                   proximity=matched_bt_mac["proximity"],
                                   beacon_gateway=matched_bt_mac['beacon_gateway'],
                                   beacon_gateway_name=matched_bt_mac["beacon_gateway_name"],
                                   time_stamp=matched_bt_mac["time_stamp"]
                                   )
            msgDb.record_m9b_device_status_db(account=matched_bt_mac["account"],
                       bt_mac=matched_bt_mac["bt_mac"],
                       rssi=matched_bt_mac["rssi"],
                       uuid=matched_bt_mac["uuid"],
                       beacon_type=matched_bt_mac["beacon_type"],
                       proximity=matched_bt_mac["proximity"],
                       beacon_gateway_IPEI=matched_bt_mac['beacon_gateway'],
                       beacon_gateway_name=matched_bt_mac["beacon_gateway_name"],
                       time_stamp=matched_bt_mac["time_stamp"]
                       )
        return True


    def update_all_tags(self):
        """Scheduled function processes all TAGs and changes non-active to holding.

        Returns:
            [job]: schedule.CancelJob
        """
        current_timestamp = datetime.datetime.now()
        # update all moving devices in holding_still
        for d in self.devices:
            if d['device_type'] == 'BTLETag':
                current_state = d['name']
                old_timestamp = datetime.datetime.strptime(d['tag_time_stamp'], "%Y-%m-%d %H:%M:%S.%f")
                delta = current_timestamp - old_timestamp
                #print(d, 'delta', delta)
                if delta.total_seconds() > 20 and current_state == 'moving':
                    d['name'] = 'holding_still'
                    # special holding state, since TAG switches beetween 0 and 1 for some time.
                    d['proximity'] = 'holding'
                    d['tag_time_stamp'] = current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                    #print('found d:', d, current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"))
                    mqttc.publish_beacon(d["bt_mac"], "", "", "", d["proximity"], -0, d["name"], d["beacon_gateway"])
                    # Update the m9b tag status and device from moving for all gateways
                    msgDb.update_m9b_tag_status_db(bt_mac=d["bt_mac"], proximity=d["proximity"])
                    msgDb.update_single_device_db(d)
                    # !!! update the beacon status from moving for all affected entries? bt_mac !!!


        # the job has been called via schedule and needs to run only once.
        return schedule.CancelJob


    def update_tag_and_m9bs(self, tag_device):
        """Current device proximity will be changed into moving,
        clear_old_m9b_tag_status_db removes current TAG from all gateways,
        when TAG is older than 30s.
        Otherwise in-active TAGs stay forever within the gateway proximity.

        Args:
            tag_device (device DICT): current device

        Returns:
            [boolean]: True
        """
        #print(tag_device)
        bt_mac = tag_device["bt_mac"]
        # clear all older M9Bs holding this TAG, only leave the newest ones
        current_timestamp = datetime.datetime.now()
        target_timestamp = current_timestamp - datetime.timedelta(seconds=30)
        msgDb.clear_old_m9b_tag_status_db(bt_mac, target_timestamp)

        # get current state and timestamp
        current_state = tag_device['name']
        current_timestamp = datetime.datetime.now()
        old_timestamp = datetime.datetime.strptime(tag_device['tag_time_stamp'], "%Y-%m-%d %H:%M:%S.%f")

        # update timestamp
        tag_device['tag_time_stamp'] = current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")

        delta = current_timestamp - old_timestamp
        #print(current_timestamp, old_timestamp, delta)

        if delta.total_seconds() > 20 and current_state != 'moving':
            tag_device['name'] = 'moving'
            tag_device['proximity'] = 'moving'
        if delta.total_seconds() <= 20:
            tag_device['name'] = 'moving'
            tag_device['proximity'] = 'moving'
        # write updated TAG to db
        msgDb.update_single_device_db(tag_device)
        return True


    def update_rssi(self, _name, _address, rfpi, rssi):
        rfpi_s = rfpi_m = rfpi_w = rssi_s = rssi_m = rssi_w = "None"
        if len(rfpi) > 1:
            for idx, element in enumerate(rfpi):
                logger.debug('rfpi=%s', element)
                if idx==0:
                    rfpi_s = element
                if idx==1:
                    rfpi_m = element
                if idx==2:
                    rfpi_w = element
        else:
            # we didnt get a list of bases
            logger.debug('rfpi=%s', rfpi[0])
            rfpi_s = rfpi[0]

        if len(rssi) > 1:
            for idx, element in enumerate(rssi):
                logger.debug('rssi=%s', element)
                if idx==0:
                    rssi_s = element
                if idx==1:
                    rssi_m = element
                if idx==2:
                    rssi_w = element
        else:
            logger.debug('rssi=%s', rssi[0])

            rssi_s = rssi[0]

        return rfpi_s, rssi_s, rfpi_m, rssi_m, rfpi_w, rssi_w


    def update_rssi_beacon(self, beacontype, broadcastdata, bdaddr, rssi):
        # beacontype = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BEACONTYPE_XPATH')
        #      broadcastdata = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BROADCASTDATA_XPATH')
        #     bdaddr = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BDADDR_XPATH')        
        b_list = []
        if len(beacontype) > 1:
            for idx, element in enumerate(beacontype):
                logger.debug('beacon=(%s, %s, %s, %s)', element, broadcastdata[idx], bdaddr[idx], rssi[idx])
                # add to beacon list
                b_list.append({'beacontype': element, 'broadcastdata': broadcastdata[idx], 'bdaddr': bdaddr[idx], 'rssi': rssi[idx]})
        else:
            # we didnt get a list of beacons
            b_list.append({'beacontype': beacontype[0], 'broadcastdata': broadcastdata[0], 'bdaddr': bdaddr[0], 'rssi': rssi[0]})
            logger.debug('beacon=(%s, %s, %s, %s)', beacontype[0], broadcastdata[0], bdaddr[0], rssi[0])
        
        return b_list


    def update_image(self, login_address, image):
        # Update device data
        matched_address = next((item for item in self.devices if item['account'] == login_address), False)

        # add new device address or update
        if not matched_address:
            # we assume it exists
            logger.error('FATAL: couldnt find address and update image %s', login_address)
        else:
            matched_address['user_image'] = image

    '''
    def update_last_beacon(self, login_name, login_address, last_beacon, base_location, eventtype):
        #print("update_last_beacon:", login_name, login_address, last_beacon, eventtype)

        # Update device data
        matched_address = next((item for item in self.devices if item['account'] == login_address), False)

        # add new device address or update
        if not matched_address:
            logger.error("FATAL??, alarm address of handset should always exist")

            current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
            # add a new bt_mac
            self.devices.append({'device_type': 'None', 'bt_mac': 'None', 'name': login_name, 'account': login_address, 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': eventtype, 'beacon_gateway' : 'Unexpected', 'beacon_gateway_name' : 'Unexpected', 'user_image': '/images/depp.jpg', 'device_loggedin' : '1', 'base_location': base_location, 'last_beacon': last_beacon, 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime})

            logger.error('added unexspected Beacon: %s', login_address)

        else:
            matched_address['last_beacon'] = last_beacon
            matched_address['beacon_gateway'] = 'Handset Rcv'
            # in case of an alarm, we get the last known position, we cannot assume that we are still in the proximity
            if eventtype != "unchanged":
                matched_address['proximity'] = eventtype
            # we got a beacon in an alarm message
            # would be best to hold this info for a while
            if eventtype == "alarm":
                matched_address['proximity'] = 'alarm'
    '''

    def update_login(self, device_type, login_name, login_address, login, base_location, ip_connection = None):
        #print('update_login:',device_type, login_name, login_address, login, base_location)
        # default is current connection
        if ip_connection is None:
            ip_connection = self.m900_connection

        # new login messages do not give bt_mac info 
        bt_mac = 'None'
        
        # Update device data
        matched_address = next((item for item in self.devices if item['account'] == login_address), False)
        # update timstamp
        current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")

        # add new device address or update
        if not matched_address:
            # add a new device
            self.devices.append({'device_type': device_type, 'bt_mac': 'None', 'name': login_name,
                                'account': login_address, 'rssi': '-100', 'uuid': '', 'beacon_type': 'None',
                                'proximity': 'None', 'beacon_gateway' : 'None', 'beacon_gateway_name' : 'None',
                                'user_image': '/images/depp.jpg', 'device_loggedin' : login,
                                'base_location': base_location, 'base_connection': ip_connection,
                                'last_beacon': 'None',
                                'time_stamp': current_datetime, 'tag_time_stamp': current_datetime})

            logger.debug("update_login: added: %s", login_address)
        else:
            # get bt_mac - might be updated elsewhere
            bt_mac = matched_address['bt_mac'] 

            # update potentially changed fields
            matched_address['device_type'] = device_type
            matched_address['device_loggedin'] = login
            matched_address['base_location']   = base_location
            matched_address['base_connection'] = ip_connection
            matched_address['name']            = login_name
            matched_address['time_stamp']      = current_datetime


        # add/update device on mqtt as well
        ip, port = ip_connection
        mqttc.publish_login(device_type, login_name, login_address, login, base_location, f'{ip}:{port}', bt_mac)
        # update device
        self.send_to_location_viewer(login_address)


    def update_login_gateway(self, *args, **kwargs):
        """Insert a new gateway ipei and gateway name of same value.
        """    
        if msgDb:
            msgDb.record_gateway_db(**kwargs)
            
        else:
            logger.warning("update_login_gateway: No DB, gateway %s not updated", kwargs)


    def update_alarm_table(self, *args, **kwargs):
        """Insert a alarm record into the DB.
        """    
        if msgDb:
            msgDb.record_alarm_db(**kwargs)
        else:
            logger.warning("update_alarm_table: No DB, gateway %s not updated", kwargs)


    def mqttc_publish_beacon(self, bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway):
        """Publish a received beacon with MQTT.
        """        
        mqttc.publish_beacon(bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway)


    def add_senderdata(self, xml_root):
        # contains all logged-in handsets
        addresses = xml_root.xpath("//senderdata/address")

        # not only addin but also removing unknown handsets should be done as long as IP address of base matches.
        for address in addresses:
            # XPATH uses index 1..
            element_idx = addresses.index(address) + 1
            #print('IDX:', element_idx, 'address:', address)
            # update or add handsets
            #  name_txt (display name) can be empty.. In this case name[x] throws a list error
            try:
                name_txt = xml_root.xpath("//senderdata/name[{0}]/text()".format(element_idx))[0]
            except:
                name_txt = 'no name'
            #  address should never been empty.. In this case continue in loop
            try:
                address_txt = xml_root.xpath("//senderdata/address[{0}]/text()".format(element_idx))[0]
            except:
                logger.debug("add_senderdata: empty address found, likely an unused account - skip")
                continue
            # get current base ip
            #print('current connection:', self.m900_connection)
            ip_connection = self.m900_connection
            # get old base ip from db
            old_m900_connection = self.get_base_connection(address_txt)
            if old_m900_connection != self.m900_connection:
                logger.info('update base IP. DECT reg moved:%s -> %s', old_m900_connection, ip_connection)

            base_location = xml_root.xpath("//systemdata/name/text()")[0]

            self.update_login('handset', name_txt, address_txt, "1", base_location, ip_connection)


    def send_xml(self, xml_data, base_connection=None, ):
        global s

        # there might be concurrency issues changing the receiving base.
        # for critical requests we submit its connection via the optional parameter
        if not base_connection:
            base_connection = self.m900_connection

        xml_with_header = (bytes('<?xml version="1.0" encoding="UTF-8"?>\n', encoding='utf-8') + ET.tostring(xml_data, pretty_print=True))

        #print(self.m900_connection)
        logger.debug(f'send_xml: {Fore.BLUE}{ET.tostring(xml_data, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}')
        logger.debug("send_xml: connection=%s", base_connection)
        s.sendto(xml_with_header, base_connection)


    def request_sms(self, base_connection=None, account=None, message=None, externalid=None, _name=None,
        priority=None, confirmationtype=None, rings=None
        ):
        if not externalid:
            externalid = f'sms{str(random.randint(100, 999))}'
        if not priority:
            priority = "1"
        if not confirmationtype:
            confirmationtype = "2"
        if not rings:
            rings = "1"

        final_doc = self.REQUEST(
                                 self.SYSTEMDATA(
                                                 self.NAME("SnomProxy"),
                                                 self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                 #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                 self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                 self.STATUS("1"),
                                                 self.STATUSINFO("System running")
                                                 ),
                                 self.JOBDATA(
                                              #self.ALARMNUMBER("2"),
                                              #self.REFERENCENUMBER("5"),
                                              self.PRIORITY(priority),
                                              self.FLASH("0"),
                                              self.RINGS(rings),
                                              self.CONFIRMATIONTYPE(confirmationtype),
                                              self.MESSAGES(
                                                            self.MESSAGE1("msg1"),
                                                            self.MESSAGE2("msg2"),
                                                            self.MESSAGEUUID(message)
                                                            ),
                                              self.STATUS("0"),
                                              self.STATUSINFO("")
                                              ),
                                 self.PERSONDATA(
                                                 self.ADDRESS(account),
                                                 self.STATUS("0"),
                                                 self.STATUSINFO("")
                                                 ),
                                 self.EXTERNALID(externalid)
                                 , version="1.0", type="job")

        self.send_xml(final_doc, base_connection)


    # test alarm
    def request_alarm(self, account, alarm_txt, alarm_prio='1', alarm_conf_type='2', alarm_status='0'):
        if int(alarm_status) == 10 or int(alarm_status) == 0:
            refnum = 100
        elif int(alarm_status) == 110 or int(alarm_status) == 100:
            # 100 and 110, we use 50 random refnums
            print(alarm_status)
            #50 random refnum 
            refnum = str(random.randint(100, 999))

            if int(alarm_status) == 100:
                alarm_status = '0'
            if int(alarm_status) == 110:
                alarm_status = '10'
        else: # 899 random refnums
            refnum = str(random.randint(100, 999))
            alarm_status = '0'

        final_doc = self.REQUEST(
                                 self.SYSTEMDATA(
                                                 self.NAME("SnomProxy"),
                                                 self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                 #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                 self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                 self.STATUS("1"),
                                                 self.STATUSINFO("System running")
                                                 ),
                                 self.JOBDATA(
                                              self.ALARMNUMBER("5"),
                                              # repeated alarms with same reference will show only last alarm
                                              self.REFERENCENUMBER('alarm_%s' % refnum),
                                              self.CALLBACKNUMBER('592'),
                                              #self.PRIORITY(str(random.randint(1, 9))),
                                              self.PRIORITY(alarm_prio),
                                              self.FLASH("0"),
                                              self.RINGS("1"),
                                              self.CONFIRMATIONTYPE(alarm_conf_type), 
                                              #self.CONFIRMATIONTYPE("2"), # with DECT and user confirmation
                                              #self.CONFIRMATIONTYPE("1"), # with DECT confirmation
                                              #self.CONFIRMATIONTYPE("0"), # without confirmation
                                              self.MESSAGES(
                                                            self.MESSAGE1("msg1"),
                                                            self.MESSAGE2("msg2"),
                                                            # add date and time to the message to distinguish better.
                                                            self.MESSAGEUUID('%s:%s' % (datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S"), alarm_txt))
                                                            ),
                                              self.STATUS(alarm_status), # delete 10
                                              self.STATUSINFO("")
                                              ),
                                 self.PERSONDATA(
                                                 self.ADDRESS(account),
                                                 self.STATUS("0"),
                                                 self.STATUSINFO("")
                                                 ),
                                 self.EXTERNALID('extID_%s' % str(random.randint(100, 999)))
                                 , version="1.0", type="job")

        self.send_xml(final_doc)

    # beacon: MS confirm response to FP:
    def response_beacon(self, externalid, _status, _statusinfo):
        final_doc = self.RESPONSE(
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by Outgoing interface"),
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  )
                                  , version="1.0", type="beacon")

        self.send_xml(final_doc)


    # sms: MS forwards sms via request to FP:
    def request_forward_sms(self, externalid, fromaddress, fromname, fromlocation, toaddress, priority, message1, message2, uuid):
        final_doc = self.REQUEST(
                                      self.EXTERNALID(externalid),
                                      self.SYSTEMDATA(
                                                      self.NAME("SnomProxy"),
                                                      self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                      #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                      self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                      self.STATUS("1"),
                                                      self.STATUSINFO("System running")
                                                    ),
                                        self.JOBDATA(
                                                     self.PRIORITY(priority),
                                                     self.MESSAGES(
                                                                   self.MESSAGE1(message1),
                                                                   self.MESSAGE2(message2),
                                                                   self.MESSAGEUUID(uuid)
                                                                   ),
                                                     self.STATUS("0"),
                                                     self.STATUSINFO("")
                                                     ),
                                        self.SENDERDATA(
                                                        self.ADDRESS(fromaddress),
                                                        self.NAME(fromname),
                                                        self.LOCATION(fromlocation)
                                                        ),
                                        self.PERSONDATA(
                                                        self.ADDRESS(toaddress)
                                                        )
                                        , version="1.0", type="job")

        m900_connection = self.get_base_connection(toaddress)
        self.send_xml(final_doc, m900_connection)


    '''
    Response (part 4) - FP acknowledges message is received:
    <?xml version="1.0" encoding="UTF-8"?>
    <response version="20.6.12.1308" type="job">
        <externalid>2953653356</externalid>
        <systemdata>
            <name>sme-voip-echoserver-0.0.1</name>
            <datetime>2020-08-14 12:44:51</datetime>
            <timestamp>5f366b23</timestamp>
            <status>1</status>
            <statusinfo>Accepted by sme-voip-echoserver-0.0.1</statusinfo>
        </systemdata>
        <senderdata>
            <address>666</address>
        </senderdata>
        <persondata>
            <address type="IPEI">0328D3C918</address>
            <location>M900</location>
        </persondata>
    </response>
    '''
    # sms: Response (part 4):
    def response_beacon_sms4(self, externalid, fromaddress, fromlocation, toaddress):
        final_doc = self.RESPONSE(
                                  self.EXTERNALID(externalid),
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("Accepted by SnomProxy")
                                                  ),
                                    self.SENDERDATA(
                                                    self.ADDRESS(toaddress),
                                                    ),
                                    self.PERSONDATA(
                                                    #<address type="IPEI">0328D3C918</address>
                                                    # difference to SMS recv response<
                                                    self.ADDRESS(fromaddress, type="IPEI"),
                                                    self.LOCATION(fromlocation)
                                                    )
                                    , version="1.0", type="job")

        self.send_xml(final_doc)


    '''
    Response (part 6) - PP acknowledges message is received
    <?xml version="1.0" encoding="UTF-8"?>
    <response version="20.6.12.1308" type="job">
        <externalid>2953653356</externalid>
        <systemdata>
            <name>sme-voip-echoserver-0.0.1</name>
            <datetime>2020-08-14 12:44:51</datetime>
            <timestamp>5f366b23</timestamp>
            <status>1</status>
            <statusinfo>Accepted by sme-voip-echoserver-0.0.1</statusinfo>
        </systemdata>
        <jobdata>
            <priority>0</priority>
            <messages>
                <message1></message1>
                <message2></message2>
                <messageuui></messageuui>
            </messages>
            <status>1</status>
            <statusinfo></statusinfo>
        </jobdata>
        <senderdata>
            <address>666</address>
        </senderdata>
        <persondata>
            <address type="IPEI">0328D3C918</address>
            <location>M900</location>
        </persondata>
    </response>
    '''
    # sms: Response (part 6):
    def response_beacon_sms6(self, externalid, fromaddress, toaddress, tolocation):
        final_doc = self.RESPONSE(
                                      self.EXTERNALID(externalid),
                                      self.SYSTEMDATA(
                                                      self.NAME("SnomProxy"),
                                                      self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                      #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                      self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                      self.STATUS("1"),
                                                      self.STATUSINFO("Accepted by SnomProxy")
                                                      ),
                                        self.JOBDATA(
                                                     self.PRIORITY("0"),
                                                     self.MESSAGES(
                                                                   self.MESSAGE1(),
                                                                   self.MESSAGE2(),
                                                                   self.MESSAGEUUID()
                                                                   ),
                                                     self.STATUS("1"),
                                                     self.STATUSINFO()
                                                     ),
                                        self.SENDERDATA(
                                                        self.ADDRESS(fromaddress),
                                                        ),
                                        self.PERSONDATA(
                                                        self.ADDRESS(toaddress, type="IPEI"),
                                                        self.LOCATION(tolocation)
                                                        )
                                        , version="1.0", type="job")

        self.send_xml(final_doc)


    # SMS response from FP gets forwarded to receiving handset untouched
    # double XML header?
    def response_forward_sms(self, xml_response):
        # we need the receipients base connection
        toaddress = self.get_value(xml_response,'JOB_RESPONSE_PERSONDATA_ADDRESS_XPATH')
        # message server has send the initial request, no device to forward
        if toaddress == '':
            logger.info('message server has send the initial request, no device to forward.')
        else:
            m900_connection = self.get_base_connection(toaddress)
            self.send_xml(xml_response, m900_connection)


    # alarm: MS confirm response to FP:
    def response_alarm(self, externalid, _status, _statusinfo):
        final_doc = self.RESPONSE(
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by Outgoing interface"),
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  #self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  )
                                  , version="1.0", type="alarm")

        self.send_xml(final_doc)


    # we request this with schedule approx. every 1 minute, given that there is activity from the FP
    def request_keepalive(self):
        final_doc = self.REQUEST(
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(f'{int(time.time()):0>8X}'.lower()),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID('001121100')
                                  , version="1.0", type="systeminfo")

        self.send_xml(final_doc)


    def clear_old_devices(self, timeout=70):
        logger.debug("clear_old_devices: running with timeout=%s", timeout)

        current_timestamp = datetime.datetime.now()
        # remove all devices older than 60min
        # use [:] to use a copy of the list to modify
        for d in self.devices[:]:
            old_timestamp = datetime.datetime.strptime(d['time_stamp'], "%Y-%m-%d %H:%M:%S.%f")
            delta = current_timestamp - old_timestamp
                #print(d, 'delta', delta)
            #if delta.total_seconds() > 3600:
            if delta.total_seconds() > timeout:
                #print('found d:', d, current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"))
                logger.debug("clear_old_devices: found device to clear: %s", d)

                # delete record.
                if msgDb:
                    msgDb.delete_db(account=d['account'])
                    self.devices.remove(d)
                else:
                    self.devices.remove(d)

        return True


    def clear_old_m9b_device_status(self, timeout=70):
        logger.debug("clear_old_m9b_device_status: running with timeout=%s", timeout)

        # database has its own time non UTC or else
        # we use our server time instead
        current_timestamp = datetime.datetime.now()
        target_timestamp = current_timestamp - datetime.timedelta(seconds=timeout)

        # delete old status in DB.
        if msgDb:
            msgDb.clear_old_m9b_device_status_db(timeout, target_timestamp)
        else:
            logger.warning("clear_old_m9b_device_status: No DB, nothing to do")

        return True


    def get_base_connection(self, account):
        matched_device = next((item for item in self.devices if item['account'] == account), False)
        if matched_device:
            if type(matched_device['base_connection']) == tuple:
                return matched_device['base_connection']
            else:
                # convert string to connection tuple
                t_l = matched_device['base_connection'][1:-1].split(',')
                return ( eval(t_l[0]), int(t_l[1]) )
        else:
            logger.warning("get_base_connection: account=%s not found (yet).", account)
            return ('127.0.0.1', 4711)


    def SMSs_MS_send_FP(self, data):
        logger.info('SMSs_MS_send_FP:')
        # get the message text
        # message is added to the name,account data, name=FormControlTextarea1 equals the form element of sms.html
        if not data:
            return

        sms_message_item = next((item for item in data if item['name'] == 'FormControlTextarea1'), False)

        for element in data:
            if element['name'] != 'FormControlTextarea1' and element['account'] != '' and sms_message_item['account'] != '':
                # request goes directly to any Mx00 base, we need to enquire for one..
                self.m900_connection = self.get_base_connection(element['account'])
                # mark the handset and send
                matched_account = next((localitem for localitem in self.devices if localitem['account'] == element['account']), False)
                if matched_account:
                    matched_account['proximity'] = 'sms'
                    self.request_sms(self.get_base_connection(element['account']), element['account'], sms_message_item['account'])


    def send_sms_from_post(self, post_data):
        """Sends sms to base from POST message to DECTMessagingViewer.
            Expects complete post_data for a single SMS in JSON format.

            JSON format example:
            {
                "externalid": "id_3x100",
                "name": "3x100",
                "account": "100100100",
                "message": "SMS sample message",
                "priority": "0",
                "confirmationtype": "2",
                "rings": "1"
            }

        Returns:
            boolean : True on successful XML submit or False. No feedback if the sms reached the base or recipient!
        """
        # get the message text
        # message is added to the name,account data, name=FormControlTextarea1 equals the form element of sms.html
        if not post_data:
            return False
        else:
            try:
                # which base serves the account?
                m900_connection = self.get_base_connection(post_data['account'])
                self.request_sms(
                    m900_connection,
                    post_data['account'],
                    post_data['message'],
                    post_data['externalid'],
                    post_data['name'],
                    post_data['priority'],
                    post_data['confirmationtype'],
                    post_data['rings']
                )
            except IndentationError:
                return False
        return True


    def alarms_MS_send_FP(self, data):
        logger.info('alarms_MS_send_FP:')
        # get the message text
        # message is added to the name,account data
        if not data:
            return

        # set default for all parameters
        sms_message_item = {"account": 'empty'}
        sms_prio_item = {"account": '1'}
        sms_conf_type_item = {"account": '2'} # DECT and user confirmation
        sms_status_item = {"account": '1'}
        
        # get submitted data, if available
        sms_message_item_t = next((item for item in data if item['name'] == 'MessageTextarea1'), False)
        if sms_message_item_t:
            sms_message_item = sms_message_item_t
        
        sms_prio_item_t= next((item for item in data if item['name'] == 'SelectPrio'), False)
        if sms_prio_item_t:
            sms_prio_item = sms_prio_item_t
       
        sms_conf_type_item_t= next((item for item in data if item['name'] == 'SelectConfType'), False)
        if sms_conf_type_item_t:
            sms_conf_type_item = sms_conf_type_item_t
       
        sms_status_item_t = next((item for item in data if item['name'] == 'SelectMsgType'), False)
        if sms_status_item_t:
            sms_status_item = sms_status_item_t
      
        for element in data:
            if element['name'] not in ['MessageTextarea1', 'SelectPrio', 'SelectConfType', 'SelectMsgType', '']:
                # request goes directly to any Mx00 base, we need to enquire for one..
                self.m900_connection = self.get_base_connection(element['account'])
                # mark the handset and send
                matched_account = next((localitem for localitem in self.devices if localitem['account'] == element['account'] and localitem['device_type'] == 'handset'), False)
                if matched_account:
                    matched_account['proximity'] = 'alarm'
                    self.request_alarm(element['account'], sms_message_item['account'], sms_prio_item['account'], sms_conf_type_item['account'], sms_status_item['account'])


    def send_to_location_viewer(self, account=None):
        """Synchronise data from:
        - Database Devices Table
        - DECTMessagingViewer - changed btmacs

        Returns:
            devices [DICT]: Synchronised devices dict
        """
        logger.info('send_to_location_viewer:')
        if msgDb:
            # sync btmacs first
            record_list = msgDb.read_db(table='Devices', bt_mac=None, account=None)
            #print(record_list)
            for elem in record_list:
                try:
                    matched_account = next((localitem for localitem in self.devices if localitem['account'] == elem['account']), False)
                    matched_account['bt_mac'] = elem['bt_mac']
                except:
                    logger.debug("account for updated bt_mac from db not existing: a:%s,%s", elem['account'], elem['bt_mac'])

            # autonomous viewer does not need to sync data back or get triggered
            if not viewer_autonomous:
                success = msgDb.update_devices_db(self.devices)
                # notify the viewer for now.
                try:
                    # send btmacs updated data back to viewer.
                    _r = requests.post(f'{DECT_MESSAGING_VIEWER_URL}/location', json=self.btmacaddresses)
                except requests.exceptions.Timeout as errt:
                    logger.warning("Timeout Error location:%s", errt)


                return success
            else:
                 # no sync back to viewer
                if account:
                    matched_account = next((localitem for localitem in self.devices if localitem['account'] == account), False)
                    if matched_account:
                        success = msgDb.update_single_device_db(matched_account)
                        logger.debug("Given account -%s- updated.", account)

                    else:
                        logger.warning("Given account -%s- not found to update.", account)

                else:    
                    success = msgDb.update_devices_db(self.devices)

                return True
                
        else:
            # first try to get an update of bt_macs.
            # this overrides the bt_mac, since at the same time we might have added another device..
            # enumerate cannot work..
            try:
                response = requests.get(f'{DECT_MESSAGING_VIEWER_URL}/devicessync', timeout=3)
                if response:
                    json_data = json.loads(response.text)
                    if json_data is not None:
                        #print(json_data)
                        for idx, item in enumerate(json_data['data']):
                            # search for a matching bt_mac. Doubles should not be there!
                            #print("item:", item)
                            matched_bt_mac = next((localitem for localitem in self.devices if localitem['account'] == item['account']), False)
                            if not matched_bt_mac:
                                logger.debug(idx, 'not existing, viewer has async data')
                            else:
                                # the user has changed a btmac via btmactable page.
                                matched_bt_mac['bt_mac'] = item['bt_mac']
            except requests.exceptions.Timeout as errt:
                logger.error("Timeout Error devicessync:%s",errt)

            try:
                # send btmacs updated data back to viewer.
                _r = requests.post(f'{DECT_MESSAGING_VIEWER_URL}/location', json=self.devices+self.btmacaddresses)
            except requests.exceptions.Timeout as errt:
                logger.error("Timeout Error location:%s",errt)

            return True


    def update_proximity(self, address, alarm_type):
        logger.info('update_proximity: %s=%s' % (address, alarm_type))
        matched_address = next((localitem for localitem in self.devices if localitem['account'] == address), False)
        matched_address['proximity'] = alarm_type


    def get_value(self, xml_root, xpath):
        # handles empty tags and returns first value in case a list is returned.
        valueList = xml_root.xpath(self.msg_xpath_map[xpath])

        # depending on the xpath used we receive a List or a value or an empty List
        if valueList:
            value = valueList[0]
        else:
            if len(valueList) == 0:
                # empty List
                value = ''
            else:
                # direct value
                value = valueList

        return value


    def msg_process(self, data):
        """XML message protocol request/response handler
        Requests, Responses are described in detail in the message protocol specification.

        Additionally special job_types with json bodies to send sms or alarms get processed.

        Args:
            data (XML message): XML message described in the protocol specification

        Returns:
            True
        """
        msg_profile_root = ET.XML(data.encode('UTF-8'))

        # check all response types and process accordingly
        response_type = msg_profile_root.xpath(self.msg_xpath_map['RESPONSE_TYPE_XPATH'])

        if response_type:
            self.msg_response(response_type, msg_profile_root)
            return True


        # check all request types and respond accordingly
        request_type = msg_profile_root.xpath(self.msg_xpath_map['REQUEST_TYPE_XPATH'])

        if request_type:
            if request_type[0] != 'json-data':
                self.msg_request(request_type, msg_profile_root)
            else:
                # Alarm and SMS trigger from MS
                #if request_type == 'json-data':
                json_data = self.get_value(msg_profile_root, 'SNOM_REQUEST_JSONDATA')
                # we get sms or alarm handsets
                jobtype = self.get_value(msg_profile_root, 'SNOM_REQUEST_JSONDATA_JOBTYPE')
                # all handset account and text message data
                data = json.loads(json_data)

                # send message to all sms or alarm recipients
                if jobtype == "alarm":
                    self.alarms_MS_send_FP(data)
                if jobtype == "send_sms":
                    self.send_sms_from_post(data)
                if jobtype == "sms":
                    self.SMSs_MS_send_FP(data)
                # ??? probably not needed!! only proximity gets rewritten into alarm or sms
                self.send_to_location_viewer()
            return True

        # type unknown !
        # all previous request types are not recognized
        logger.error('unknown request RECEIVED')
        logger.error(ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode"))
        return False
        # done


import timeit

# gevent greenlet queue
def worker():
    while True:
        gevent.sleep(0.0)
        starttime = timeit.default_timer()
        xmldata = q.get()
        try:
            logger.debug('#### task started')
            amsg.msg_process(xmldata)
        finally:
            elapsed = 1000 * (timeit.default_timer() - starttime)
            q.task_done()
            logger.debug(f'#### Queue of size {q.qsize()}: current task took {elapsed:.2f}ms')
        
            #logger.debug('Worker took %s ns', elapsed)
            break
    #print(gevent.getcurrent())
    # kill greenlet - otherwise mem leak
    gevent.kill(gevent.getcurrent())



import gevent.queue
from gevent.queue import JoinableQueue

q = JoinableQueue(maxsize=5)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='DECTMessagingServer')
    parser.add_argument('udp_port', metavar='udp_port', type=int, default=10300,
                   help='UDP port to send and receive XML messages.')
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example --log debug', default='warning'"),
    )

    options = parser.parse_args()
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    level = levels.get(options.log.lower())
    if level is None:
        raise ValueError(
            f"log level given: {options.log}"
            f" -- must be one of: {' | '.join(levels.keys())}"
        )
    args = parser.parse_args()
    #print(args)

    logger = logging.getLogger('DMServer')
    logger.setLevel(level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    ############################
    # get the device list data #
    ############################

    if msgDb and not INITDB:
        # read device list from DB
        my_devices = msgDb.read_devices_db()

    else:
        # import device list from file
        try:
            from DeviceData import predefined_devices, m9bIPEI_description
            my_devices = predefined_devices
            logger.debug('devices imported: %s' % my_devices)

            # add/overwrite all M9B descrtiption names to the existing table
            if msgDb:
                for key in m9bIPEI_description.keys():
                    msgDb.record_gateway_db(beacon_gateway_IPEI=key, beacon_gateway_name=m9bIPEI_description[key])
        except:
            my_devices = []
            logger.debug('no devices found to import')

    ''' 
    ACTIONS
    '''
    # initiate message handler
    KNX_URL = f'{KNX_GATEWAY_URL}'
    # we use DECT ULE instead of KNX for the plug.
    KNX_URL = f'{ULE_GATEWAY_URL}'
    KNX_gateway = DECT_KNX_gateway_connector(knx_url=KNX_URL)

    # add all the capacity overflow actions
    ACTIONS = [
        # ULE only 
        {'m9b_IPEI': '0328DD60EE', 'device_bt_mac': '000413BA0029', 'url': '/snom_ule_cmd/snom_set_cmd_attribute_value%209%201%20514%201%201%20%22Hue%200-359%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%22%200', 
         'proximity': '0'},
        {'m9b_IPEI': '0328DD60EE', 'device_bt_mac': '000413BA0029', 'url': '/snom_ule_cmd/snom_set_cmd_attribute_value%209%201%20514%201%201%20%22Hue%200-359%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%22%200', 
         'proximity': 'moving'},
        {'m9b_IPEI': '0328DD60EE', 'device_bt_mac': '000413BA0029', 'url': '/snom_ule_cmd/snom_set_cmd_attribute_value%209%201%20514%201%201%20%22Hue%200-359%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%22%20120', 
         'proximity': 'holding_still'},
        {'m9b_IPEI': '0328DD60EE', 'device_bt_mac': '000413BA0029', 'url': '/snom_ule_cmd/snom_set_cmd_attribute_value%209%201%20514%201%201%20%22Hue%200-359%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%22%20120', 
         'proximity': '1'},
    ]
    KNX_gateway.update_actions(ACTIONS)



    # add dummy devices for load testing
    for i in range(0):
        my_devices.append({'device_type': 'None', 'bt_mac': 'None', 'name': "name_%s" % i, 'account': "account_%s" % i,
                        'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': "1", 'beacon_gateway' : 'None',
                        'beacon_gateway_name' : '', 'user_image': '/images/depp.jpg', 'device_loggedin' : "1",
                        'base_location': "no clue", 'last_beacon': "None", 'base_connection': ('127.0.0.1', 4711),
                        'time_stamp': '2020-04-01 00:00:01.100000', 'tag_time_stamp': '2020-04-01 00:00:01.100000'} )

    # initiate message handler
    amsg = MSSeriesMessageHandler(logger, my_devices)
    logger.debug("%s devices loaded", len(amsg.devices))

    #######
    #######

    ##################################
    # start the UDP protocol channel #
    ##################################


    import sys, socket

    localPort = args.udp_port

    ''' later?!
    HOST, PORT = "0.0.0.0", localPort
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()

    print('server started')        
    '''

    try:
        localPort = int(localPort)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', localPort))
    except:
        logger.critical('FATAL: bind to port number %s failed', str(localPort))
        exit()

    ## connection will be incoming Mx00 address, use a random connection for now.
    amsg.m900_connection  = ('192.168.188.21', 1300)

    knownClient = None
    sys.stderr.write('All set.\n')

    #send initial devices data
    # in case device viewer is autonomous, this one syncs the DB again.
    amsg.send_to_location_viewer()

    logger.debug("main: schedule.every(1).minutes.do(amsg.request_keepalive)")
    schedule.every(1).minutes.do(amsg.request_keepalive)
    # we delete records from the DB if this is set!
    logger.debug("main: schedule.every(1).minutes.do(amsg.clear_old_devices(3600))")
    #schedule.every(1).minutes.do(amsg.clear_old_devices, 60)
    logger.debug("main: schedule.every(6).minutes.do(amsg.clear_old_m9b_device_status(360))")
    schedule.every(6).minutes.do(amsg.clear_old_m9b_device_status, 350)


    # MQTT Interface / False to disable temporarily..
    mqttc = snomM900MqttClient(True)
    rc = mqttc.connect_and_subscribe()

    ###################################
    # UDP protocol listen and process #
    ###################################
  
    while True:
        # check and execute scheduled task
        schedule.run_pending()

        raw_data, addr = s.recvfrom(32768)

        # data can come from multiple Mx00
        # addr is (ip, port) tuple
        amsg.m900_connection = addr

        try:
            # quick check if data is valid missing
            xmldata = raw_data.decode('utf-8')
            # process message
            #amsg.msg_process(xmldata)
            q.put(xmldata)
            gevent.spawn(worker)

            # yield to worker
            gevent.sleep(0)

            # mqtt is async now
            # rc = mqttc.run()
            # if rc != 0:
            #     logger.debug("MQTT: We have a problem rc=%s -- reconnnect" % rc)
            #     rc = mqttc.connect_and_subscribe()
        except:
            logger.warning("main: Message could not be understoood or unexpected error %s" % raw_data)
