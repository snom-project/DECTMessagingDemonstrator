import pyproxy as pp
from lxml import etree as ET
import lxml.builder
import datetime
import schedule
import time
import requests
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

# DB reuse and type
odbc=False
initdb=True
msgDb = DECTMessagingDb(beacon_queue_size=15, odbc=odbc, initdb=initdb)

#msgDb.delete_db()
viewer_autonomous = True
beacon_action = False


m9bIPEI_description ={
         '0328D3C918': 'Schreibtisch',
         '0328D3C922': 'Computer',
         '0328D7848C': 'Meeting6OG',
         '0328D78490': 'Kueche6OG',
         '0328D78488': 'Poststelle6O',
         '0328D78483': 'Eingang7OG',
         '0328D783CB': 'Treppe6OG',
         '0328D7848F': 'Treppe7OG',
         '0328D78491': 'MeetingG7OG',
         '0328D78492': 'StandUP6OG',
         '0328D78493': 'Kueche7OG',
         '0328D784B4': 'MeetingW7OG',
         '0328D3C8FC': 'RMA7OG',
         '0328D783C1': 'Marketing',
         '0328D783CA': 'Sales'
        }
if msgDb:
    for key in m9bIPEI_description.keys():
        msgDb.record_gateway_db(beacon_gateway_IPEI=key, beacon_gateway_name=m9bIPEI_description[key])


