from DB.DECTMessagingDb import DECTMessagingDb
from DECTKNXGatewayConnector import DECT_KNX_gateway_connector

import requests
import json
import time
import schedule
import logging


class snomRoomCapacityClient():
    def __init__(self, enable=True):
        self.enable = enable

    def check_rooms_capacity(self):
        if msgDb:

            result = msgDb.read_m9b_device_status_2_db()
            #print(result)
            '''
            [{'account': '000413B50038', 'bt_mac': '000413B50038',
            'rssi': '-53', 'uuid': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FF',
            'beacon_type': 'a', 'proximity': '3',
            'beacon_gateway_IPEI': '0328D3C918', 'beacon_gateway_name': 'Schreibtisch',
            'time_stamp': '2020-10-29 10:44:22.489801', 'server_time_stamp': '2020-10-29 09:44:22', 'timeout': 96945}]
            '''
            # not unique
            m9bs = list({v['beacon_gateway_IPEI']:v['beacon_gateway_IPEI'] for v in result}.values())
            #print(m9bs)

            for m9b in m9bs:
                # publish config
                #mqttc.publish_beacon_full_config_ha(btmac.lower(), "M90", "001122334455", "d_type", "0", "-99", "000413444444", "beacon_gateway")

                print(m9b)
                # get btmac data for m9b
                selected_items = [{k:d[k] for k in d if k!="a"} for d in result if d.get("beacon_gateway_IPEI") == m9b]
                #print('selected_items:' , selected_items)
                print(len(selected_items))
                # create list of visible m9bs
                #gateway_list = []
                if len(selected_items) > 2:
                    logger.info("check_rooms_capacity: capacity of %s exceeded.", selected_items[0]["beacon_gateway_IPEI"])

                    for elem in selected_items:
                        # send alarm to all handsets - base_connection is needed from the Devives Tabel
                        logger.info(f'send alarm to {elem["account"]} on base connection {elem["base_connection"]}' )
                        # fire knx action(s)
                        logger.info(f'fire knx action for {elem["account"]},{elem["bt_mac"]} seen by M9B:{elem["beacon_gateway_IPEI"]}' )
                        KNX_gateway.fire_KNX_action(elem["bt_mac"], elem["beacon_gateway_IPEI"], "1")
                    # send alarm to handset
                    message = [
                        {"name": elem["account"], "account": elem["account"]}, 
                        {"name": "FormControlTextarea1", "account": "Corona Alert - too many people in room!"}, 
                        {"name": "FormControlStatus1",   "account": "0"},
                        {"name": "submitbutton", "account": ""}
                        ] 

                    # notify the user with alarm.
                    try:
                        # send btmacs updated data back to viewer.
                        _r = requests.post('http://127.0.0.1:8081/en_US/alarm', json=message)
                    except requests.exceptions.Timeout as errt:
                        print ("Timeout Error location:",errt)

    

if __name__ == "__main__":

    # prepare logger
    logger = logging.getLogger('SnomM9BCapacity')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s: %(message)s')

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # get access to the DB
    # DB reuse and type
    odbc=False
    initdb=False
    msgDb = DECTMessagingDb(odbc=odbc, initdb=initdb)

    # get access to KXN
    KNX_gateway = DECT_KNX_gateway_connector(knx_url='http://10.110.16.63:1234', maxsize=5)

    # get a mqtt instance sending data in hass.io form
    rc = snomRoomCapacityClient()
    # add all the capacity overflow actions 
    ACTIONS = [
        {'m9b_IPEI': '0328D3C918', 'device_bt_mac': '000413B50038', 'url': '/1/1/10-aus' , 'proximity': '0'},
        {'m9b_IPEI': '0328D3C918', 'device_bt_mac': '000413B50038', 'url': '/1/1/10-an' , 'proximity': '1'},
        {'m9b_IPEI': '0328D3C918', 'device_bt_mac': '000413B50038', 'url': '/1/1/10-an' , 'proximity': '2'},
        {'m9b_IPEI': '0328D3C918', 'device_bt_mac': '000413B50038', 'url': '/1/1/10-an' , 'proximity': '3'}
    ]
    KNX_gateway.update_actions(ACTIONS)

    # fire data with scheduler
    logger.debug("main: schedule.every(1).minutes.do(amsg.request_keepalive)")
    schedule.every(2).seconds.do(rc.check_rooms_capacity)

    while True:
        # check and execute scheduled task
        schedule.run_pending()
        time.sleep(2)
