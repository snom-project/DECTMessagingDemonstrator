from lxml import etree as ET

from colorama import init, Fore, Style
init()

def msg_request(self, request_type, msg_profile_root):
    """XML request message handler

    Args:
        data (XML message): XML message described in the protocol specification. Sends message request to UDP port.

    Returns:
        XML message: XML request described in the protocol specification. Updates the devices dict / DB.
    """
    if request_type:
        request_type = request_type[0]
        self.logger.info('Request: %s', request_type)
        self.logger.debug(f'{Fore.GREEN}{ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}..')

        # common systeminfo data for all request types
        self.externalid = self.get_value(msg_profile_root, 'X_REQUEST_EXTERNALID_XPATH')
        status = self.get_value(msg_profile_root, 'X_REQUEST_SYSTEMDATA_STATUS_XPATH')
        statusinfo = self.get_value(msg_profile_root, 'X_REQUEST_SYSTEMDATA_STATUSINFO_XPATH')


        # sync beetween FP and MS
        if request_type == 'systeminfo':
            # check if we have a login request, including a logindata section
            senderdata = msg_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_XPATH'])

            if senderdata:
                # add all existing logged-in devices
                self.add_senderdata(msg_profile_root)
                self.send_to_location_viewer()

                self.logger.debug("systeminfo keep_alive: Respond with MS confirm response to FP:")

                # send ready to operate response
                self.response_keepalive(self.externalid, status, statusinfo)
            else:
                self.logger.debug("systeminfo: Respond with MS confirm response to FP:")

                # send ready to operate response
                self.response_systeminfo(self.externalid, status, statusinfo)

            return True


        #### HANDSET alarming
        if request_type == 'alarm':
            # name/account and location of the device
            name = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
            address = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
            base_location = self.get_value(msg_profile_root, 'X_SENDERDATA_LOCATION_XPATH')

            # update the location of the device
            self.update_login('handset', name, address, "1", base_location)

            alarmdata = msg_profile_root.xpath(self.msg_xpath_map['X_ALARMDATA_XPATH'])

            if alarmdata:  # will someday be the best 3 beacons
                # beacon last position info
                alarm_type = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_TYPE_XPATH')
                beacontype = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BEACONTYPE_XPATH')
                broadcastdata = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BROADCASTDATA_XPATH')
                bdaddr = self.get_value(msg_profile_root, 'ALARM_REQUEST_ALARMDATA_BDADDR_XPATH')
                if beacontype:
                    print("alarm beacon info", alarm_type, beacontype, broadcastdata, bdaddr)
                    # update the last beacon location
                    # we assume proximity = "1" since this was the last known location
                    self.update_last_beacon(name, address, bdaddr, base_location, "alarm")
                # - 0: Man Down
                # - 1: No Movement - 2: Running
                # - 3: Pull Cord
                # - 4: Red Key
                # - 5-9 Reserved
                self.logger.debug('Alarmtype:%s', alarm_type)
            else: # we set defaults for the DB
                alarm_type = beacontype = broadcastdata = bdaddr = None

            rssidata = msg_profile_root.xpath(self.msg_xpath_map['X_RSSIDATA_XPATH'])
            if rssidata:
                # beacon last position info
                rfpi = msg_profile_root.xpath(self.msg_xpath_map['ALARM_REQUEST_RSSIDATA_RFPI_XPATH'])
                rssi = msg_profile_root.xpath(self.msg_xpath_map['ALARM_REQUEST_RSSIDATA_RSSI_XPATH'])

                # update handset rssi data
                rfpi_s, rssi_s, rfpi_m, rssi_m, rfpi_w, rssi_w = self.update_rssi(name, address, rfpi, rssi)
            else: # we set defaults for the DB
                rfpi_s = rssi_s = "None"
                rfpi_m = rssi_m = "None"
                rfpi_w = rssi_w = "None"

            self.update_proximity(address, 'alarm_handset_%s' % alarm_type)

            self.response_alarm(self.externalid, status, statusinfo)

            # add, update Alarm table
            self.update_alarm_table(account=address,
                                    name=name,
                                    alarm_type=alarm_type,
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
            priority = self.get_value(msg_profile_root, 'X_REQUEST_JOBDATA_PRIORITY_XPATH')
            message1 = message2 = '' # not used today
            toaddress = self.get_value(msg_profile_root, 'JOB_REQUEST_PERSONDATA_ADDRESS_XPATH')
            fromname = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
            fromaddress = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
            fromlocation = self.get_value(msg_profile_root, 'X_SENDERDATA_LOCATION_XPATH')

            uuid = self.get_value(msg_profile_root, 'JOB_REQUEST_JOBDATA_MESSAGEUUID_XPATH')

            if '!BT' in uuid:
                self.logger.debug('Beacon')
                #self.logger.debug(f'{Fore.RED}data:{data}{Style.RESET_ALL}')
                self.logger.debug(f'{Fore.RED}{ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}')


                messageuui = msg_profile_root.xpath(self.msg_xpath_map['JOB_REQUEST_JOBDATA_MESSAGEUUID_XPATH'])[0]
                personaddress= msg_profile_root.xpath(self.msg_xpath_map['JOB_REQUEST_PERSONDATA_ADDRESS_XPATH'])[0]

                #     <senderdata>
                #     <address type="IPEI">0328D3C909</address>
                #     <location>M700-1</location>
                #     </senderdata>
                senderaddress_ipei = msg_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_ADDRESS_IPEI_XPATH'])
                #print("We have a GW sending device proximity identified by its BT mac ", senderaddress_ipei, messageuui)
                if senderaddress_ipei:
                    print("personaddress could be empty, the GW IPEI is always there")

                # update the devices DB
                self.update_beacon(messageuui, senderaddress_ipei[0], personaddress)

                # send response on job with beacon
                # here we consider dialog SMS from FP to MS,
                # resulting in Response (4) and Response (6)
                self.logger.debug('response_beacon_sms (4): id=%s, from:%s registered on %s, name:%s', self.externalid, fromaddress, fromlocation, toaddress)
                self.response_beacon_sms4(self.externalid, fromaddress, fromlocation, toaddress)
                self.logger.debug('response_beacon_sms (6):id=%s from:%s, registered on %s, name:%s', self.externalid, fromaddress, fromlocation, toaddress)
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
                priority = self.get_value(msg_profile_root, 'X_REQUEST_JOBDATA_PRIORITY_XPATH')
                message1 = message2 = '' # not used today
                toaddress = self.get_value(msg_profile_root, 'JOB_REQUEST_PERSONDATA_ADDRESS_XPATH')
                fromname = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
                fromaddress = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
                fromlocation = self.get_value(msg_profile_root, 'X_SENDERDATA_LOCATION_XPATH')

                # forward to receiver
                # we need the base connection from the receiver!
                self.request_forward_sms(self.externalid, fromaddress, fromname, fromlocation, toaddress, priority, message1, message2, uuid)


        if request_type == 'beacon':

            #self.logger.debug(f'{Fore.RED}data:{data}{Style.RESET_ALL}')
            self.logger.debug(f'{Fore.RED}{ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}')

            # we have received a proximity beacon info from a handset
            # name/account and location of the device
            name = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
            address = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
            base_location = self.get_value(msg_profile_root, 'X_SENDERDATA_LOCATION_XPATH')

            # update the location of the device
            self.update_login('handset', name, address, "1", base_location)

            beacondata = msg_profile_root.xpath(self.msg_xpath_map['X_BEACONDATA_XPATH'])
            # we expect beacondata
            if beacondata:
                # beacon last position info
                eventtype = self.get_value(msg_profile_root,'X_BEACONDATA_EVENTTYPE_XPATH')
                beacontype = self.get_value(msg_profile_root, 'X_BEACONDATA_BEACONTYPE_XPATH')
                broadcastdata = self.get_value(msg_profile_root,'X_BEACONDATA_BROADCASTDATA_XPATH')
                bdaddr = self.get_value(msg_profile_root, 'X_BEACONDATA_BDADDR_XPATH')

                # The eventtype can be:
                # 0: entering proximity of the beacon 1: leaving proximity of the beacon
                self.update_last_beacon(name, address, bdaddr, base_location, eventtype)

                self.response_beacon(self.externalid, status, statusinfo)

            else:
                #self.logger.error('FATAL, beacondata  expected: %s' % data)
                self.logger.debug(f'FATAL, beacondata  expected: {Fore.RED}{ET.tostring(msg_profile_root, pretty_print=True, encoding="unicode")}{Style.RESET_ALL}..')


            # alarm is impotant, we update the viewer
            self.send_to_location_viewer()

            self.mqttc_publish_beacon(bdaddr, "BTLE", broadcastdata, beacontype, eventtype, "-00", address, "HS-Base:%s" % base_location)


        #### LOGIN of handsets (address) and BEACON Gateways (IPEI)
        if request_type == 'login':

            device_type = 'handset'
            name = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
            # the name TAG is missing in case of a BEACON login.
            # existence can only by checked by findall, xpath always returns empty not None
            name_exists = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_EXISTS_XPATH')

            if name_exists != "":
                # we have a handset
                name = self.get_value(msg_profile_root, 'X_SENDERDATA_NAME_XPATH')
                if len(name) == 0:
                    name = "no name"
                address = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')
            else:
                # we have a beacon gateway, here name tag is not existing
                name = "Snom M9B XX"
                address = self.get_value(msg_profile_root, 'X_SENDERDATA_ADDRESS_XPATH')

                # we cannot know RX or TX
                # device_type = 'SnomM9BRX'


            loggedin = self.get_value(msg_profile_root, 'LOGIN_REQUEST_LOGINDATA_STATUS_XPATH')
            if loggedin == "1" :
                location = self.get_value(msg_profile_root, 'X_SENDERDATA_LOCATION_XPATH')
            else:
                location = 'None'

            # login adds new devices as well..
            self.update_login(device_type, name, address, loggedin, location)

            # <address type="IPEI">0328D3C918</address>
            # Snom M9B gets its own picture
            senderaddress_ipei = msg_profile_root.xpath(self.msg_xpath_map['X_SENDERDATA_ADDRESS_IPEI_XPATH'])
            if senderaddress_ipei:
                self.update_image(address, '/images/SnomM9B.jpg')
                device_type = 'SnomM9BRX'

                # add, update gateway table
                self.update_login_gateway(beacon_gateway_IPEI=senderaddress_ipei[0], beacon_gateway_name=senderaddress_ipei[0])

            # send to location viewer
            self.send_to_location_viewer()

            # send to FP
            self.response_login(self.externalid, status, statusinfo)
