from mqtt.snomM900MqttClient import snomM900MqttClient as hassiomqtt
from DB.DECTMessagingDb import DECTMessagingDb

import json
import time
import schedule
import logging


class snomMqttHasssioClient(hassiomqtt):
    def __init__(self, enable=True):
        hassiomqtt.__init__(self)

        self.enable = enable


    def publish_beacon_full_config_ha(self, bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway):
        if self.enable:
              
            component = 'sensor'
            #object_id = beacon_gateway
            object_id = bt_mac.lower()
            # leave out
            node_id = "1"

            # /config for best gateway
            attribute='G'
            device_name = "snomMxx-%s" % bt_mac
            # send a new device with multiple sensors
            device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_%s" % (object_id, attribute))          
            payload = {"name": "SnomMxx-%s-%s" % (object_id, attribute),
            "unique_id": "SnomMxx-%s-%s" % (object_id, attribute),
            #"device_class": "None",
            "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_template": "{{ value_json.data | tojson}}",
            "unit_of_measurement": "M9B",
            "value_template": "{{ value_json.data.b_gateway }}",
            "device": {"identifiers": ["%s-%s" % (object_id, attribute)],
                        "name": device_name, 
                        "model": "SnomMxx", 
                        "manufacturer": "Snom Technology GmbH"}
            }
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))

            # /config for best gateway_name
            attribute='GN'
            device_name = "snomMxx-%s" % bt_mac
            # send a new device with multiple sensors
            device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_%s" % (object_id, attribute))          
            payload = {"name": "SnomMxx-%s-%s" % (object_id, attribute),
            "unique_id": "SnomMxx-%s-%s" % (object_id, attribute),
            #"device_class": "None",
            "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_template": "{{ value_json.data | tojson}}",
            "unit_of_measurement": "",
            "value_template": "{{ value_json.data.b_gateway_name }}",
            "device": {"identifiers": ["%s-%s" % (object_id, attribute)],
                        "name": device_name, 
                        "model": "SnomMxx", 
                        "manufacturer": "Snom Technology GmbH"}
            }
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))

            # /config for best proximity
            attribute='P'
            device_name = "snomMxx-%s" % bt_mac
            # send a new device with multiple sensors
            device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_%s" % (object_id, attribute))          
            payload = {"name": "SnomMxx-%s-%s" % (object_id, attribute),
            "unique_id": "SnomMxx-%s-%s" % (object_id, attribute),
            #"device_class": "None",
            "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_template": "{{ value_json.data | tojson}}",
            "unit_of_measurement": "",
            "value_template": "{{ value_json.data.b_proximity | int }}",
            "device": {"identifiers": ["%s-%s" % (object_id, attribute)],
                        "name": device_name, 
                        "model": "SnomMxx", 
                        "manufacturer": "Snom Technology GmbH"}
            }
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))
            
            # /config for best rssi
            attribute='R'
            device_name = "snomMxx-%s" % bt_mac
            # send a new device with multiple sensors
            device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_%s" % (object_id, attribute))          
            payload = {"name": "SnomMxx-%s-%s" % (object_id, attribute),
            "unique_id": "SnomMxx-%s-%s" % (object_id, attribute),
            #"device_class": "None",
            "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_template": "{{ value_json.data | tojson}}",
            "unit_of_measurement": "dBm",
            "value_template": "{{ value_json.data.b_rssi | int | abs }}",
            "device": {"identifiers": ["%s-%s" % (object_id, attribute)],
                        "name": device_name, 
                        "model": "SnomMxx", 
                        "manufacturer": "Snom Technology GmbH"}
            }
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))
            
            # /config for list of reporting gateways and their parameters
            attribute='GL'
            device_name = "snomMxx-%s" % bt_mac
            # send a new device with multiple sensors
            device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_%s" % (object_id, attribute))          
            payload = {"name": "SnomMxx-%s-%s" % (object_id, attribute),
            "unique_id": "SnomMxx-%s-%s" % (object_id, attribute),
            #"device_class": "None",
            "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
            "json_attributes_template": "{{ value_json.data | tojson}}",
            "unit_of_measurement": "list",
            "value_template": "{{ value_json.data.gateway_list | tojson }}",
            "device": {"identifiers": ["%s-%s" % (object_id, attribute)],
                        "name": device_name, 
                        "model": "SnomMxx", 
                        "manufacturer": "Snom Technology GmbH"}
            }
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))
            
           
    def publish_beacon_full_state_ha(self, bt_mac, device_name, account, proximity, rssi, beacon_gateway, beacon_gateway_name,
                                     gateway_list):

        component = 'sensor'
        #object_id = beacon_gateway
        object_id = bt_mac.lower()
        # leave out
        node_id = "1"
        
        if self.enable:
            # send payload to existing device
            # contains the nearest M9B + the full list of all reported M9Bs 
            print(gateway_list)
            payload = { "data" : {  "name" : device_name,
                                    "account" : account,
                                    "b_gateway" : beacon_gateway,
                                    "b_gateway_name" : beacon_gateway_name,
                                    "b_rssi" : rssi,
                                    "b_proximity" : proximity,
                                    # this is a list of {'ipei': '0328D3C918', 'proximity': '3', 'rssi': '-52'} dicts   
                                    "gateway_list" : gateway_list 
                                    }
                        }
            device_topic = "snomMxx/%s/%s/%s/state" % (component, node_id, object_id)
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))


    def publish_beacon_room_state_ha(self, bt_mac, account, proximity, rssi, beacon_gateway, beacon_gateway_name):
        if self.enable:
            component = 'sensor'
            object_id = bt_mac.lower()
            # leave out
            node_id = "1"

            # calculate distance
            distance = 1
            # send mqtt_room payload for device = id to room=beacon_gateway_name state 
            payload = {
                        "id": object_id,
                        "name": account,
                        "distance": distance
                        }
            # mqtt_rooms location topic
            device_topic = "snomMxx/%s/%s/presence/%s" % (component, node_id, beacon_gateway_name)
            # mqtt_rooms location
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))


    def publish_beacon_list_ha(self, bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway):
        if self.enable:
              
            component = 'sensor'
            #object_id = beacon_gateway
            object_id = bt_mac.lower()
            # leave out
            node_id = "1"

            list_of_IPEIS = ['list']    
            
            for ipei in list_of_IPEIS:
                device_name = "snomMxx-%s" % bt_mac
                # send a new device with multiple sensors
                device_topic = "snomMxx/%s/%s/%s/config" % (component, node_id, "%s_R_%s" % (object_id, ipei))          
                payload = {"name": "SnomMxx-%s" % (bt_mac),
                "unique_id": "SnomMxx-%s" % (bt_mac),
                #"device_class": "None",
                "state_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
                "json_attributes_topic": "snomMxx/%s/%s/%s/state" % (component, node_id, object_id),
                #"json_attributes_template": "{{ value_json.gateway_list | tojson }}",
                "json_attributes_template": "{{ value_json.data | tojson}}",
                "unit_of_measurement": "M9B",
                #"value_template": "{{ value_json.ipei_%s}}" % ipei,
                "value_template": "{{ value_json.data.gateway }}",
                #"value_template": "{{ value_json.data | tojson}}",
                "device": {"identifiers": ["%s" % bt_mac],
                            "name": device_name, 
                            "model": "SnomMxx", 
                            "manufacturer": "Snom Technology GmbH"}
                }
                # encode object to JSON
                self.publish("%s" % device_topic, json.dumps(payload))
            
            # send payload to existing device
            # contains the nearest M9B + the full list of all reported M9Bs 
            payload = { "data" : {  "name" : "M90",
                                    "account" : "100100100",
                                    "gateway" : "0000best01",
                                    "gateway_name" : "Kitchen",
                                    "rssi" : "-60",
                                    "proximity" : "2",
                                    "gateway_list" : [
                                        { "ipei" : "0000aa0001",
                                        "proximity" : "0",
                                        "rssi" : "-60"
                                        },
                                        { "ipei" : "0000aa0002",
                                        "proximity" : "1",
                                        "rssi" : "-70"
                                        },
                                        { "ipei" : "0000aa0003",
                                        "proximity" : "2",
                                        "rssi" : "-80"
                                        }     
                                    ] }
                                }
            '''payload = { "data" : {"some_name" : "my_name",
                        "gateway_list" : 
                            { "ipei" : "0000aa0001",
                              "proximity" : "0",
                              "irgendwas" : "sdfsfd"
                             } }
                      }
            '''
            device_topic = "snomMxx/%s/%s/%s/state" % (component, node_id, object_id)
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))
    


    # special Home-Assistant publish for mqtt dicovery
    # follows
    def publish_beacon_ha(self, bt_mac, beacon_type, uuid, d_type, proximity, rssi, name, beacon_gateway):
        if self.enable:
              
            component = 'sensor'
            #object_id = beacon_gateway
            object_id = bt_mac.lower()
            # leave out
            node_id = "1"
                        
            if beacon_gateway != "":
                device_name = "snom%s" % bt_mac
                # send a new device with multiple sensors
                device_topic = "snomM9BGateway/%s/%s/%s/config" % (component, node_id, "%s_R" % object_id)          
                payload = {"name": "SnomMxx-%s-R" % bt_mac,
                #"device_class": "None",
                "state_topic": "snomM9BGateway/%s/%s/%s/state" % (component, node_id, object_id),
                "unique_id": "SnomMxx-%s-R" % bt_mac,
                "unit_of_measurement": "IPEI",
                "value_template": "{{ value_json.rssi | int | abs}}",
                "device": {"identifiers": ["%s" % bt_mac],
                           "name": device_name, 
                           "model": "SnomM90", 
                           "manufacturer": "Snom Technology GmbH"}
                }
                # encode object to JSON
                self.publish("%s" % device_topic, json.dumps(payload))
                
                device_topic = "snomM9BGateway/%s/%s/%s/config" % (component, node_id, "%s_G" % object_id)
                payload = {"name": "SnomMxx-%s-G" % bt_mac,
                #"device_class": "None",
                "state_topic": "snomM9BGateway/%s/%s/%s/state" % (component, node_id, object_id),
                "unique_id": "SnomMxx-%s-G" % bt_mac,
                "unit_of_measurement": "BTLE GW",
                "value_template": "{{ value_json.beacon_gateway}}",
                "device": {"identifiers": ["%s" % bt_mac],
                           "name": device_name, 
                           "model": "SnomM90", 
                           "manufacturer": "Snom Technology GmbH"}
                }
                self.publish("%s" % device_topic, json.dumps(payload))

                device_topic = "snomM9BGateway/%s/%s/%s/config" % (component, node_id, "%s_P" % object_id)
                payload = {"name": "SnomMxx-%s-P" % bt_mac,
                #"device_class": "None",
                "state_topic": "snomM9BGateway/%s/%s/%s/state" % (component, node_id, object_id),
                "unique_id": "SnomMxx-%s-P" % bt_mac,
                "unit_of_measurement": "prox",
                "value_template": "{{ value_json.proximity | int}}",
                "device": {"identifiers": ["%s" % bt_mac],
                           "name": device_name, 
                           "model": "SnomM90", 
                           "manufacturer": "Snom Technology GmbH"}
                }
                self.publish("%s" % device_topic, json.dumps(payload))

            # send payload to existing device
            payload = {"bt_mac": bt_mac, 
                       "beacon_type": beacon_type, 
                       "uuid": uuid, 
                       "d_type": d_type, 
                       "proximity": proximity, 
                       "rssi": rssi, 
                       "name": name,
                       "beacon_gateway": beacon_gateway
                      }

            device_topic = "snomM9BGateway/%s/%s/%s/state" % (component, node_id, object_id)
            # encode object to JSON
            self.publish("%s" % device_topic, json.dumps(payload))
    