class MSSeriesMessageHandler:
    
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

        #    <senderdata> <address type="IPEI">0328D3C909</address> ...
        'X_SENDERDATA_ADDRESS_IPEI_XPATH': "//senderdata/address[@type='IPEI']/text()",

        'X_SENDERDATA_LOCATION_XPATH': "//senderdata//location/text()",
              
        'X_BEACONDATA_EVENTTYPE_XPATH':     "//beacondata//eventtype/text()",
        'X_BEACONDATA_BEACONTYPE_XPATH':    "//beacondata//beacontype/text()",
        'X_BEACONDATA_BROADCASTDATA_XPATH': "//beacondata//broadcastdata/text()",
        'X_BEACONDATA_BDADDR_XPATH':        "//beacondata//bdaddr/text()",
                
        'ALARM_NAMESPACE_PREFIX': {'x': namespace}
    }

    def __init__(self, devices={}):
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
    
    
    def fire_beacon_action(self, beacon_gateway, proximity):
        KNX_URL = 'http://192.168.178.22:1234'

        if proximity != "0":
            switch='an'
        else:
            switch='aus'
        request_url = '{0}{1}{2}'.format(KNX_URL, '/1/2/10-', switch )
        
        if beacon_action:
            r = requests.get(request_url)
            print('KNX: %s' % request_url, r)

        else:
            print('KNX disabled: %s' % request_url)


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
     <address>200</address>
     </persondata>
     </request>
    '''
    #   self.update_beacon(messageuui, senderaddress_ipei[0], personaddress)

    def update_beacon(self, messageuui, senderaddress, personaddress):
        # this is the sender of the beacon
        beacon_gateway = senderaddress
        
        #print('update_beacon')
        logger.debug('messageuui from %s:%s' % (beacon_gateway, messageuui))

        if messageuui.split(';',1)[0] == '!BT':
            _, bt_mac, _, beacon_type, uuid, d_type, proximity, rssi= messageuui.split(';')

            print("take only the first 2 characters form d_type", d_type)
            d_type = d_type[:2]
            print("resulting d_type:", d_type)
        else:
            print('not a BT message')
            return False

        # rssi worse than 100 we discard radically, proximity can be 1 (inside), 2 (rssi change)  or 3 (state report)
        if proximity != '0' and int(rssi) < -100:
            print('disregarding Beacon Info with rssi=', rssi)
            logger.info("update_beacon: disregarding Beacon Info with rssi=%s" % rssi)
            return False
            
        # Update device data
        matched_bt_mac = next((item for item in self.devices if item['bt_mac'] == bt_mac), False)
        # we record updated timestamps to identify stale devices
        current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")

        if not matched_bt_mac:
        # we found a new device

            # we see the device_type in the BT message
            if d_type == "-4" and '1122334455667788990011223344' not in uuid:
                device_type_new = 'BTLETag'
                self.devices.append({'device_type': device_type_new, 'bt_mac': bt_mac, 'name': 'moving', 'account': 'Tag_%s' % bt_mac, 'rssi': rssi, 'uuid': uuid, 'beacon_type': beacon_type, 'proximity': proximity, 'beacon_gateway' : beacon_gateway, 'beacon_gateway_name' : '', 'user_image': '/images/beacon.jpeg', 'device_loggedin' : '1', 'base_location': 'None', 'base_connection': self.m900_connection, 'last_beacon': 'Tag', 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime} )
                
                logger.debug("update_beacon: added Tag %s %s" % (bt_mac, uuid))

            else:
                # alt beacon M9b TX have payload default e.g. 001122334455667788990011223344556677889000
                # we use only the common part for all beacon types
                if '1122334455667788990011223344' in uuid:
                    print('device is a M9B in TX mode')
            
                device_type_new = 'beacon'
                # add a new bt_mac
                self.devices.append({'device_type': device_type_new, 'bt_mac': bt_mac, 'name': 'M9B %s' % personaddress, 'account': bt_mac, 'rssi': rssi, 'uuid': uuid, 'beacon_type': beacon_type, 'proximity': proximity, 'beacon_gateway' : beacon_gateway, 'beacon_gateway_name' : '', 'user_image': '/images/beacon.png', 'device_loggedin' : '1', 'base_location': 'None', 'base_connection': self.m900_connection, 'last_beacon': 'beacon ping', 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime} )
                self.btmacaddresses.append({'account': bt_mac, 'bt_mac': bt_mac})
                print('added: beacon?M9B ', personaddress, bt_mac, ' ', uuid)
            # we have added a new device, now match it to process further
            matched_bt_mac = next((item for item in self.devices if item['bt_mac'] == bt_mac), False)
            if not matched_bt_mac:
                print('FATAL: We have added a new device and cant match it.')
        
        # we found an already existing device
        else:
        
            # we see the device_type in the BT message
            if d_type == "-4":
                matched_bt_mac['device_type'] = 'BTLETag'
            else:
                matched_bt_mac['device_type'] = 'handset'
            # M9B in TX mode
            if '1122334455667788990011223344' in uuid:
                matched_bt_mac['device_type'] = 'beacon'


#            print('old   :', matched_bt_mac)
            matched_bt_mac['uuid'] = uuid
            matched_bt_mac['rssi'] = rssi
            matched_bt_mac['beacon_type'] = beacon_type
            # timestamp
            matched_bt_mac['time_stamp'] = current_datetime
    
            # check if address has changed. In this case do not Overwrite with Outside on old location
            #print('################', matched_bt_mac['beacon_gateway'], beacon_gateway, proximity)
            if (matched_bt_mac['beacon_gateway'] != beacon_gateway) and  proximity == '0':
                # we have a new address already, this message is leave message from an old address
                # do nothing
                # we do not overide the device info but instead make sure we record the 0 Beacon
                # in the database by using proximity and gateway directly.
                print('%%%%%%%%%%%%%old leave message, ignore', matched_bt_mac)
                #matched_bt_mac['beacon_gateway'] = matched_bt_mac['beacon_gateway'] + ' left: ' + beacon_gateway
                # proximity stays the old inside
                #return True
            else:
                matched_bt_mac['proximity'] = proximity
                matched_bt_mac['beacon_gateway'] = beacon_gateway
                #print('update:', matched_bt_mac)
        
            # fire action on beacon proximity
            self.fire_beacon_action(beacon_gateway, proximity)
            
            # Tags have their own state.
            if matched_bt_mac['device_type'] == 'BTLETag':
                # udpdate newly beacon and all Tags timstamps and states
                self.update_tags(matched_bt_mac)
                # Tags keep sending bursts and a final before they stop. We do not count the bursts
                # instead we assume that after the last burst in the next 30s nothing will come.
                # The Tag rests
                schedule.clear('TAGHold')
                schedule.every(30).seconds.do(self.update_all_tags).tag('TAGHold')
                

        # at this point we have appended new device and have a matched_bt_mac

        # rssi change
        if proximity == '2' and matched_bt_mac:
            matched_bt_mac["rssi"] = rssi
        
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
            # we do not overide the device info but instead make sure we record the 0 Beacon
            # in the database by using proximity and gateway directly.
            msgDb.record_beacon_db(account=matched_bt_mac["account"],
                                   device_type=matched_bt_mac["device_type"],
                                   bt_mac=matched_bt_mac["bt_mac"],
                                   name=matched_bt_mac["name"],
                                   rssi=matched_bt_mac["rssi"],
                                   uuid=matched_bt_mac["uuid"],
                                   beacon_type=matched_bt_mac["beacon_type"],
                                   proximity=proximity,
                                   beacon_gateway=beacon_gateway,
                                   beacon_gateway_name=beacon_gateway_name,
                                   time_stamp=matched_bt_mac["time_stamp"]
                                   )
            msgDb.record_m9b_device_status_db(account=matched_bt_mac["account"],
                       bt_mac=matched_bt_mac["bt_mac"],
                       rssi=matched_bt_mac["rssi"],
                       uuid=matched_bt_mac["uuid"],
                       beacon_type=matched_bt_mac["beacon_type"],
                       proximity=proximity,
                       beacon_gateway_IPEI=beacon_gateway,
                       beacon_gateway_name=beacon_gateway_name,
                       time_stamp=matched_bt_mac["time_stamp"]
                       )

            
#        for item in self.devices:
#            print(item['bt_mac'], ' ', item['name'], ' ', item['proximity'], ' ', item['beacon_gateway'], ':', item['beacon_gateway'], ' ', item['device_loggedin'])

        return True


    def update_all_tags(self):
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
                    if d['proximity'] == '1':
                        d['proximity'] = 'holding'
                    d['tag_time_stamp'] = current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                    #print('found d:', d, current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"))
                    mqttc.publish_beacon(d["bt_mac"], "", "", "", d["proximity"], -0, d["name"], d["beacon_gateway"])
                       
                     
        # the job has been called via schedule and needs to run only once.
        return schedule.CancelJob


    def update_tags(self, tag_device):
        #print(tag_device)
        
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
            tag_device['proximity'] = '1'
        if delta.total_seconds() <= 20:
            tag_device['name'] = 'moving'
            tag_device['proximity'] = '1'
        
        return True


    def update_rssi(self, name, address, rfpi, rssi):
        rfpi_s = rfpi_m = rfpi_w = rssi_s = rssi_m = rssi_w = "None"
        if len(rfpi) > 1:
            for idx, element in enumerate(rfpi):
                print("rfpi=", element)
                if idx==0:
                    rfpi_s = element
                if idx==1:
                    rfpi_m = element
                if idx==2:
                    rfpi_w = element        
        else:
            # we didnt get a list of bases
            print("rfpi=", rfpi[0])
            rfpi_s = rfpi[0]

        if len(rssi) > 1:
             for idx, element in enumerate(rssi):
                print("rssi=", element)
                if idx==0:
                    rssi_s = element
                if idx==1:
                    rssi_m = element
                if idx==2:
                    rssi_w = element        
        else:
            print("rssi=", rssi[0])
            rssi_s = rssi[0]

        return rfpi_s, rssi_s, rfpi_m, rssi_m, rfpi_w, rssi_w


    def update_image(self, login_address, image):
          # Update device data
          matched_address = next((item for item in self.devices if item['account'] == login_address), False)
          
          # add new device address or update
          if not matched_address:
              # we assume it exists
              print('FATAL: couldnt find address and update image', login_address)
          
          else:
              matched_address['user_image'] = image
            

    def update_last_beacon(self, login_name, login_address, last_beacon, base_location, eventtype):
        #print("update_last_beacon:", login_name, login_address, last_beacon, eventtype)
        
        # Update device data
        matched_address = next((item for item in self.devices if item['account'] == login_address), False)
        #matched_name = next((item for item in self.devices if item['name'] == login_name), False)
        
        # add new device address or update
        if not matched_address:
            print('FATAL??, alarm address of handset should always exist')
            current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
            # add a new bt_mac
            self.devices.append({'device_type': 'None', 'bt_mac': 'None', 'name': login_name, 'account': login_address, 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': eventtype, 'beacon_gateway' : 'Unexpected', 'beacon_gateway_name' : 'Unexpected', 'user_image': '/images/depp.jpg', 'device_loggedin' : '1', 'base_location': base_location, 'last_beacon': last_beacon, 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime})
            
            print('added unexspected Beacon: ', login_address)
        
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

            
    def update_login(self, device_type, login_name, login_address, login, base_location, ip_connection = None):
        #print('update_login:',device_type, login_name, login_address, login, base_location)
        # default is current connection
        if ip_connection == None:
            ip_connection = self.m900_connection
            
        # Update device data
        matched_address = next((item for item in self.devices if item['account'] == login_address), False)
        #matched_name = next((item for item in self.devices if item['name'] == login_name), False)
        # update timstamp
        current_datetime = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")

        # add new device address or update
        if not matched_address:
            # add a new device
            self.devices.append({'device_type': device_type, 'bt_mac': 'None', 'name': login_name, 'account': login_address, 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': 'None', 'beacon_gateway' : 'None', 'beacon_gateway_name' : 'None', 'user_image': '/images/depp.jpg', 'device_loggedin' : login, 'base_location': base_location, 'base_connection': ip_connection, 'last_beacon': 'None', 'time_stamp': current_datetime, 'tag_time_stamp': current_datetime})
            
            print('added: ', login_address)

        else:
            # update potentially changed fields
            matched_address['device_loggedin'] = login
            matched_address['base_location']   = base_location
            matched_address['base_connection'] = ip_connection
            matched_address['name']            = login_name
            matched_address['time_stamp']      = current_datetime
            
        mqttc.publish_login(device_type, login_name, login_address, login, base_location)


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
            if (old_m900_connection != self.m900_connection):
                print('update base IP. DECT reg moved:', old_m900_connection, ip_connection)
                
            base_location = xml_root.xpath("//systemdata/name/text()")[0]
                
            self.update_login('handset', name_txt, address_txt, "1", base_location, ip_connection)


    def send_xml(self, xml_data):
        global s
  
        xml_with_header = (bytes('<?xml version="1.0" encoding="UTF-8"?>\n', encoding='utf-8') + ET.tostring(xml_data, pretty_print=True))

        #print(self.m900_connection)
        print(f'{Fore.BLUE}{ET.tostring(xml_data, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}')
        s.sendto(xml_with_header, self.m900_connection)
    

    def request_sms(self, account, message):
        final_doc = self.REQUEST(
                                 self.SYSTEMDATA(
                                                 self.NAME("SnomProxy"),
                                                 self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                 self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                 self.STATUS("1"),
                                                 self.STATUSINFO("System running")
                                                 ),
                                 self.JOBDATA(
                                              #self.ALARMNUMBER("2"),
#                                              self.REFERENCENUMBER("5"),
                                              self.PRIORITY("1"),
                                              self.FLASH("0"),
                                              self.RINGS("1"),
                                              self.CONFIRMATIONTYPE("2"),
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
                                 self.EXTERNALID('sms%s' % str(random.randint(100, 999)))
                                 , version="1.0", type="job")
            
        self.send_xml(final_doc)
        
        
    # test alarm
    def request_alarm(self, account, alarm_txt, alarm_status):
        final_doc = self.REQUEST(
                                 self.SYSTEMDATA(
                                                 self.NAME("SnomProxy"),
                                                 self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                 self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                 self.STATUS("1"),
                                                 self.STATUSINFO("System running")
                                                 ),
                                 self.JOBDATA(
                                              self.ALARMNUMBER("5"),
                                              # repeated alarms with same reference will show only last alarm
                                              self.REFERENCENUMBER('alarm_%s' % str(random.randint(100, 100))),
                                              self.PRIORITY("1"),
                                              self.FLASH("0"),
                                              self.RINGS("10"),
                                              self.CONFIRMATIONTYPE("2"),
                                              self.MESSAGES(
                                                            self.MESSAGE1("msg1"),
                                                            self.MESSAGE2("msg2"),
                                                            self.MESSAGEUUID(alarm_txt)
                                                            ),
                                              self.STATUS(alarm_status), # delete 10
                                              self.STATUSINFO("")
                                              ),
                                 self.PERSONDATA(
                                                 self.ADDRESS(account),
                                                 self.STATUS("0"),
                                                 self.STATUSINFO("")
                                                 ),
                                 self.EXTERNALID('alarm_%s' % str(random.randint(500, 500)))
                                 , version="1.0", type="job")
            
        self.send_xml(final_doc)

    # beacon: MS confirm response to FP:
    def response_beacon(self, externalid, status, statusinfo):
        final_doc = self.RESPONSE(
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by Outgoing interface"),
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  )
                                  , version="1.0", type="beacon")
            
        self.send_xml(final_doc)
     
 
    # sms: MS forwards sms via request to to FP:
    def request_forward_sms(self, externalid, fromaddress, fromname, fromlocation, toaddress, priority, message1, message2, uuid):
        final_doc = self.REQUEST(
                                      self.EXTERNALID(externalid),
                                      self.SYSTEMDATA(
                                                      self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                   self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
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
        self.send_xml(final_doc)


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
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
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
                                                   self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
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
    def response_forward_sms(self, xml_with_header):
        self.send_xml(xml_with_header)

    
    # alarm: MS confirm response to FP:
    def response_alarm(self, externalid, status, statusinfo):
        final_doc = self.RESPONSE(
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by Outgoing interface"),
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
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
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID('001121100')
                                  , version="1.0", type="systeminfo")
                                  
        self.send_xml(final_doc)


    # keep_alive: MS confirm response to FP:
    def response_keepalive(self, externalid, status, statusinfo):
        self.response_systeminfo(externalid, status, statusinfo)
    
    def clear_old_devices(self, timeout=70):
        logger.debug("clear_old_devices: running with timeout=%s" % (timeout))

        current_timestamp = datetime.datetime.now()
        # remove all devices older than 60min
        # use [:] to use a copy of the list to modify
        for d in self.devices[:]:
            old_timestamp = datetime.datetime.strptime(d['time_stamp'], "%Y-%m-%d %H:%M:%S.%f")
            delta = current_timestamp - old_timestamp
                #print(d, 'delta', delta)
            #if delta.total_seconds() > 3600:
            if delta.total_seconds() > timeout:
                print('found d:', d, current_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"))
                logger.debug("clear_old_devices: found device to clear: %s", d)

                # delete record.
                if msgDb:
                    msgDb.delete_db(account=d['account'])
                    self.devices.remove(d)
                else:
                    self.devices.remove(d)
                
        return True

    def clear_old_m9b_device_status(self, timeout=70):
        logger.debug("clear_old_m9b_device_status: running with timeout=%s" % (timeout))
                
        num_deleted = 0
        # database has its own time non UTC or else
        # we use our server time instead
        current_timestamp = datetime.datetime.now()
        target_timestamp = current_timestamp - datetime.timedelta(seconds=timeout)

        # delete old status in DB.
        if msgDb:
            msgDb.clear_old_m9b_device_status_db(timeout, target_timestamp)
        else:
            logger.debug("clear_old_m9b_device_status: No DB, noting to do")

        logger.debug("clear_old_m9b_device_status: %s status cleared" % (num_deleted))

        return True


    # login: MS confirm response to FP:
    def response_login(self, externalid, status, statusinfo):
        final_doc = self.RESPONSE(
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by external system")
                                  , version="1.0", type="login")

        self.send_xml(final_doc)


    # systeminfo: MS confirm response to FP:
    def response_systeminfo(self, externalid, status, statusinfo):
        final_doc = self.RESPONSE(
                                  self.SYSTEMDATA(
                                                  self.NAME("SnomProxy"),
                                                  self.DATETIME(datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")),
                                                  self.TIMESTAMP(format(int(datetime.datetime.utcnow().strftime("%s")), 'x')),
                                                  self.STATUS("1"),
                                                  self.STATUSINFO("System running")
                                                  ),
                                  self.EXTERNALID(externalid),
                                  self.STATUS("1"),
                                  self.STATUSINFO("Accepted by external system")
                                  , version="1.0", type="systeminfo",)

        self.send_xml(final_doc)

    def get_base_connection(self, account):
        matched_device = next((item for item in self.devices if item['account'] == account), False)
        if matched_device:
            return matched_device['base_connection']
        else:
            return ('127.0.0.1', 4711)


    def SMSs_MS_send_FP(self, data):
        print('SMSs_MS_send_FP:')
        # get the message text
        # message is added to the name,account data, name=FormControlTextarea1 equals the form element of sms.html
        if not data:
            return
        
        sms_message_item = next((item for item in data if item['name'] == 'FormControlTextarea1'), False)

        for element in data:
            if element['name'] != 'FormControlTextarea1' and element['account'] != '' and sms_message_item['account'] != '':
                # request goes directly to any Mx00 base, we need to enquire for one..
                #self.m900_connection = ('10.110.30.109', 1300)
                self.m900_connection = self.get_base_connection(element['account'])
                #print('set connect', self.get_base_connection(element['account']))
                # mark the handset and send
                matched_account = next((localitem for localitem in self.devices if localitem['account'] == element['account']), False)
                if matched_account:
                    matched_account['proximity'] = 'sms'
                    self.request_sms(element['account'], sms_message_item['account'])

                

    def alarms_MS_send_FP(self, data):
        print('alarms_MS_send_FP:')
        # get the message text
        # message is added to the name,account data, name=FormControlTextarea1 equals the form element of sms.html
        if not data:
            return
       
        sms_message_item = next((item for item in data if item['name'] == 'FormControlTextarea1'), False)
        sms_status_item = next((item for item in data if item['name'] == 'FormControlStatus1'), False)

        for element in data:
            if element['name'] != 'FormControlTextarea1' and element['account'] != '' and sms_message_item['account'] != '':
            
                # request goes directly to any Mx00 base, we need to enquire for one..
                self.m900_connection = self.get_base_connection(element['account'])
                #print('set connect', self.get_base_connection(element['account']))
                # mark the handset and send
                matched_account = next((localitem for localitem in self.devices if localitem['account'] == element['account']), False)
                if matched_account:
                    matched_account['proximity'] = 'alarm'
                    self.request_alarm(element['account'], sms_message_item['account'], sms_status_item['account'])

   
    def send_to_location_viewer(self):
        if msgDb:
            # sync btmacs first
            record_list = msgDb.read_db(table='Devices', bt_mac=None, account=None)
            #print(record_list)
            for elem in record_list:
                try:
                    matched_account = next((localitem for localitem in self.devices if localitem['account'] == elem['account']), False)
                    matched_account['bt_mac'] = elem['bt_mac']
                    #print(matched_account)

                except:
                    logger.debug("account for updated bt_mac from db not existing: a:%s,%s" % (elem['account'], elem['bt_mac']))

            # autonomous viewer does not need to sync data back or get triggered
            if not viewer_autonomous:
                success = msgDb.update_devices_db(self.devices)
                # notify the viewer for now.
                try:
                    # send btmacs updated data back to viewer.
                    _r = requests.post('http://127.0.0.1:8081/en_US/location', json=self.btmacaddresses)
                except requests.exceptions.Timeout as errt:
                    print ("Timeout Error location:",errt)

                return success
            else:
                # no sync back to viewer
                success = msgDb.update_devices_db(self.devices)

                return True
            
        else:
            # first try to get an update of bt_macs.
            # this overrides the bt_mac, since at the same time we might have added another device..
            # enumerate cannot work..
            try:
                response = requests.get('http://127.0.0.1:8081/en_US/devicessync', timeout=3)
                if (response):
                    json_data = json.loads(response.text)
                    if json_data is not None:
                        #print(json_data)
                        for idx, item in enumerate(json_data['data']):
                            # search for a matching bt_mac. Doubles should not be there!
                            #print("item:", item)
                            matched_bt_mac = next((localitem for localitem in self.devices if localitem['account'] == item['account']), False)
                            if not matched_bt_mac:
                                print(idx, 'not existing, viewer has async data')
                            else:
                                # the user has changed a btmac via btmactable page.
                                matched_bt_mac['bt_mac'] = item['bt_mac']
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error devicessync:",errt)
                
            try:
                # send btmacs updated data back to viewer.
                _r = requests.post('http://127.0.0.1:8081/en_US/location', json=self.devices+self.btmacaddresses)
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error location:",errt)
                
            return True
    
    
    def update_proximity(self, address, alarm_type):
        # ?????
        #print(address, alarm_type )
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
        alarm_profile_root = ET.XML(data.encode('UTF-8'))
            
        # check all response types and process accordingly
        response_type = alarm_profile_root.xpath(self.msg_xpath_map['RESPONSE_TYPE_XPATH'])
        
        if response_type:
            print('response type')
            self.msg(data)

        # check all request types and respond accordingly
        request_type = alarm_profile_root.xpath(self.msg_xpath_map['REQUEST_TYPE_XPATH'])

        if request_type:
            print('request type')
            self.msg(data)

    
    def msg(self, data):
#        print('################################################')
#        print(data)
#        print('################################################')

        alarm_profile_root = ET.XML(data.encode('UTF-8'))

        # check all response types and process accordingly
        response_type = alarm_profile_root.xpath(self.msg_xpath_map['RESPONSE_TYPE_XPATH'])

        if response_type:
            response_type = response_type[0]
            print('Response:', response_type)
            
            print(f'{Fore.YELLOW}{ET.tostring(alarm_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}..')
            # check if we got a response on our keepalive
            if response_type == 'systeminfo':
                # add all existing logged-in devices
                self.add_senderdata(alarm_profile_root)
                self.send_to_location_viewer()
                
                return True
            

            if response_type == 'job':
                # check the status
                ## zu viele werden gefunden.. brauchen nur den ersten stat
                alarm_status = alarm_profile_root.xpath(self.msg_xpath_map['JOB_RESPONSE_STATUS_XPATH'])
                if alarm_status:
                    alarm_status = alarm_status[0]

                    if alarm_status == "1":
                        print("message sent")

                alarm_job_status = alarm_profile_root.xpath(self.msg_xpath_map['X_REQUEST_JOBDATA_STATUS_XPATH'])

                alarm_job_address = self.get_value(alarm_profile_root,'X_SENDERDATA_ADDRESS_XPATH')

                # external ID gives us a hint if it is an sms or alarm message
                # sms: sms_xxx, alarm: alarm_xxx
                externalid = self.get_value(alarm_profile_root, 'X_REQUEST_EXTERNALID_XPATH')

                if alarm_job_status :
                    alarm_job_status = alarm_job_status[0]
                    if alarm_job_status == "1":
                        print("message received")
                    if alarm_job_status == "4":
                        print("message OKed / Confirmed %s" % externalid)
                        self.update_proximity(alarm_job_address, "alarm_confirmed")
                    if alarm_job_status == "5":
                        print("message rejected")
                        self.update_proximity(alarm_job_address, "alarm_rejected")
                    if alarm_job_status == "10":
                        print("message canceled")
                        self.update_proximity(alarm_job_address, "alarm_canceled")

                if alarm_job_status == '1':
                    self.response_forward_sms(alarm_profile_root)
                else:
                    if alarm_job_status == []:
                        print("Beacon Received")
                    else:
                        print("Job Response Status does not get a response :", alarm_job_status)

                return True


        # check all request types and respond accordingly
        request_type = alarm_profile_root.xpath(self.msg_xpath_map['REQUEST_TYPE_XPATH'])

        if request_type:
            request_type = request_type[0]
            print('Request:', request_type)
            print(f'{Fore.GREEN}{ET.tostring(alarm_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}..')

            
            # common systeminfo data for all request types
            self.externalid = self.get_value(alarm_profile_root, 'X_REQUEST_EXTERNALID_XPATH')
            status = self.get_value(alarm_profile_root, 'X_REQUEST_SYSTEMDATA_STATUS_XPATH')
            statusinfo = self.get_value(alarm_profile_root, 'X_REQUEST_SYSTEMDATA_STATUSINFO_XPATH')


            # sync beetween FP and MS
            if request_type == 'json-data':
                # check if we have a login request, including a logindata section
                
                json_data = self.get_value(alarm_profile_root, 'SNOM_REQUEST_JSONDATA')
                # we get sms or alarm handsets
                jobtype = self.get_value(alarm_profile_root, 'SNOM_REQUEST_JSONDATA_JOBTYPE')
                # all handset account and text message data
                data = json.loads(json_data)
                
                # send message to all sms or alarm recipients
                if jobtype == "alarm":
                    self.alarms_MS_send_FP(data)
                else:
                    self.SMSs_MS_send_FP(data)

                self.send_to_location_viewer()


                
                     
            # sync beetween FP and MS
            if request_type == 'systeminfo':
                # check if we have a login request, including a logindata section
                senderdata = alarm_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_XPATH'])
                
                if senderdata:
                    # add all existing logged-in devices
                    self.add_senderdata(alarm_profile_root)
                    self.send_to_location_viewer()

                    logger.debug("systeminfo keep_alive: Respond with MS confirm response to FP:")

                    # send ready to operate response
                    self.response_keepalive(self.externalid, status, statusinfo)
                else:
                    logger.debug("systeminfo: Respond with MS confirm response to FP:")

                    # send ready to operate response
                    self.response_systeminfo(self.externalid, status, statusinfo)

                return True


            #### HANDSET alarming
            if request_type == 'alarm':
                # name/account and location of the device
                name = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                address = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                base_location = self.get_value(alarm_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
                
                # update the location of the device
                self.update_login('handset', name, address, "1", base_location)
                
                alarmdata = alarm_profile_root.xpath(self.msg_xpath_map['X_ALARMDATA_XPATH'])
    
                if alarmdata:  # will someday be the best 3 beacons
                    # beacon last position info
                    type = self.get_value(alarm_profile_root, 'ALARM_REQUEST_ALARMDATA_TYPE_XPATH')
                    beacontype = self.get_value(alarm_profile_root, 'ALARM_REQUEST_ALARMDATA_BEACONTYPE_XPATH')
                    broadcastdata = self.get_value(alarm_profile_root, 'ALARM_REQUEST_ALARMDATA_BROADCASTDATA_XPATH')
                    bdaddr = self.get_value(alarm_profile_root, 'ALARM_REQUEST_ALARMDATA_BDADDR_XPATH')
                    if beacontype:
                        print("alarm beacon info", type, beacontype, broadcastdata, bdaddr)
                        # update the last beacon location
                        # we assume proximity = "1" since this was the last known location
                        self.update_last_beacon(name, address, bdaddr, base_location, "alarm")
                    # - 0: Man Down
                    # - 1: No Movement - 2: Running
                    # - 3: Pull Cord
                    # - 4: Red Key
                    # - 5-9 Reserved
                    print('Alarmtype:', type)
                else: # we set defaults for the DB
                    type = beacontype = broadcastdata = bdaddr = None
                
                rssidata = alarm_profile_root.xpath(self.msg_xpath_map['X_RSSIDATA_XPATH'])
                if rssidata:
                    # beacon last position info
                    rfpi = alarm_profile_root.xpath(self.msg_xpath_map['ALARM_REQUEST_RSSIDATA_RFPI_XPATH'])
                    rssi = alarm_profile_root.xpath(self.msg_xpath_map['ALARM_REQUEST_RSSIDATA_RSSI_XPATH'])

                    # update handset rssi data
                    rfpi_s, rssi_s, rfpi_m, rssi_m, rfpi_w, rssi_w = self.update_rssi(name, address, rfpi, rssi)
                else: # we set defaults for the DB
                    rfpi_s = rssi_s = "None"
                    rfpi_m = rssi_m = "None"
                    rfpi_w = rssi_w = "None"

                self.update_proximity(address, 'alarm_handset_%s' % type)
                
                self.response_alarm(self.externalid, status, statusinfo)

                # add, update Alarm table
                if msgDb:
                    msgDb.record_alarm_db(account=address,
                                   name=name,
                                   alarm_type=type,
                                   beacon_type=beacontype,
                                   beacon_broadcastdata=broadcastdata,
                                   beacon_bdaddr=bdaddr,
                                   rfpi_s=rfpi_s, rfpi_m=rfpi_m, rfpi_w=rfpi_w, 
                                   rssi_s=rssi_s, rssi_m=rssi_m, rssi_w=rssi_w, 
                                   )
                
                self.send_to_location_viewer()


            #### BEACONS and handsets
     
#     Job:  <?xml version="1.0" encoding="UTF-8"?>
#     <request version="19.8.6.1008" type="job">
#     <externalid>2113083292</externalid>
#     <systemdata>
#     <name>M700-1</name>
#     <datetime>1970-01-01 03:55:58</datetime>
#     <timestamp>0000374e</timestamp>
#     <status>1</status>
#     <statusinfo>System running</statusinfo>
#     </systemdata>
#     <jobdata>
#     <priority>0</priority>
#     <messages>
#     <message1></message1>
#     <message2></message2>
#     <messageuui>!BT;000413B50038;p;i;FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FFF1FFFF;0;1;-47</messageuui>
#     </messages>
#     <status>0</status>
#     <statusinfo></statusinfo>
#     </jobdata>
#     <senderdata>
#     <address type="IPEI">0328D3C909</address>
#     <location>M700-1</location>
#     </senderdata>
#     <persondata>
#     <address>4711</address>
#     </persondata>
#     </request>

     
            if request_type == 'job':
            
                print("We assume a SMS request")
                priority = self.get_value(alarm_profile_root, 'X_REQUEST_JOBDATA_PRIORITY_XPATH')
                message1 = message2 = '' # not used today
                toaddress = self.get_value(alarm_profile_root, 'JOB_REQUEST_PERSONDATA_ADDRESS_XPATH')
                fromname = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                fromaddress = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                fromlocation = self.get_value(alarm_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
                                
                uuid = self.get_value(alarm_profile_root, 'JOB_REQUEST_JOBDATA_MESSAGEUUID_XPATH')
                
                if '!BT' in uuid:
                    print('Beacon')
                    print(f'{Fore.RED}data:{data}{Style.RESET_ALL}')

                    messageuui = alarm_profile_root.xpath(self.msg_xpath_map['JOB_REQUEST_JOBDATA_MESSAGEUUID_XPATH'])[0]
                    personaddress= alarm_profile_root.xpath(self.msg_xpath_map['JOB_REQUEST_PERSONDATA_ADDRESS_XPATH'])[0]
                
                    #     <senderdata>
                    #     <address type="IPEI">0328D3C909</address>
                    #     <location>M700-1</location>
                    #     </senderdata>
                    senderaddress_ipei = alarm_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_ADDRESS_IPEI_XPATH'])
                    #print("We have a GW sending device proximity identified by its BT mac ", senderaddress_ipei, messageuui)
                    if senderaddress_ipei:
                        print("personaddress could be empty, the GW IPEI is always there")

                    # update the devices DB
                    self.update_beacon(messageuui, senderaddress_ipei[0], personaddress)
                    
                    # send response on job with beacon
                    # here we consider dialog SMS from FP to MS,
                    # resulting in Response (4) and Response (6)
                    print('response_beacon_sms (4)', self.externalid, fromaddress, fromlocation, toaddress)
                    self.response_beacon_sms4(self.externalid, fromaddress, fromlocation, toaddress)
                    print('response_beacon_sms (6)', self.externalid, fromaddress, fromlocation, toaddress)
                    self.response_beacon_sms6(self.externalid, toaddress, fromaddress, fromlocation)


                    # send to location viewer
                    self.send_to_location_viewer()
                else:
                
#                Job:  <?xml version="1.0" encoding="UTF-8"?>
#                <request version="19.8.6.1008" type="job">
#                <externalid>1457798220</externalid>
#                <systemdata>
#                <name>M700DataMaster</name>
#                <datetime>2019-11-02 17:55:01</datetime>
#                <timestamp>5dbdb4e5</timestamp>
#                <status>1</status>
#                <statusinfo>System running</statusinfo>
#                </systemdata>
#                <jobdata>
#                <priority>0</priority>
#                <messages>
#                <message1></message1>
#                <message2></message2>
#                <messageuui>K</messageuui>
#                </messages>
#                <status>0</status>
#                <statusinfo></statusinfo>
#                </jobdata>
#                <senderdata>
#                <address>+4925518638088002</address>
#                <name>025518638088</name>
#                <location>M700DataMaster</location>
#                </senderdata>
#                <persondata>
#                <address>999</address>
#                </persondata>
#                </request>
                    print('Job SMS: ', data)

                    print("We assume a SMS request")
                    priority = self.get_value(alarm_profile_root, 'X_REQUEST_JOBDATA_PRIORITY_XPATH')
                    message1 = message2 = '' # not used today
                    toaddress = self.get_value(alarm_profile_root, 'JOB_REQUEST_PERSONDATA_ADDRESS_XPATH')
                    fromname = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                    fromaddress = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                    fromlocation = self.get_value(alarm_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
                     
                    #print(uuid)
                    # forward to receiver
                    self.request_forward_sms(self.externalid, fromaddress, fromname, fromlocation, toaddress, priority, message1, message2, uuid)
                    
                    
            if request_type == 'beacon':
            
                print(f'{Fore.RED}data:{data}{Style.RESET_ALL}')
                # we have received a proximity beacon info from a handset
                # name/account and location of the device
                name = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                address = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                base_location = self.get_value(alarm_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
                            
                # update the location of the device
                self.update_login('handset', name, address, "1", base_location)
                            
                beacondata = alarm_profile_root.xpath(self.msg_xpath_map['X_BEACONDATA_XPATH'])
                # we expect beacondata
                if beacondata:
                    # beacon last position info
                    eventtype = self.get_value(alarm_profile_root,'X_BEACONDATA_EVENTTYPE_XPATH')
                    beacontype = self.get_value(alarm_profile_root, 'X_BEACONDATA_BEACONTYPE_XPATH')
                    broadcastdata = self.get_value(alarm_profile_root,'X_BEACONDATA_BROADCASTDATA_XPATH')
                    bdaddr = self.get_value(alarm_profile_root, 'X_BEACONDATA_BDADDR_XPATH')
                    
#                    The eventtype can be:
#                    0: entering proximity of the beacon 1: leaving proximity of the beacon
                    self.update_last_beacon(name, address, bdaddr, base_location, eventtype)

                    self.response_beacon(self.externalid, status, statusinfo)
                    
                else:
                    logger.debug('FATAL, we expected beacondata %s' % data)
                    
                # alarm is impotant, we update the viewer
                self.send_to_location_viewer()

                mqttc.publish_beacon(bdaddr, "BTLE", broadcastdata, beacontype, eventtype, "-00", address, "HS-Base:%s" % base_location)

                           
            #### LOGIN of handsets (address) and BEACON Gateways (IPEI)
            if request_type == 'login':

                device_type = 'handset'
                name = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                # the name TAG is missing in case of a BEACON login.
                # existence can only by checked by findall, xpath always returns empty not None
                name_exists = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_EXISTS_XPATH')
                                
                if name_exists is not "":
                    # we have a handset
                    name = self.get_value(alarm_profile_root, 'X_SENDERDATA_NAME_XPATH')
                    if len(name) == 0:
                        name = "no name"
                    address = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                else:
                    # we have a beacon gateway, here name tag is not existing
                    name = "Snom M9B XX"
                    address = self.get_value(alarm_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')

                    # we cannot know RX or TX
#                    device_type = 'SnomM9BRX'
                    

                loggedin = self.get_value(alarm_profile_root, 'LOGIN_REQUEST_LOGINDATA_STATUS_XPATH')
                if loggedin == "1" :
                    location = self.get_value(alarm_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
                else:
                    location = 'None'
                    
                # login adds new devices as well..
                self.update_login(device_type, name, address, loggedin, location)
            
                # <address type="IPEI">0328D3C918</address>
                # Snom M9B gets its own picture
                senderaddress_ipei = alarm_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_ADDRESS_IPEI_XPATH'])
                if senderaddress_ipei:
                    self.update_image(address, '/images/SnomM9B.jpg')
                    device_type = 'SnomM9BRX'
                    
                    # add, update gateway table
                    if msgDb:
                        msgDb.record_gateway_db(beacon_gateway_IPEI=senderaddress_ipei[0], beacon_gateway_name=senderaddress_ipei[0])

                # send to location viewer
                self.send_to_location_viewer()

                # send to FP
                self.response_login(self.externalid, status, statusinfo)

        # type unknown !
        else:
            print('unknown request RECEIVED')
            print(ET.tostring(alarm_profile_root, pretty_print=True, encoding="unicode"))


# main
logger = logging.getLogger('SnomMMessagingService')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


if msgDb and not initdb:
    devices = msgDb.read_devices_db()


# import data from file
try:
    from DeviceData import predefined_devices      
    devices = predefined_devices
    logger.debug('devices imported: %s' % devices)

except:
    devices = []
    logger.debug('no devices found to import')

amsg = MSSeriesMessageHandler(devices)
print(amsg.devices)


for i in range(0):
    devices.append({'device_type': 'None', 'bt_mac': 'None', 'name': "name_%s" % i, 'account': "account_%s" % i, 'rssi': '-100', 'uuid': '', 'beacon_type': 'None', 'proximity': "1", 'beacon_gateway' : 'None', 'beacon_gateway_name' : '', 'user_image': '/images/depp.jpg', 'device_loggedin' : "1", 'base_location': "no clue", 'last_beacon': "None", 'base_connection': ('127.0.0.1', 4711), 'time_stamp': '2020-04-01 00:00:01.100000', 'tag_time_stamp': '2020-04-01 00:00:01.100000'} )
         



#######
#######

import sys, socket

def fail(reason):
    sys.stderr.write(reason + '\n')
    sys.exit(1)


#if len(sys.argv) != 2:
#    fail('Usage: DECTMessagingServer.py localPort - python DECTMessagingServer.py 1300')

localPort = sys.argv[1]

try:
    localPort = int(localPort)
except:
    fail('Invalid port number: ' + str(localPort))
    exit()

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', localPort))
except:
    fail('Failed to bind on port ' + str(localPort))
    exit()

## check how far you can go without a real alarm server.
## connection will be incoming Mx00 address
amsg.m900_connection  = ('192.168.188.21', 1300)


knownClient = None
sys.stderr.write('All set.\n')

#### send initial devices data
amsg.send_to_location_viewer()

logger.debug("main: schedule.every(1).minutes.do(amsg.request_keepalive)")
schedule.every(1).minutes.do(amsg.request_keepalive)
logger.debug("main: schedule.every(1).minutes.do(amsg.clear_old_devices(3600))")
schedule.every(1).minutes.do(amsg.clear_old_devices, 60)
logger.debug("main: schedule.every(6).minutes.do(amsg.clear_old_m9b_device_status(360))")
schedule.every(6).minutes.do(amsg.clear_old_m9b_device_status, 350)

    
# MQTT Interface / False to disable temporarily..
mqttc = snomM900MqttClient(False)
rc = mqttc.connect_and_subscribe()

while True:
    # check and execute scheduled task
    schedule.run_pending()
    
    data, addr = s.recvfrom(32768)

    # data can come from multiple Mx00
    #print(addr)
    # addr is (ip, port) tuple
    amsg.m900_connection = addr
  
    #    print(data)
    try:
        xmldata = data.decode('utf-8')
        # process message
        amsg.msg_process(xmldata)

        # mqtt publish needs to be sent as well
        #mqttc.publish_login("M85 %s" % time.time())
        rc = mqttc.run()
        if rc != 0:
            logger.debug("MQTT: We have a problem rc=%s -- reconnnect" % rc)
            rc = mqttc.connect_and_subscribe()

    except:
        logger.debug("main: Message could not be understoood or unexpected error %s" % data)
        print('Encode to utf-8 failed', data)