def get_best_m9b(selected):
    # get the best visible rssi m9b
    # sort in place
    selected.sort(key=lambda item: item.get("rssi"))
    #print('sorted', selected)
    return selected[0]


def send_locations():
    if msgDb:
        
        result = msgDb.read_m9b_device_status_db()
        #print(result)
        '''
        [{'account': '000413B50038', 'bt_mac': '000413B50038', 
        'rssi': '-53', 'uuid': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90FF', 
        'beacon_type': 'a', 'proximity': '3', 
        'beacon_gateway_IPEI': '0328D3C918', 'beacon_gateway_name': 'Schreibtisch', 
        'time_stamp': '2020-10-29 10:44:22.489801', 'server_time_stamp': '2020-10-29 09:44:22', 'timeout': 96945}]
        '''
        btmacs = [ sub['bt_mac'] for sub in result ] 
        print(btmacs)

        for btmac in btmacs:
            # publish config
            mqttc.publish_beacon_full_config_ha(btmac.lower(), "M90", "001122334455", "d_type", "0", "-99", "000413444444", "beacon_gateway")

            # get m9b data for btmac
            selected_items = [{k:d[k] for k in d if k!="a"} for d in result if d.get("bt_mac") == btmac]
            print('selected_items:' , selected_items)
            # create list of visible m9bs
            gateway_list = []
            for elem in selected_items: 
                gateway_list.append({"ipei": elem['beacon_gateway_IPEI'], 'proximity': elem['proximity'], 'rssi': elem['rssi']})
            #print('Full list::', gateway_list)

            # finally publish a full bt_mac data set 
            # select the BEST 
            set = get_best_m9b(selected_items)
            mqttc.publish_beacon_full_state_ha(set['bt_mac'], "Mxx", set['account'],
                                               set['proximity'], set['rssi'], 
                                               set['beacon_gateway_IPEI'],
                                               set['beacon_gateway_name'],
                                               gateway_list
                                               )
            # mqtt_room state
            mqttc.publish_beacon_room_state_ha(set['bt_mac'], set['account'], 
                                               set['proximity'], set['rssi'], 
                                               set['beacon_gateway_IPEI'], set['beacon_gateway_name'])


if __name__ == "__main__":

    # prepare logger
    logger = logging.getLogger('SnomMqttHassio')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # get access to the DB
    # DB reuse and type
    odbc=False
    initdb=False
    msgDb = DECTMessagingDb(odbc=odbc, initdb=initdb)


    # get a mqtt instance sending data in hass.io form
    mqttc = snomMqttHasssioClient()

    # fire data with scheduler
    logger.debug("main: schedule.every(1).minutes.do(amsg.request_keepalive)")
    schedule.every(2).seconds.do(send_locations)
    
    rc = mqttc.connect_and_subscribe('127.0.0.1', 1883)
    # publish the state only once.. we assume device attributes are constant
    mqttc.publish_beacon_full_config_ha("000413b50038", "M90", "001122334455", "d_type", "0", "-60", "000413444444", "beacon_gateway")

    rc = 0
    while rc == 0:
        # check and execute scheduled task
        schedule.run_pending()

        # motivate mqtt scheduler
        rc = mqttc.run()
        time.sleep(2)


    print("rc: "+str(rc))